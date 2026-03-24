import os
import json
from datetime import datetime
import time
import shutil
import math
import pandas as pd
from opeyrateur_app.core import config
from opeyrateur_app.core import db_manager

# Noms des mois pour les onglets (gardé pour compatibilité éventuelle)
MONTHS_FR = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
]

ACCOUNT_MAP = {
    "Loyer": "613200",
    "Électricité / Gaz": "606100",
    "Ménage": "615000",
    "Assurance Local": "616000",
    "Doctolib / Logiciels": "628000",
    "Téléphone / Internet": "626000",
    "Site Web": "623000",
    "Mouchoirs / Café": "606300",
    "Papeterie / Tests": "606400",
    "Repas (seule)": "625700",
    "Supervision": "622800",
    "Formation": "618100",
    "Banque": "627800",
    "Assurance RCP": "616000",
    "Déplacement": "625100",
    "Cotisations": "646000",
    "Tenue Pro": "606300",
    "Prélèvement Personnel": "108000",
    "Autre": "628000",
    "Matériel": "606300", "Fournitures": "606400"
}

def get_next_sequence_id(year):
    """Calcule le prochain numéro de séquence disponible pour l'année donnée."""
    return db_manager.get_next_sequence_id(year)

def check_duplicate_invoice(data):
    """Vérifie si une facture identique (Date, Nom, Prénom, Montant) existe déjà."""
    return db_manager.check_duplicate_invoice(
        data.get('Date', ''),
        data.get('Nom', ''),
        data.get('Prenom', ''),
        data.get('Montant', 0.0)
    )

