import os
from datetime import datetime
import time
import shutil
import math
from concurrent.futures import ThreadPoolExecutor
from . import config

# Noms des mois pour les onglets Excel
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

# --- Cache pour les fichiers Excel ---
_file_cache = {}

def _load_excel_file_cached(path):
    """Charge un fichier Excel en utilisant un cache basé sur la date de modification."""
    global _file_cache
    if not os.path.exists(path):
        return None
        
    current_mtime = os.path.getmtime(path)
    if path in _file_cache:
        if _file_cache[path]['mtime'] == current_mtime:
            return _file_cache[path]['data']
            
    try:
        import pandas as pd
        data = pd.read_excel(path, sheet_name=None)
        _file_cache[path] = {'mtime': current_mtime, 'data': data}
        return data
    except Exception as e:
        print(f"Erreur lecture fichier {path}: {e}")
        return None

def _get_excel_path(year):
    """Retourne le chemin du fichier Excel pour une année donnée."""
    year_dir = os.path.join(config.FACTURES_DIR, str(year))
    return os.path.join(year_dir, f"factures_{year}.xlsx")

def get_yearly_invoice_count(year):
    """Compte le nombre total de factures pour une année à partir de son fichier Excel."""
    excel_path = _get_excel_path(year)
    all_sheets = _load_excel_file_cached(excel_path)
    
    if all_sheets is None:
        return 0
    try:
        return sum(len(df) for df in all_sheets.values())
    except Exception:
        return 0

def get_next_sequence_id(year):
    """Calcule le prochain numéro de séquence disponible pour l'année donnée (comble les trous)."""
    import pandas as pd
    excel_path = _get_excel_path(year)
    
    if not os.path.exists(excel_path):
        return 1
    
    existing_seqs = set()
    try:
        all_sheets = pd.read_excel(excel_path, sheet_name=None)
        for df in all_sheets.values():
            if 'SequenceID' in df.columns:
                # On convertit en numérique et on ignore les erreurs/vides
                seqs = pd.to_numeric(df['SequenceID'], errors='coerce').dropna().astype(int)
                existing_seqs.update(seqs.tolist())
        
        # On cherche le premier entier positif (partir de 1) qui n'est pas dans l'ensemble
        seq = 1
        while seq in existing_seqs:
            seq += 1
        return seq

    except Exception as e:
        print(f"Erreur calcul sequence: {e}")
        # Fallback : max + 1 si on n'arrive pas à lire correctement
        return get_yearly_invoice_count(year) + 1

def check_duplicate_invoice(data):
    """Vérifie si une facture identique (Date, Nom, Prénom, Montant) existe déjà."""
    import pandas as pd
    try:
        invoice_date = datetime.strptime(data['Date'], '%d/%m/%Y')
        year = invoice_date.year
        excel_path = _get_excel_path(year)
        
        all_sheets = _load_excel_file_cached(excel_path)
        if all_sheets is None:
            return False
        
        target_nom = str(data.get('Nom', '')).strip().upper()
        target_prenom = str(data.get('Prenom', '')).strip().lower()
        target_montant = float(data.get('Montant', 0.0))
        target_date = data.get('Date')

        for df in all_sheets.values():
            if df.empty: continue
            
            # Vérification des colonnes nécessaires
            if not {'Date', 'Nom', 'Prenom', 'Montant'}.issubset(df.columns):
                continue
            
            # Recherche de correspondance
            # On compare les chaînes en minuscule/majuscule pour être sûr
            # On utilise une tolérance pour le montant (float)
            match = df[
                (df['Date'] == target_date) &
                (df['Nom'].astype(str).str.strip().str.upper() == target_nom) &
                (df['Prenom'].astype(str).str.strip().str.lower() == target_prenom) &
                (abs(pd.to_numeric(df['Montant'], errors='coerce') - target_montant) < 0.01)
            ]
            
            if not match.empty:
                return True
                
    except Exception as e:
        print(f"Erreur check doublon: {e}")
        return False
    return False

