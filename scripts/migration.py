import os
import pandas as pd
from datetime import datetime
from . import config
from . import db_manager

def migrate_excel_to_sqlite():
    """Migre les données des fichiers Excel (factures et frais) vers la base SQLite."""
    print("Début de la migration des données vers SQLite...")
    
    # 1. Migration des factures
    if os.path.exists(config.FACTURES_DIR):
        year_dirs = [d for d in os.listdir(config.FACTURES_DIR) if os.path.isdir(os.path.join(config.FACTURES_DIR, d)) and d.isdigit()]
        for year in year_dirs:
            excel_path = os.path.join(config.FACTURES_DIR, year, f"factures_{year}.xlsx")
            if not os.path.exists(excel_path):
                continue
                
            print(f"Migration des factures de {year}...")
            try:
                all_sheets = pd.read_excel(excel_path, sheet_name=None, dtype={'SequenceID': str, 'ID': str})
                for sheet_name, df in all_sheets.items():
                    if df.empty:
                        continue
                        
                    # Remplacement des NaN par None
                    df = df.where(pd.notnull(df), None)
                    
                    for _, row in df.iterrows():
                        if pd.isna(row.get('ID')) or row.get('ID') is None:
                            continue
                            
                        # Formatage spécial pour la liste des membres de famille (si c'est une string représentant une liste, on la parse)
                        membres_famille = row.get('Membres_Famille')
                        import ast
                        if isinstance(membres_famille, str) and membres_famille.startswith('['):
                            try:
                                membres_famille = ast.literal_eval(membres_famille)
                            except (ValueError, SyntaxError):
                                pass
                                
                        data = {
                            "ID": str(row.get('ID', '')),
                            "Date": str(row.get('Date', '')),
                            "SequenceID": str(row.get('SequenceID', '')).zfill(4) if row.get('SequenceID') else "",
                            "Nom": str(row.get('Nom', '')).strip().upper() if row.get('Nom') else "",
                            "Prenom": str(row.get('Prenom', '')).strip() if row.get('Prenom') else "",
                            "Adresse": str(row.get('Adresse', '')) if row.get('Adresse') else "",
                            "Attention_de": str(row.get('Attention_de', '')) if row.get('Attention_de') else "",
                            "Nom_Enfant": str(row.get('Nom_Enfant', '')) if row.get('Nom_Enfant') else "",
                            "Naissance_Enfant": str(row.get('Naissance_Enfant', '')) if row.get('Naissance_Enfant') else "",
                            "Attention_de2": str(row.get('Attention_de2', '')) if row.get('Attention_de2') else "",
                            "Prenom2": str(row.get('Prenom2', '')) if row.get('Prenom2') else "",
                            "Nom2": str(row.get('Nom2', '')) if row.get('Nom2') else "",
                            "Membres_Famille": membres_famille,
                            "Prestation": str(row.get('Prestation', '')) if row.get('Prestation') else "",
                            "Date_Seance": str(row.get('Date_Seance', '')) if row.get('Date_Seance') else "",
                            "Montant": float(row.get('Montant', 0.0)) if row.get('Montant') else 0.0,
                            "Methode_Paiement": str(row.get('Methode_Paiement', '')) if row.get('Methode_Paiement') else "",
                            "Date_Paiement": str(row.get('Date_Paiement', '')) if row.get('Date_Paiement') else "",
                            "Date_Envoi_Email": str(row.get('Date_Envoi_Email', '')) if row.get('Date_Envoi_Email') else "",
                            "Note": str(row.get('Note', '')) if row.get('Note') else ""
                        }
                        
                        try:
                            db_manager.insert_invoice(data)
                        except Exception as e:
                            print(f"Erreur lors de l'insertion de la facture {data['ID']} : {e}")
            except Exception as e:
                print(f"Erreur globale lors de la migration des factures de {year} : {e}")
                
    # 2. Migration des frais
    if os.path.exists(config.FRAIS_DIR):
        year_dirs = [d for d in os.listdir(config.FRAIS_DIR) if os.path.isdir(os.path.join(config.FRAIS_DIR, d)) and d.isdigit()]
        for year in year_dirs:
            excel_path = os.path.join(config.FRAIS_DIR, year, f"frais_{year}.xlsx")
            if not os.path.exists(excel_path):
                continue
                
            print(f"Migration des frais de {year}...")
            try:
                all_sheets = pd.read_excel(excel_path, sheet_name=None, dtype={'ExpenseID': str})
                for sheet_name, df in all_sheets.items():
                    if df.empty:
                        continue
                        
                    df = df.where(pd.notnull(df), None)
                    
                    for _, row in df.iterrows():
                        if pd.isna(row.get('ExpenseID')) or row.get('ExpenseID') is None:
                            continue
                            
                        data = {
                            "ExpenseID": str(row.get('ExpenseID', '')),
                            "Date": str(row.get('Date', '')),
                            "Categorie": str(row.get('Categorie', '')) if row.get('Categorie') else "",
                            "Description": str(row.get('Description', '')) if row.get('Description') else "",
                            "Montant": float(row.get('Montant', 0.0)) if row.get('Montant') else 0.0,
                            "ProofPath": str(row.get('ProofPath', '')) if row.get('ProofPath') else "",
                            "CompteNum": str(row.get('CompteNum', '')) if row.get('CompteNum') else ""
                        }
                        
                        try:
                            # Avoid null float conversion error
                            if pd.isna(data["Montant"]) or data["Montant"] is None:
                                data["Montant"] = 0.0
                            db_manager.insert_expense(data)
                        except Exception as e:
                            print(f"Erreur lors de l'insertion de la dépense {data['ExpenseID']} : {e}")
            except Exception as e:
                print(f"Erreur globale lors de la migration des frais de {year} : {e}")

    # Marquer la migration comme terminée en créant un fichier flag caché
    migration_flag = os.path.join(config.BASE_DIR, ".migration_done")
    with open(migration_flag, "w") as f:
        f.write("Migration was completed on " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
    print("Migration terminée avec succès !")

def check_and_migrate():
    """Vérifie si la migration a déjà été effectuée, sinon la lance."""
    migration_flag = os.path.join(config.BASE_DIR, ".migration_done")
    if not os.path.exists(migration_flag) and (os.path.exists(config.FACTURES_DIR) or os.path.exists(config.FRAIS_DIR)):
        migrate_excel_to_sqlite()
