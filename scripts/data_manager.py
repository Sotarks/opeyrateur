import os
import pandas as pd
from datetime import datetime
import time
import shutil
import math
from . import config

# Noms des mois pour les onglets Excel
MONTHS_FR = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
]

def _get_excel_path(year):
    """Retourne le chemin du fichier Excel pour une année donnée."""
    year_dir = os.path.join(config.FACTURES_DIR, str(year))
    return os.path.join(year_dir, f"factures_{year}.xlsx")

def get_yearly_invoice_count(year):
    """Compte le nombre total de factures pour une année à partir de son fichier Excel."""
    excel_path = _get_excel_path(year)
    if not os.path.exists(excel_path):
        return 0
    try:
        all_sheets = pd.read_excel(excel_path, sheet_name=None)
        return sum(len(df) for df in all_sheets.values())
    except Exception:
        return 0

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
        if pd.isna(raw_seq): raw_seq = 0
        sequence_str = f"{int(raw_seq):04d}"
    except (ValueError, TypeError):
        sequence_str = str(raw_seq)

    filename = f"FACTURE_{safe_nom}_{filename_date_str}-{sequence_str}.pdf"
    return os.path.join(output_dir, filename)

def load_all_data():
    """Charge toutes les données de tous les fichiers 'factures_YYYY.xlsx' dans un seul DataFrame."""
    all_dfs = []
    if not os.path.exists(config.FACTURES_DIR):
        return pd.DataFrame()
        
    try:
        year_dirs = [d for d in os.listdir(config.FACTURES_DIR) if os.path.isdir(os.path.join(config.FACTURES_DIR, d)) and d.isdigit()]
    except FileNotFoundError:
        return pd.DataFrame()

    for year in sorted(year_dirs, reverse=True): # Traite les années récentes en premier
        excel_path = _get_excel_path(year)
        if not os.path.exists(excel_path):
            continue
        try:
            yearly_sheets = pd.read_excel(excel_path, sheet_name=None)
            for month_df in yearly_sheets.values():
                if not month_df.empty:
                    all_dfs.append(month_df)
        except Exception as e:
            print(f"Impossible de lire le fichier pour l'année {year}: {e}")
    
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
    excel_path = _get_excel_path(year)
    if not os.path.exists(excel_path):
        return pd.DataFrame()
    
    try:
        all_sheets = pd.read_excel(excel_path, sheet_name=None)
        # Concatène toutes les feuilles (mois) qui contiennent des données
        df_list = [df for df in all_sheets.values() if not df.empty]
        if df_list:
            return pd.concat(df_list, ignore_index=True)
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def delete_invoice(data):
    """Supprime une facture du fichier Excel."""
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
    try:
        if 'ExpenseID' not in data or not data['ExpenseID']:
            data['ExpenseID'] = f"EXP-{int(time.time() * 1000)}"

        date_obj = datetime.strptime(data['Date'], '%d/%m/%Y')
        year = date_obj.year
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
        
        # Colonnes attendues
        columns = ["ExpenseID", "Date", "Categorie", "Description", "Montant", "ProofPath"]
        
        os.makedirs(os.path.dirname(excel_path), exist_ok=True)
        if os.path.exists(excel_path):
            df = pd.read_excel(excel_path)
        else:
            df = pd.DataFrame(columns=columns)
            
        new_row = pd.DataFrame([data])
        
        # S'assure que toutes les colonnes existent avant de concaténer
        for col in columns:
            if col not in df.columns:
                df[col] = None
        
        df = pd.concat([df, new_row], ignore_index=True)
        
        df.to_excel(excel_path, index=False)
        return True
    except Exception as e:
        print(f"Erreur sauvegarde frais: {e}")
        return False

def load_expenses(year):
    """Charge les frais pour une année donnée."""
    excel_path = _get_expenses_excel_path(year)
    columns = ["ExpenseID", "Date", "Categorie", "Description", "Montant", "ProofPath"]
    if not os.path.exists(excel_path):
        return pd.DataFrame(columns=columns)
    
    df = pd.read_excel(excel_path)
    # S'assure que la colonne ProofPath existe (pour les anciens fichiers)
    if "ProofPath" not in df.columns:
        df["ProofPath"] = None
    # S'assure que la colonne ExpenseID existe (pour les anciens fichiers)
    if "ExpenseID" not in df.columns:
        df["ExpenseID"] = None
    return df

def delete_expense(data):
    """Supprime une dépense du fichier Excel."""
    try:
        date_obj = datetime.strptime(data['Date'], '%d/%m/%Y')
        year = date_obj.year
        excel_path = _get_expenses_excel_path(year)
        
        if not os.path.exists(excel_path):
            return False
            
        df = pd.read_excel(excel_path, dtype={'ExpenseID': str})
        
        # Recherche de la ligne à supprimer
        idx_to_drop = None

        # Nouvelle méthode : suppression par ID unique (plus fiable)
        if 'ExpenseID' in data and data['ExpenseID'] and 'ExpenseID' in df.columns:
            matches = df.index[df['ExpenseID'] == data['ExpenseID']].tolist()
            if matches:
                idx_to_drop = matches[0]
        
        # Ancienne méthode (fallback pour les données sans ID)
        if idx_to_drop is None:
            for idx, row in df.iterrows():
                row_date = str(row['Date'])
                row_cat = str(row['Categorie'])
                row_desc = str(row['Description'])
                row_amount = float(row.get('Montant', 0.0))
                
                if (row_date == data['Date'] and row_cat == data['Categorie'] and row_desc == data['Description'] and abs(row_amount - data['Montant']) < 0.01):
                    idx_to_drop = idx
                    break
        
        if idx_to_drop is not None:
            # Suppression du fichier de preuve associé s'il existe
            proof_path = df.loc[idx_to_drop, 'ProofPath'] if 'ProofPath' in df.columns else None
            if proof_path and pd.notna(proof_path) and os.path.exists(str(proof_path)):
                try:
                    os.remove(str(proof_path))
                except Exception as e:
                    print(f"Erreur suppression fichier preuve: {e}")

            df = df.drop(idx_to_drop).reset_index(drop=True)
            df.to_excel(excel_path, index=False)
            return True
        return False
    except Exception as e:
        print(f"Erreur suppression frais: {e}")
        return False