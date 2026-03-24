import sqlite3
import os
import json
from datetime import datetime
from opeyrateur_app.core import config

DB_PATH = os.path.join(config.BASE_DIR, "data.db")

def get_connection():
    """Crée et retourne une connexion à la base de données SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Permet d'accéder aux colonnes par leur nom
    return conn

def init_db():
    """Initialise la base de données et crée les tables si elles n'existent pas."""
    conn = get_connection()
    cursor = conn.cursor()

    # Table des factures
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            ID TEXT PRIMARY KEY,
            Date TEXT,
            SequenceID TEXT,
            Nom TEXT,
            Prenom TEXT,
            Adresse TEXT,
            Attention_de TEXT,
            Nom_Enfant TEXT,
            Naissance_Enfant TEXT,
            Attention_de2 TEXT,
            Prenom2 TEXT,
            Nom2 TEXT,
            Membres_Famille TEXT,
            Prestation TEXT,
            Date_Seance TEXT,
            Montant REAL,
            Methode_Paiement TEXT,
            Date_Paiement TEXT,
            Date_Envoi_Email TEXT,
            Note TEXT
        )
    ''')

    # Création d'index pour accélérer les recherches sur les factures
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoice_date ON invoices(Date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoice_nom ON invoices(Nom)')

    # Table des frais (dépenses)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            ExpenseID TEXT PRIMARY KEY,
            Date TEXT,
            Categorie TEXT,
            Description TEXT,
            Montant REAL,
            ProofPath TEXT,
            CompteNum TEXT,
            Compte_Paiement TEXT
        )
    ''')
    
    # Migration pour rajouter le Compte_Paiement sur une base existante
    try:
        cursor.execute("ALTER TABLE expenses ADD COLUMN Compte_Paiement TEXT DEFAULT 'Compte Pro'")
    except sqlite3.OperationalError:
        pass # La colonne existe déjà

    # Migration pour rajouter l'état de remboursement perso
    try:
        cursor.execute("ALTER TABLE expenses ADD COLUMN Est_Rembourse INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass # La colonne existe déjà
    
    # Création d'index pour accélérer les recherches sur les dépenses
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_expense_date ON expenses(Date)')

    conn.commit()
    conn.close()

# Initialisation automatique au chargement du module
init_db()

# --- Fonctions Factures (Invoices) ---

def sanitize_dict(d):
    """Nettoie les valeurs avant insertion (remplace 'nan', '', etc. par None)."""
    cleaned = {}
    for k, v in d.items():
        if isinstance(v, str):
            val = v.strip()
            if val.lower() in ('nan', '<na>', 'nat', ''):
                cleaned[k] = None
            else:
                cleaned[k] = val
        elif v is not None and type(v).__name__ in ('float', 'float64'):
            import math
            if math.isnan(v):
                cleaned[k] = None
            else:
                cleaned[k] = v
        else:
            cleaned[k] = v
    return cleaned

def insert_invoice(data):
    """Insère ou met à jour une facture dans la base de données."""
    data = sanitize_dict(data)
    conn = get_connection()
    cursor = conn.cursor()
    
    # Conversion de la liste Membres_Famille en JSON string
    membres_famille = data.get('Membres_Famille')
    if isinstance(membres_famille, list):
        membres_famille = json.dumps(membres_famille, ensure_ascii=False)
    
    try:
        cursor.execute('''
            INSERT INTO invoices (
                ID, Date, SequenceID, Nom, Prenom, Adresse, Attention_de, Nom_Enfant, 
                Naissance_Enfant, Attention_de2, Prenom2, Nom2, Membres_Famille, Prestation, 
                Date_Seance, Montant, Methode_Paiement, Date_Paiement, Date_Envoi_Email, Note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ID) DO UPDATE SET
                Date=excluded.Date,
                SequenceID=excluded.SequenceID,
                Nom=excluded.Nom,
                Prenom=excluded.Prenom,
                Adresse=excluded.Adresse,
                Attention_de=excluded.Attention_de,
                Nom_Enfant=excluded.Nom_Enfant,
                Naissance_Enfant=excluded.Naissance_Enfant,
                Attention_de2=excluded.Attention_de2,
                Prenom2=excluded.Prenom2,
                Nom2=excluded.Nom2,
                Membres_Famille=excluded.Membres_Famille,
                Prestation=excluded.Prestation,
                Date_Seance=excluded.Date_Seance,
                Montant=excluded.Montant,
                Methode_Paiement=excluded.Methode_Paiement,
                Date_Paiement=excluded.Date_Paiement,
                Date_Envoi_Email=excluded.Date_Envoi_Email,
                Note=excluded.Note
        ''', (
            data.get('ID'),
            data.get('Date'),
            data.get('SequenceID'),
            data.get('Nom'),
            data.get('Prenom'),
            data.get('Adresse'),
            data.get('Attention_de'),
            data.get('Nom_Enfant'),
            data.get('Naissance_Enfant'),
            data.get('Attention_de2'),
            data.get('Prenom2'),
            data.get('Nom2'),
            membres_famille,
            data.get('Prestation'),
            data.get('Date_Seance'),
            data.get('Montant'),
            data.get('Methode_Paiement'),
            data.get('Date_Paiement'),
            data.get('Date_Envoi_Email'),
            data.get('Note')
        ))
        conn.commit()
    finally:
        conn.close()

def delete_invoice_by_id(invoice_id):
    """Supprime une facture par son ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM invoices WHERE ID = ?', (invoice_id,))
    rows_deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_deleted > 0

def get_all_invoices(year=None, order_by_date_desc=True):
    """Retourne toutes les factures, potentiellement filtrées par année."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM invoices'
    params = []
    
    # Filtrage manuel par année en SQL (vu que les dates sont jj/mm/aaaa)
    # L'année dans jj/mm/aaaa correspond aux caractères à partir de l'index 7 dans SQLite.
    if year:
        query += ' WHERE SUBSTR(Date, 7, 4) = ?'
        params.append(str(year))
        
    query += ' ORDER BY SUBSTR(Date, 7, 4) DESC, SUBSTR(Date, 4, 2) DESC, SUBSTR(Date, 1, 2) DESC' if order_by_date_desc else ''
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Convertit les sqlite3.Row en dict
    results = [dict(row) for row in rows]
    
    # Post-traitement: re-convertir le JSON Membres_Famille en liste si existant
    for r in results:
        mf = r.get('Membres_Famille')
        if mf:
            try:
                r['Membres_Famille'] = json.loads(mf)
            except json.JSONDecodeError:
                r['Membres_Famille'] = mf
    
    conn.close()
    return results

def search_invoices(query=None, year=None, limit=5):
    """Recherche rapide de factures par nom/prénom du patient, et optionalement par année."""
    conn = get_connection()
    cursor = conn.cursor()
    
    sql_query = 'SELECT * FROM invoices WHERE 1=1'
    params = []
    
    if query:
        search_term = f'%{query}%'
        sql_query += ' AND (Nom LIKE ? OR Prenom LIKE ?)'
        params.extend([search_term, search_term])
        
    if year:
        sql_query += ' AND SUBSTR(Date, 7, 4) = ?'
        params.append(str(year))
        
    sql_query += ' ORDER BY SUBSTR(Date, 7, 4) DESC, SUBSTR(Date, 4, 2) DESC, SUBSTR(Date, 1, 2) DESC LIMIT ?'
    params.append(limit)
    
    cursor.execute(sql_query, params)
    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results

def advanced_search_invoices(year=None, month_index=None, prestation=None, status=None, query=None):
    """Recherche avancée multicritères utilisant SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    
    sql_query = 'SELECT * FROM invoices WHERE 1=1'
    params = []
    
    if year and year != "Toutes":
        sql_query += ' AND SUBSTR(Date, 7, 4) = ?'
        params.append(str(year))
        
    if month_index:
        month_str = f"{int(month_index):02d}"
        sql_query += ' AND SUBSTR(Date, 4, 2) = ?'
        params.append(month_str)

    if prestation and prestation != "Toutes":
        sql_query += ' AND Prestation = ?'
        params.append(prestation)
        
    if status == "Impayées":
        sql_query += ' AND Methode_Paiement = "Impayé"'
    elif status == "Payées":
        sql_query += ' AND Methode_Paiement != "Impayé"'
    elif status == "Non-lieu":
        sql_query += ' AND LOWER(Date_Seance) = "non-lieu"'
        
    if query:
        # Search across Nom, Prenom, and Nom_Enfant
        parts = query.lower().split()
        for part in parts:
            search_term = f'%{part}%'
            sql_query += ' AND (LOWER(Nom) LIKE ? OR LOWER(Prenom) LIKE ? OR LOWER(Nom_Enfant) LIKE ?)'
            params.extend([search_term, search_term, search_term])
            
    sql_query += ' ORDER BY SUBSTR(Date, 7, 4) DESC, SUBSTR(Date, 4, 2) DESC, SUBSTR(Date, 1, 2) DESC'
    
    cursor.execute(sql_query, params)
    rows = cursor.fetchall()
    
    results = [dict(row) for row in rows]
    conn.close()
    return results

def search_patients_for_suggestions(query_prenom, query_nom, limit=5):
    """Recherche les patients uniques pour les suggestions d'auto-complétion (depuis les factures)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    sql_query = """
        SELECT Nom, Prenom, Adresse, Prestation, Nom_Enfant, Naissance_Enfant, Prenom2, Nom2, Date
        FROM invoices WHERE 1=1
    """
    params = []
    
    if query_nom:
        sql_query += " AND Nom LIKE ?"
        params.append(f"{query_nom}%")
        
    if query_prenom:
        sql_query += " AND Prenom LIKE ?"
        params.append(f"{query_prenom}%")
        
    # On trie par date la plus récente
    sql_query += " ORDER BY SUBSTR(Date, 7, 4) DESC, SUBSTR(Date, 4, 2) DESC, SUBSTR(Date, 1, 2) DESC"
    
    cursor.execute(sql_query, params)
    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    
    # On doit dé-dupliquer manuellement en Python pour conserver les infos de la dernière facture
    unique_patients = []
    seen = set()
    for row in results:
        key = (str(row.get('Nom', '')).lower(), str(row.get('Prenom', '')).lower())
        if key not in seen:
            seen.add(key)
            unique_patients.append(row)
            if len(unique_patients) >= limit:
                break
                
    return unique_patients

def mark_invoices_as_sent(invoice_ids):
    """Met à jour la Date_Envoi_Email pour une liste d'IDs de factures."""
    if not invoice_ids: return
    
    today_str = datetime.now().strftime("%d/%m/%Y")
    conn = get_connection()
    cursor = conn.cursor()
    
    placeholders = ','.join('?' * len(invoice_ids))
    query = f"UPDATE invoices SET Date_Envoi_Email = ? WHERE ID IN ({placeholders})"
    
    params = [today_str] + invoice_ids
    cursor.execute(query, params)
    conn.commit()
    conn.close()

def get_next_sequence_id(year):
    """Calcule le prochain numéro de séquence disponible pour l'année donnée."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT SequenceID FROM invoices 
        WHERE SUBSTR(Date, 7, 4) = ?
    ''', (str(year),))
    
    rows = cursor.fetchall()
    conn.close()
    
    existing_seqs = set()
    for row in rows:
        try:
            seq = int(row['SequenceID'])
            existing_seqs.add(seq)
        except (ValueError, TypeError):
            pass
            
    seq = 1
    while seq in existing_seqs:
        seq += 1
    return seq

def check_duplicate_invoice(date_str, nom, prenom, montant_str):
    """Vérifie si une facture identique existe déjà."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT Montant FROM invoices
        WHERE Date = ? AND UPPER(Nom) = ? AND LOWER(Prenom) = ?
    ''', (date_str, nom.strip().upper(), prenom.strip().lower()))
    
    rows = cursor.fetchall()
    conn.close()
    
    try:
        target_montant = float(montant_str)
    except ValueError:
        return False
        
    for row in rows:
        try:
            db_montant = float(row['Montant'])
            if abs(db_montant - target_montant) < 0.01:
                return True
        except (ValueError, TypeError):
            pass
            
    return False

def get_available_invoice_years():
    """Retourne la liste des années disponibles (distinctes) dans la base de données."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT DISTINCT SUBSTR(Date, 7, 4) as Year FROM invoices ORDER BY Year DESC')
    rows = cursor.fetchall()
    conn.close()
    
    years = [row['Year'] for row in rows if row['Year']]
    return years

# --- Fonctions Frais (Expenses) ---

def insert_expense(data):
    """Insère ou met à jour une dépense dans la base de données."""
    data = sanitize_dict(data)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO expenses (
                ExpenseID, Date, Categorie, Description, Montant, ProofPath, CompteNum, Compte_Paiement, Est_Rembourse
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ExpenseID) DO UPDATE SET
                Date=excluded.Date,
                Categorie=excluded.Categorie,
                Description=excluded.Description,
                Montant=excluded.Montant,
                ProofPath=excluded.ProofPath,
                CompteNum=excluded.CompteNum,
                Compte_Paiement=excluded.Compte_Paiement,
                Est_Rembourse=excluded.Est_Rembourse
        ''', (
            data.get('ExpenseID'),
            data.get('Date'),
            data.get('Categorie'),
            data.get('Description'),
            data.get('Montant'),
            data.get('ProofPath'),
            data.get('CompteNum'),
            data.get('Compte_Paiement', 'Compte Pro'),
            data.get('Est_Rembourse', 0)
        ))
        conn.commit()
    finally:
        conn.close()