def backup_database(year):
    """Crée une copie de sauvegarde du fichier Excel de l'année donnée."""
    source = _get_excel_path(year)
    if not os.path.exists(source):
        return

    backup_dir = os.path.join(config.BASE_DIR, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(source)
    backup_name = f"{os.path.splitext(filename)[0]}_{timestamp}.xlsx"
    destination = os.path.join(backup_dir, backup_name)

    try:
        shutil.copy2(source, destination)
        # Optionnel : Nettoyage des vieilles sauvegardes si besoin
    except Exception as e:
        print(f"Erreur de sauvegarde : {e}")

def save_to_excel(data):
    """Enregistre les données d'une facture dans le bon onglet du bon fichier Excel annuel."""
    import pandas as pd
    invoice_date = datetime.strptime(data['Date'], '%d/%m/%Y')
    year = invoice_date.year
    month_name = MONTHS_FR[invoice_date.month - 1]
    excel_path = _get_excel_path(year)

    if os.path.exists(excel_path):
        backup_database(year)

    os.makedirs(os.path.dirname(excel_path), exist_ok=True)

    new_data_df = pd.DataFrame([data])

    try:
        all_sheets = pd.read_excel(excel_path, sheet_name=None, dtype={'SequenceID': str})
    except (FileNotFoundError, ValueError):
        all_sheets = {m: pd.DataFrame() for m in MONTHS_FR}

    sheet_df = all_sheets.get(month_name, pd.DataFrame())
    if sheet_df.empty:
        updated_sheet_df = new_data_df
    else:
        updated_sheet_df = pd.concat([sheet_df, new_data_df], ignore_index=True)
    all_sheets[month_name] = updated_sheet_df

    # Crée une liste maîtresse de toutes les colonnes pour éviter la perte de données
    master_columns = set()
    for df in all_sheets.values():
        master_columns.update(df.columns)

    preferred_order = [
        "ID", "Date", "SequenceID", "Nom", "Prenom", "Adresse", "Attention_de", "Nom_Enfant",
        "Naissance_Enfant", "Attention_de2", "Prenom2", "Nom2", "Membres_Famille", "Prestation", "Date_Seance", "Montant",
        "Methode_Paiement", "Date_Paiement", "Note"
    ]
    
    final_columns = [col for col in preferred_order if col in master_columns]
    remaining_columns = sorted([col for col in master_columns if col not in final_columns])
    final_columns.extend(remaining_columns)

    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        for sheet_name, df_to_write in all_sheets.items():
            if not df_to_write.empty:
                df_to_write = df_to_write.reindex(columns=final_columns)
            df_to_write.to_excel(writer, sheet_name=sheet_name, index=False)

def get_invoice_path(data, get_folder=False):
    """Construit le chemin du PDF de la facture avec le nouveau nommage."""
    try:
        invoice_date = datetime.strptime(data['Date'], '%d/%m/%Y')
        folder_date_str = invoice_date.strftime('%Y-%m-%d')
        year_str = str(invoice_date.year)
    except (ValueError, TypeError):
        now = datetime.now()
        invoice_date = now # Fallback for date used in filename
        folder_date_str = now.strftime('%Y-%m-%d')
        year_str = str(now.year)

    output_dir = os.path.join(config.FACTURES_DIR, year_str, folder_date_str)

    if get_folder:
        return output_dir

    # Nouveau nommage : FACTURE_NOMDE FAMILLE_YYYYMMDD-XXXX
    safe_nom = "".join(c for c in data.get('Nom', '').upper() if c.isalnum())
    filename_date_str = invoice_date.strftime('%Y%m%d')
    
    # Correction : On force le format 4 chiffres (ex: 1 devient "0001")
    raw_seq = data.get('SequenceID', 0)
    try:
        import pandas as pd
        if pd.isna(raw_seq): raw_seq = 0
        sequence_str = f"{int(raw_seq):04d}"
    except (ValueError, TypeError):
        sequence_str = str(raw_seq)

    filename = f"FACTURE_{safe_nom}_{filename_date_str}-{sequence_str}.pdf"
    return os.path.join(output_dir, filename)

def load_all_data():
    """Charge toutes les données de tous les fichiers 'factures_YYYY.xlsx' dans un seul DataFrame."""
    import pandas as pd
    all_dfs = []
    if not os.path.exists(config.FACTURES_DIR):
        return pd.DataFrame()
        
    try:
        year_dirs = [d for d in os.listdir(config.FACTURES_DIR) if os.path.isdir(os.path.join(config.FACTURES_DIR, d)) and d.isdigit()]
    except FileNotFoundError:
        return pd.DataFrame()

    year_dirs = sorted(year_dirs, reverse=True)
    all_dfs = []

    # Utilisation de load_year_data qui utilise maintenant le cache
    def safe_load_year(year):
        return load_year_data(year)

    with ThreadPoolExecutor() as executor:
        results = executor.map(safe_load_year, year_dirs)
        for df in results:
            if not df.empty:
                all_dfs.append(df)

    if not all_dfs:
        return pd.DataFrame()
        
    return pd.concat(all_dfs, ignore_index=True)

def get_available_years():
    """Retourne la liste des années disponibles dans le dossier factures."""
    if not os.path.exists(config.FACTURES_DIR):
        return []
    try:
        years = [d for d in os.listdir(config.FACTURES_DIR) if os.path.isdir(os.path.join(config.FACTURES_DIR, d)) and d.isdigit()]
        return sorted(years, reverse=True)
    except Exception:
        return []

def load_year_data(year):
    """Charge les données pour une année spécifique."""
    import pandas as pd
    excel_path = _get_excel_path(year)
    
    all_sheets = _load_excel_file_cached(excel_path)
    if all_sheets is None:
        return pd.DataFrame()
    
    try:
        # Concatène toutes les feuilles (mois) qui contiennent des données
        df_list = [df for df in all_sheets.values() if not df.empty]
        if df_list:
            return pd.concat(df_list, ignore_index=True)
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def delete_invoice(data):
    """Supprime une facture du fichier Excel."""
    import pandas as pd
    try:
        invoice_date = datetime.strptime(data['Date'], '%d/%m/%Y')
        year = invoice_date.year
        month_name = MONTHS_FR[invoice_date.month - 1]
        excel_path = _get_excel_path(year)

        if not os.path.exists(excel_path):
            return False

        # Sauvegarde avant suppression
        backup_database(year)

        all_sheets = pd.read_excel(excel_path, sheet_name=None)
        sheet_df = all_sheets.get(month_name)

        if sheet_df is None or 'ID' not in sheet_df.columns:
            return False

        # Suppression de la ligne correspondant à l'ID
        sheet_df = sheet_df[sheet_df['ID'] != data['ID']]
        all_sheets[month_name] = sheet_df

        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            for sheet_name, df_to_write in all_sheets.items():
                df_to_write.to_excel(writer, sheet_name=sheet_name, index=False)
        return True
    except Exception as e:
        print(f"Erreur suppression: {e}")
        return False

def _get_expenses_excel_path(year):
    """Retourne le chemin du fichier Excel des frais pour une année donnée."""
    year_dir = os.path.join(config.FRAIS_DIR, str(year))
    return os.path.join(year_dir, f"frais_{year}.xlsx")

def save_expense(data):
    """Enregistre une dépense dans le fichier Excel des frais."""
    import pandas as pd
    try:
        if 'ExpenseID' not in data or not data['ExpenseID']:
            data['ExpenseID'] = f"EXP-{int(time.time() * 1000)}"

        date_obj = datetime.strptime(data['Date'], '%d/%m/%Y')
        year = date_obj.year
        month_name = MONTHS_FR[date_obj.month - 1]
        excel_path = _get_expenses_excel_path(year)
        
        # Gestion du justificatif
        proof_path = data.get('ProofPath')
        final_proof_path = None

        if proof_path and os.path.exists(proof_path):
            # Formatage de la date pour le dossier et le fichier (YYYY-MM-DD)
            date_formatted = date_obj.strftime("%Y-%m-%d")
            
            # Création du dossier justificatifs/DATE
            proofs_dir = os.path.join(config.FRAIS_DIR, str(year), "justificatifs", date_formatted)
            os.makedirs(proofs_dir, exist_ok=True)
            
            # Nettoyage des chaînes pour le nom de fichier
            safe_cat = "".join(c for c in str(data.get('Categorie', '')) if c.isalnum() or c in (' ', '_', '-')).strip()
            safe_desc = "".join(c for c in str(data.get('Description', '')) if c.isalnum() or c in (' ', '_', '-')).strip()
            
            # Extension du fichier original
            _, ext = os.path.splitext(proof_path)
            
            # Nom du fichier : CATEGORY_DATE_DESCRIPTION.ext
            new_filename = f"{safe_cat}_{date_formatted}_{safe_desc}{ext}"
            destination = os.path.join(proofs_dir, new_filename)
            
            try:
                shutil.copy2(proof_path, destination)
                final_proof_path = destination
            except Exception as e:
                print(f"Erreur copie justificatif: {e}")

        # Mise à jour des données avec le chemin final
        data['ProofPath'] = final_proof_path
        
        # Ajout du CompteNum si absent
        if 'CompteNum' not in data:
            data['CompteNum'] = ACCOUNT_MAP.get(data.get('Categorie'), "628000")
        
        # Colonnes attendues
        columns = ["ExpenseID", "Date", "Categorie", "Description", "Montant", "ProofPath", "CompteNum"]
        
        os.makedirs(os.path.dirname(excel_path), exist_ok=True)
        
        all_sheets = {}
        if os.path.exists(excel_path):
            try:
                all_sheets = pd.read_excel(excel_path, sheet_name=None)
            except Exception:
                all_sheets = {}
        
        if month_name in all_sheets:
            df = all_sheets[month_name]
        else:
            df = pd.DataFrame(columns=columns)
            
        new_row = pd.DataFrame([data])
        
        # S'assure que toutes les colonnes existent avant de concaténer
        for col in columns:
            if col not in df.columns:
                df[col] = None
        
        if df.empty:
            df = new_row
        else:
            df = pd.concat([df, new_row], ignore_index=True)
        all_sheets[month_name] = df
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            for sheet_name, sheet_df in all_sheets.items():
                sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
                
        return True
    except Exception as e:
        print(f"Erreur sauvegarde frais: {e}")
        return False

def load_expenses(year):
    """Charge les frais pour une année donnée."""
    import pandas as pd
    excel_path = _get_expenses_excel_path(year)
    columns = ["ExpenseID", "Date", "Categorie", "Description", "Montant", "ProofPath", "CompteNum"]
    
    all_sheets = _load_excel_file_cached(excel_path)
    if all_sheets is None:
        return pd.DataFrame(columns=columns)
    
    try:
        df_list = []
        for df in all_sheets.values():
            if not df.empty:
                df_list.append(df)
        
        if df_list:
            df = pd.concat(df_list, ignore_index=True)
        else:
            df = pd.DataFrame(columns=columns)
    except Exception:
        return pd.DataFrame(columns=columns)

    # S'assure que la colonne ProofPath existe (pour les anciens fichiers)
    if "ProofPath" not in df.columns:
        df["ProofPath"] = None
    # S'assure que la colonne ExpenseID existe (pour les anciens fichiers)
    if "ExpenseID" not in df.columns:
        df["ExpenseID"] = None
    # S'assure que la colonne CompteNum existe
    if "CompteNum" not in df.columns:
        df["CompteNum"] = df["Categorie"].map(ACCOUNT_MAP).fillna("628000")
    return df

def delete_expense(data):
    """Supprime une dépense du fichier Excel."""
    import pandas as pd
    try:
        date_obj = datetime.strptime(data['Date'], '%d/%m/%Y')
        year = date_obj.year
        excel_path = _get_expenses_excel_path(year)
        
        if not os.path.exists(excel_path):
            return False
            
        all_sheets = pd.read_excel(excel_path, sheet_name=None, dtype={'ExpenseID': str})
        deleted = False

        def remove_from_df(df):
            idx_to_drop = None
            if 'ExpenseID' in data and data['ExpenseID'] and 'ExpenseID' in df.columns:
                matches = df.index[df['ExpenseID'] == data['ExpenseID']].tolist()
                if matches:
                    idx_to_drop = matches[0]
            
            if idx_to_drop is None:
                for idx, row in df.iterrows():
                    try:
                        row_amount = float(row.get('Montant', 0.0))
                        data_amount = float(data.get('Montant', 0.0))
                    except:
                        row_amount, data_amount = 0.0, 0.0
                    
                    if (str(row['Date']) == data['Date'] and 
                        str(row['Categorie']) == data['Categorie'] and 
                        str(row['Description']) == data['Description'] and 
                        abs(row_amount - data_amount) < 0.01):
                        idx_to_drop = idx
                        break
            
            if idx_to_drop is not None:
                proof_path = df.loc[idx_to_drop, 'ProofPath'] if 'ProofPath' in df.columns else None
                if proof_path and pd.notna(proof_path) and os.path.exists(str(proof_path)):
                    try: os.remove(str(proof_path))
                    except Exception: pass
                return df.drop(idx_to_drop).reset_index(drop=True), True
            return df, False

        # 1. Chercher dans l'onglet du mois
        month_name = MONTHS_FR[date_obj.month - 1]
        if month_name in all_sheets:
            all_sheets[month_name], deleted = remove_from_df(all_sheets[month_name])

        # 2. Si pas trouvé, chercher partout (migration)
        if not deleted:
            for name in all_sheets:
                if name == month_name: continue
                all_sheets[name], deleted = remove_from_df(all_sheets[name])
                if deleted: break

        if deleted:
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                for name, sheet_df in all_sheets.items():
                    sheet_df.to_excel(writer, sheet_name=name, index=False)
            return True
            
        return False
    except Exception as e:
        print(f"Erreur suppression frais: {e}")
        return False

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
    import pandas as pd
    try:
        # Tentative de lecture avec détection automatique du séparateur
        try:
            df = pd.read_csv(file_path, sep=None, engine='python', encoding='utf-8')
        except:
            df = pd.read_csv(file_path, sep=None, engine='python', encoding='latin-1')

        # Normalisation des noms de colonnes (minuscules, sans accents)
        df.columns = df.columns.str.lower().str.replace('é', 'e').str.replace('è', 'e').str.strip()

        # Identification des colonnes clés
        col_date = next((c for c in df.columns if 'date' in c), None)
        col_desc = next((c for c in df.columns if any(x in c for x in ['libelle', 'description', 'label', 'operation'])), None)
        col_amount = next((c for c in df.columns if any(x in c for x in ['montant', 'amount', 'debit', 'credit', 'solde'])), None)

        if not (col_date and col_desc and col_amount):
            return 0, "Colonnes Date, Libellé ou Montant introuvables."

        count = 0
        for _, row in df.iterrows():
            try:
                # Gestion du montant (virgule vs point, signe)
                montant_raw = row[col_amount]
                if isinstance(montant_raw, str):
                    montant_raw = montant_raw.replace(',', '.').replace(' ', '').replace('€', '')
                montant = float(montant_raw)

                # On ne garde que les dépenses (montants négatifs)
                if montant >= 0:
                    continue
                
                # On passe en positif pour l'enregistrement
                montant = abs(montant)

                # Formatage de la date
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
                    "CompteNum": compte_num
                }
                
                if save_expense(data):
                    count += 1
            except Exception:
                continue
                
        return count, ""
    except Exception as e:
        return 0, str(e)