def backup_database():
    """Crée une copie de sauvegarde de la base de données au démarrage et conserve les 30 derniers."""
    source = os.path.join(config.BASE_DIR, "data.db")
    if not os.path.exists(source):
        return

    backup_dir = os.path.join(config.BASE_DIR, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    # Nettoyage des anciens backups (plus de 30 jours)
    now_ts = time.time()
    for f in os.listdir(backup_dir):
        fp = os.path.join(backup_dir, f)
        if os.path.isfile(fp) and f.startswith("data_backup_"):
            if os.stat(fp).st_mtime < now_ts - 30 * 86400:
                try: os.remove(fp)
                except: pass

    # On ne fait qu'un backup par jour (le premier lancement)
    timestamp = datetime.now().strftime("%Y%m%d")
    backup_name = f"data_backup_{timestamp}.db"
    destination = os.path.join(backup_dir, backup_name)
    
    if os.path.exists(destination):
        return # Déjà sauvegardé aujourd'hui

    try:
        shutil.copy2(source, destination)
    except Exception as e:
        print(f"Erreur de sauvegarde DB : {e}")

def save_to_excel(data):
    """Enregistre les données d'une facture. Le nom 'save_to_excel' est conservé pour la rétrocompatibilité,
       mais sauvegarde dans SQLite."""
    db_manager.insert_invoice(data)

def mark_invoices_as_sent(invoice_list):
    """Met à jour la date d'envoi d'email pour une liste de factures."""
    ids = [inv.get('ID') for inv in invoice_list if inv.get('ID')]
    db_manager.mark_invoices_as_sent(ids)

def get_invoice_path(data, get_folder=False):
    """Construit le chemin du PDF de la facture avec la structure Année/Mois/Jour."""
    try:
        invoice_date = datetime.strptime(data['Date'], '%d/%m/%Y')
        year_str = str(invoice_date.year)
        month_str = f"{invoice_date.month:02d}_{MONTHS_FR[invoice_date.month - 1]}"
        folder_date_str = invoice_date.strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        now = datetime.now()
        invoice_date = now # Fallback for date used in filename
        year_str = str(now.year)
        month_str = f"{now.month:02d}_{MONTHS_FR[now.month - 1]}"
        folder_date_str = now.strftime('%Y-%m-%d')

    output_dir = os.path.join(config.FACTURES_DIR, year_str, month_str, folder_date_str)

    if get_folder:
        return output_dir

    # Nouveau nommage : FACTURE_NOMDE FAMILLE_YYYYMMDD-XXXX
    safe_nom = "".join(c for c in data.get('Nom', '').upper() if c.isalnum())
    filename_date_str = invoice_date.strftime('%Y%m%d')
    
    raw_seq = data.get('SequenceID', 0)
    try:
        if pd.isna(raw_seq): raw_seq = 0
        sequence_str = f"{int(raw_seq):04d}"
    except (ValueError, TypeError):
        sequence_str = str(raw_seq)

    filename = f"FACTURE_{safe_nom}_{filename_date_str}-{sequence_str}.pdf"
    return os.path.join(output_dir, filename)

def get_available_years():
    """Retourne la liste des années disponibles dans la base de données."""
    return [str(y) for y in db_manager.get_available_invoice_years()]

def load_year_data(year):
    """Charge les données (factures) pour une année spécifique en format DataFrame."""
    invoices = db_manager.get_all_invoices(year=str(year))
    if not invoices:
        return pd.DataFrame()
    df = pd.DataFrame(invoices)
    df.replace(['nan', 'NaN', '<na>', 'nat', ''], None, inplace=True)
    return df

def load_all_data():
    """Charge toutes les données de factures dans un seul DataFrame."""
    invoices = db_manager.get_all_invoices()
    if not invoices:
        return pd.DataFrame()
    df = pd.DataFrame(invoices)
    df.replace(['nan', 'NaN', '<na>', 'nat', ''], None, inplace=True)
    return df

def delete_invoice(data):
    """Supprime une facture de la base de données."""
    return db_manager.delete_invoice_by_id(data.get('ID'))

def save_expense(data):
    """Enregistre une dépense dans la base de données."""
    if 'ExpenseID' not in data or not data['ExpenseID']:
        data['ExpenseID'] = f"EXP-{int(time.time() * 1000)}"

    # Gestion du justificatif
    proof_path = data.get('ProofPath')
    final_proof_path = None

    if proof_path and os.path.exists(proof_path):
        try:
            date_obj = datetime.strptime(data['Date'], '%d/%m/%Y')
        except ValueError:
            date_obj = datetime.now()
            
        year = date_obj.year
        date_formatted = date_obj.strftime("%Y-%m-%d")
        
        proofs_dir = os.path.join(config.FRAIS_DIR, str(year), "justificatifs", date_formatted)
        os.makedirs(proofs_dir, exist_ok=True)
        
        safe_cat = "".join(c for c in str(data.get('Categorie', '')) if c.isalnum() or c in (' ', '_', '-')).strip()
        safe_desc = "".join(c for c in str(data.get('Description', '')) if c.isalnum() or c in (' ', '_', '-')).strip()
        
        _, ext = os.path.splitext(proof_path)
        new_filename = f"{safe_cat}_{date_formatted}_{safe_desc}{ext}"
        final_proof_path = os.path.join(proofs_dir, new_filename)
        
        try:
            shutil.copy2(proof_path, final_proof_path)
        except Exception as e:
            print(f"Erreur copie justificatif: {e}")
            final_proof_path = None

    data['ProofPath'] = final_proof_path
    if 'CompteNum' not in data:
        data['CompteNum'] = ACCOUNT_MAP.get(data.get('Categorie'), "628000")
    
    try:
        db_manager.insert_expense(data)
        return True
    except Exception as e:
        print(f"Erreur sauvegarde frais DB: {e}")
        return False

def load_expenses(year):
    """Charge les frais pour une année donnée."""
    expenses = db_manager.get_all_expenses(year=str(year))
    columns = ["ExpenseID", "Date", "Categorie", "Description", "Montant", "ProofPath", "CompteNum", "Compte_Paiement", "Est_Rembourse"]
    if not expenses:
        return pd.DataFrame(columns=columns)
    
    df = pd.DataFrame(expenses)
    # Remplir les colonnes manquantes si besoin
    for col in columns:
        if col not in df.columns:
            df[col] = None
    return df

def delete_expense(data):
    """Supprime une dépense."""
    if 'ExpenseID' not in data:
        # Fallback to try and find the ID using date/categorie/montant ?
        # Much harder without ID. For safety, we should ensure UI passes ExpenseID.
        return False
        
    proof_path = data.get('ProofPath')
    if proof_path and os.path.exists(str(proof_path)):
        try: 
            os.remove(str(proof_path))
        except Exception: 
            pass
            
    return db_manager.delete_expense_by_id(data['ExpenseID'])

def mark_as_reimbursed(expense_ids):
    """Marque les dépenses ciblées comme remboursées."""
    db_manager.mark_expenses_as_reimbursed(expense_ids)

def unmark_as_reimbursed(expense_ids):
    """Annule le remboursement des dépenses ciblées."""
    db_manager.unmark_expenses_as_reimbursed(expense_ids)

def _guess_category(description):
    """Devine la catégorie d'une dépense en fonction de sa description."""
    desc = description.upper()
    keywords = {
        "Loyer": ["LOYER", "SCI", "IMMOBILIER", "FONCIA"],
        "Électricité / Gaz": ["EDF", "ENGIE", "TOTAL ENERGIES", "EAU", "VEOLIA"],
        "Ménage": ["MENAGE", "NETTOYAGE", "SHIVA", "O2"],
        "Assurance Local": ["ASSURANCE LOCAL", "MULTIRISQUE"],
        "Doctolib / Logiciels": ["DOCTOLIB", "GOOGLE", "MICROSOFT", "ADOBE", "ZOOM", "LOGICIEL"],
        "Téléphone / Internet": ["ORANGE", "SFR", "BOUYGUES", "FREE", "TELEPHONE", "INTERNET", "SOSH", "RED"],
        "Site Web": ["WORDPRESS", "OVH", "IONOS", "HOSTINGER", "GANDI", "SITE"],
        "Mouchoirs / Café": ["ACTION", "HEMA", "CAFE", "NESPRESSO", "MOUCHOIR", "ENTRETIEN", "IKEA"],
        "Papeterie / Tests": ["BUREAU", "OFFICE", "DEPOT", "CARTOUCHE", "PAPIER", "ECPA", "PEARSON", "TEST", "WISC", "WAIS"],
        "Repas (seule)": ["RESTAURANT", "BOULANGERIE", "MC DO", "BURGER", "SUSHI", "EAT", "DELIVEROO", "UBER EATS", "CARREFOUR", "LECLERC", "AUCHAN", "INTERMARCHE", "MONOPRIX"],
        "Supervision": ["SUPERVISION"],
        "Formation": ["FORMATION", "DPC", "FIFPL"],
        "Banque": ["BANQUE", "FRAIS", "COMMISSION", "AGIOS", "CB"],
        "Assurance RCP": ["MAAF", "AXA", "ALLIANZ", "MACIF", "MATMUT", "RCP", "ASSURANCE"],
        "Tenue Pro": ["BLOUSE", "VETEMENT", "CHAUSSURE", "TENUE", "UNIFORME", "TEXTILE"],
        "Prélèvement Personnel": ["SALAIRE", "PERSO", "PRELEVEMENT", "VIREMENT COMPTE", "REMUNERATION"],
        "Déplacement": ["SNCF", "UBER", "TAXI", "TOTAL", "ESSO", "BP", "SHELL", "PEAGE", "PARKING", "STATION", "AIR FRANCE", "EASYJET"],
        "Cotisations": ["URSSAF", "CIPAV", "RETRAITE", "RAM", "CPAM", "IMPOTS", "SIE", "CFE"],
        "Autre": []
    }

    for cat, words in keywords.items():
        if any(word in desc for word in words):
            return cat
    return "Autre"

def import_expenses_from_csv(file_path):
    """Importe des dépenses depuis un fichier CSV bancaire."""
    try:
        try:
            df = pd.read_csv(file_path, sep=None, engine='python', encoding='utf-8')
        except:
            df = pd.read_csv(file_path, sep=None, engine='python', encoding='latin-1')

        df.columns = df.columns.str.lower().str.replace('é', 'e').str.replace('è', 'e').str.strip()

        col_date = next((c for c in df.columns if 'date' in c), None)
        col_desc = next((c for c in df.columns if any(x in c for x in ['libelle', 'description', 'label', 'operation'])), None)
        col_amount = next((c for c in df.columns if any(x in c for x in ['montant', 'amount', 'debit', 'credit', 'solde'])), None)

        if not (col_date and col_desc and col_amount):
            return 0, "Colonnes Date, Libellé ou Montant introuvables."

        count = 0
        for _, row in df.iterrows():
            try:
                montant_raw = row[col_amount]
                if isinstance(montant_raw, str):
                    montant_raw = montant_raw.replace(',', '.').replace(' ', '').replace('€', '')
                montant = float(montant_raw)

                if montant >= 0:
                    continue
                
                montant = abs(montant)
                date_raw = pd.to_datetime(row[col_date], dayfirst=True, errors='coerce')
                if pd.isna(date_raw): continue
                date_str = date_raw.strftime("%d/%m/%Y")

                description = str(row[col_desc]).strip()
                categorie = _guess_category(description)
                compte_num = ACCOUNT_MAP.get(categorie, "628000")

                data = {
                    "Date": date_str,
                    "Categorie": categorie,
                    "Description": description,
                    "Montant": montant,
                    "ProofPath": None,
                    "CompteNum": compte_num,
                    "Compte_Paiement": "Compte Pro",
                    "Est_Rembourse": 0
                }
                
                if save_expense(data):
                    count += 1
            except Exception:
                continue
                
        return count, ""
    except Exception as e:
        return 0, str(e)

# --- Gestion de l'Agenda (Notes/RDV) ---
def _get_agenda_path(year):
    """Retourne le chemin du fichier JSON de l'agenda pour une année."""
    os.makedirs(config.AGENDA_DIR, exist_ok=True)
    return os.path.join(config.AGENDA_DIR, f"agenda_{year}.json")

def save_agenda_note(data):
    """Enregistre une note dans l'agenda."""
    try:
        date_obj = datetime.strptime(data['date'], '%d/%m/%Y')
        year = date_obj.year
        filepath = _get_agenda_path(year)
        
        notes = []
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                notes = json.load(f)
        
        if 'id' not in data:
            data['id'] = str(int(time.time() * 1000))
            
        existing_idx = next((i for i, n in enumerate(notes) if n['id'] == data['id']), None)
        if existing_idx is not None:
            notes[existing_idx] = data
        else:
            notes.append(data)
            
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(notes, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Erreur sauvegarde note: {e}")
        return False

def load_agenda_notes(year):
    """Charge les notes de l'agenda pour une année."""
    filepath = _get_agenda_path(year)
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def delete_agenda_note(note_id, year):
    """Supprime une note."""
    filepath = _get_agenda_path(year)
    if not os.path.exists(filepath):
        return False
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            notes = json.load(f)
        
        notes = [n for n in notes if n['id'] != note_id]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(notes, f, ensure_ascii=False, indent=4)
        return True
    except Exception:
        return False