def get_all_expenses(year=None):
    """Retourne tous les frais, potentiellement filtrés par année."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM expenses'
    params = []
    
    if year:
        query += ' WHERE SUBSTR(Date, 7, 4) = ?'
        params.append(str(year))
        
    query += ' ORDER BY SUBSTR(Date, 7, 4) DESC, SUBSTR(Date, 4, 2) DESC, SUBSTR(Date, 1, 2) DESC'
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results

def delete_expense_by_id(expense_id):
    """Supprime une dépense par son ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM expenses WHERE ExpenseID = ?', (expense_id,))
    rows_deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_deleted > 0

def mark_expenses_as_reimbursed(expense_ids):
    """Marque une liste de dépenses comme remboursées."""
    if not expense_ids: return
    conn = get_connection()
    cursor = conn.cursor()
    placeholders = ','.join('?' * len(expense_ids))
    cursor.execute(f"UPDATE expenses SET Est_Rembourse = 1 WHERE ExpenseID IN ({placeholders})", expense_ids)
    conn.commit()
    conn.close()

def unmark_expenses_as_reimbursed(expense_ids):
    """Annule le remboursement d'une liste de dépenses."""
    if not expense_ids: return
    conn = get_connection()
    cursor = conn.cursor()
    placeholders = ','.join('?' * len(expense_ids))
    cursor.execute(f"UPDATE expenses SET Est_Rembourse = 0 WHERE ExpenseID IN ({placeholders})", expense_ids)
    conn.commit()
    conn.close()

