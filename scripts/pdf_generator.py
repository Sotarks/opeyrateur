import os
from fpdf import FPDF
import pandas as pd
from PIL import Image
from .utils import resource_path
from . import config
from .data_manager import get_invoice_path
from . import settings_manager
from datetime import datetime

class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        self.doc_type = kwargs.pop('doc_type', 'invoice') # 'invoice' or 'attestation'
        super().__init__(*args, **kwargs)
        self.alias_nb_pages() # Permet d'utiliser {nb} pour le nombre total de pages
        self.pdf_info = settings_manager.get_pdf_info()

    def footer(self):
        # On positionne le bloc de contact plus bas, pour qu'il soit juste au-dessus de la ligne
        self.set_y(-65)
        y_start = self.get_y()

        # --- Signature à gauche ---
        signature_path = resource_path(os.path.join("src", "signature.png"))
        text_x = 10 # Position X par défaut du texte
        
        if os.path.exists(signature_path):
            self.image(signature_path, x=10, y=y_start, w=40)
            text_x = 55 # Décale le texte vers la droite

        self.set_font('Arial', 'B', 11)
        self.set_text_color(0)
        self.set_x(text_x)
        self.cell(0, 6, self.pdf_info.get('practitioner_name', ''), ln=True, align='L')
        self.set_font('Arial', '', 10)
        self.set_x(text_x)
        self.cell(0, 5, self.pdf_info.get('practitioner_title', ''), ln=True, align='L')
        self.set_x(text_x)
        self.cell(0, 5, self.pdf_info.get('phone_number', ''), ln=True, align='L')
        
        email = self.pdf_info.get('email', '')
        if email:
            self.set_x(text_x)
            self.cell(0, 5, email, ln=True, align='L')

        if self.doc_type != 'attestation':
            self.ln(1)
            self.set_x(text_x)
            self.cell(0, 5, f"Siret : {self.pdf_info.get('siret', '')}", ln=True, align='L')

        # --- Ligne de séparation, mention TVA et pagination ---
        self.set_y(-25)
        self.set_font('Arial', 'I', 8)
        self.line(10, self.get_y(), 200, self.get_y())

        # Mention TVA sous la ligne
        if self.doc_type != 'attestation':
            self.ln(2) # Petit espace sous la ligne
            self.set_font('Arial', 'I', 9)
            self.set_text_color(128)
            self.cell(0, 5, "TVA non applicable, art. 293 B du CGI", ln=True, align='C')

        # Numérotation des pages en bas
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(0) # Remet la couleur du texte en noir
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'R')

def generate_pdf(data, is_duplicate=False):
    logo_path = resource_path(os.path.join("src", "logo.png"))
    pdf = PDF()
    pdf_info = pdf.pdf_info
    pdf.set_auto_page_break(auto=True, margin=85)
    pdf.add_page()

    # --- Filigrane DUPLICATA ---
    if is_duplicate:
        pdf.set_font('Arial', 'B', 60)
        pdf.set_text_color(220, 220, 220) # Gris clair
        with pdf.rotation(45, 105, 148): # Rotation de 45 degrés au centre de la page (A4)
            pdf.text(40, 150, "DUPLICATA")
        pdf.set_text_color(0) # Remet la couleur en noir

    # --- En-tête ---
    logo_exists = os.path.exists(logo_path)
    start_x = 60 if logo_exists else 10

    if logo_exists:
        pdf.image(logo_path, x=10, y=8, w=40)
    
    pdf.set_y(15)
    
    pdf.set_x(start_x)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, pdf_info.get('company_name', ''), ln=True)

    pdf.set_x(start_x)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, pdf_info.get('address_line1', ''), ln=True)
    pdf.set_x(start_x)
    pdf.cell(0, 5, pdf_info.get('address_line2', ''), ln=True)
    pdf.ln(2)
    pdf.set_x(start_x)
    pdf.cell(0, 5, f"Siret : {pdf_info.get('siret', '')}", ln=True)
    pdf.set_x(start_x)
    pdf.cell(0, 5, f"RPPS : {pdf_info.get('rpps', '')}", ln=True)

    # --- Titre de la facture ---
    pdf.set_y(55)
    pdf.set_font("Arial", 'B', 18)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 12, "Facture de suivi psychologique", ln=True, align='C', fill=True)
    pdf.ln(5)

    pdf.set_font("Arial", '', 11)
    pdf.cell(130)
    pdf.cell(50, 7, f"Date : {data['Date']}", ln=True, align='L')
    pdf.cell(130)
    pdf.cell(50, 7, f"Facture N° : {data['ID']}", ln=True, align='L')
    pdf.ln(5)

    # --- Informations du client ---
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 7, "Facturé à :", ln=True)
    pdf.set_font("Arial", '', 11)

    if data.get("Nom_Enfant"):
        attention_str = f"À l'attention de : {data['Attention_de']} {data['Prenom']} {data['Nom']}"
        if data.get("Nom2"):
            attention_str += f" et de {data['Attention_de2']} {data['Prenom2']} {data['Nom2']}"
        pdf.cell(0, 6, attention_str, ln=True)
        if data.get("Adresse"):
            pdf.cell(0, 6, data.get("Adresse"), ln=True)
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(0, 6, f"Pour l'enfant : {data['Nom_Enfant']}, né(e) le {data['Naissance_Enfant']}", ln=True)
    elif data.get("Membres_Famille"):
        pdf.cell(0, 6, f"À l'attention de : {data['Prenom']} {data['Nom']}", ln=True)
        if data.get("Adresse"):
            pdf.cell(0, 6, data.get("Adresse"), ln=True)
        pdf.cell(0, 6, "Pour les bénéficiaires suivants :", ln=True)
        pdf.set_font("Arial", '', 10)
        for member in data.get("Membres_Famille", []):
            pdf.cell(10)
            pdf.cell(0, 5, f"- {member}", ln=True)
    elif "couple" in data.get("Prestation", "").lower() and data.get("Nom2"):
        patient_str = f"Patients: {data['Prenom']} {data['Nom']} et {data['Prenom2']} {data['Nom2']}"
        pdf.cell(0, 6, patient_str, ln=True)
        if data.get("Adresse"):
            pdf.cell(0, 6, data.get("Adresse"), ln=True)
    else:
        pdf.cell(0, 6, f"Patient: {data['Prenom']} {data['Nom']}", ln=True)
        if data.get("Adresse"):
            pdf.cell(0, 6, data.get("Adresse"), ln=True)

    pdf.ln(15)

    # --- Tableau des prestations ---
    pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(120, 8, 'Description', 1, 0, 'L', fill=True)
    pdf.cell(30, 8, 'Date', 1, 0, 'C', fill=True)
    pdf.cell(40, 8, 'Montant', 1, 1, 'C', fill=True)

    y_before = pdf.get_y()
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(120, 7, data['Prestation'], border='LR', align='L')
    y_after = pdf.get_y()
    cell_height = y_after - y_before

    pdf.set_xy(10 + 120, y_before)
    pdf.cell(30, cell_height, data.get("Date_Seance", ""), border='R', align='C')
    pdf.cell(40, cell_height, f"{data['Montant']:.2f} EUR", border='R', ln=1, align='C')

    pdf.cell(190, 0, '', 'T', 1)

    # --- Total et mode de paiement ---
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(130)
    pdf.cell(20, 8, 'Total :', 0, 0, 'L')
    pdf.cell(40, 8, f"{data['Montant']:.2f} EUR", 1, 1, 'C')
    pdf.ln(5)

    if data.get("Methode_Paiement"):
        if data.get("Methode_Paiement") == "Impayé":
            pdf.set_font("Arial", 'B', 10)
            pdf.set_text_color(255, 0, 0)
            pdf.cell(0, 7, "Impayé", ln=True)
            pdf.set_text_color(0)
        else:
            payment_text = f"Payé par {data['Methode_Paiement']}"
            if data.get("Date_Paiement"):
                payment_text += f" le {data['Date_Paiement']}"
            payment_text += "."
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 7, payment_text, ln=True)

    # --- Sauvegarde du fichier ---
    full_path = get_invoice_path(data)
    output_dir = os.path.dirname(full_path)
    os.makedirs(output_dir, exist_ok=True)
    pdf.output(full_path)
    return full_path

def generate_attestation_pdf(data):
    """Génère un PDF d'attestation de présence."""
    pdf = PDF(doc_type='attestation')
    pdf_info = pdf.pdf_info
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()

    # --- En-tête (similaire à la facture) ---
    logo_path = resource_path(os.path.join("src", "logo.png"))
    logo_exists = os.path.exists(logo_path)
    start_x = 60 if logo_exists else 10

    if logo_exists:
        pdf.image(logo_path, x=10, y=8, w=40)
    
    pdf.set_y(15)
    
    pdf.set_x(start_x)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, pdf_info.get('company_name', ''), ln=True)

    pdf.set_x(start_x)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, pdf_info.get('address_line1', ''), ln=True)
    pdf.set_x(start_x)
    pdf.cell(0, 5, pdf_info.get('address_line2', ''), ln=True)
    pdf.ln(2)
    pdf.set_x(start_x)
    pdf.cell(0, 5, f"Siret : {pdf_info.get('siret', '')}", ln=True)
    pdf.set_x(start_x)
    pdf.cell(0, 5, f"RPPS : {pdf_info.get('rpps', '')}", ln=True)

    # Titre
    pdf.ln(20) # Espace après l'en-tête
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Attestation de Présence", ln=True, align='C')
    pdf.ln(20) # Espace après le titre

    # Corps du texte
    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 8, "Madame, Monsieur,")
    pdf.ln(10)
    
    message_template = pdf_info.get('attestation_message', "Erreur: Modèle de message non trouvé.")
    try:
        line1 = message_template.format(
            practitioner_name=pdf_info.get('practitioner_name', ''),
            practitioner_title=pdf_info.get('practitioner_title', ''),
            gender=data['gender'],
            patient_name=data['patient_name'],
            consultation_date=data['consultation_date']
        )
    except KeyError as e:
        line1 = f"Erreur dans le modèle de message : variable {e} manquante."
    pdf.multi_cell(0, 8, line1)
    pdf.ln(20)

    pdf.multi_cell(0, 8, "Cordialement,")
    pdf.ln(20)

    # Date de génération et lieu
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 8, f"Fait à {pdf_info.get('attestation_city', 'Carvin')}, le {data['generation_date']}", ln=True, align='R')

    # --- Sauvegarde du fichier ---
    try:
        consult_date_obj = datetime.strptime(data['consultation_date'], '%d/%m/%Y')
        filename_date_str = consult_date_obj.strftime('%Y%m%d')
    except ValueError:
        filename_date_str = datetime.now().strftime('%Y%m%d')

    safe_nom = "".join(c for c in data.get('patient_name', '').upper().replace(" ", "_") if c.isalnum() or c == '_')
    
    output_dir = config.ATTESTATIONS_DIR
    os.makedirs(output_dir, exist_ok=True)

    # Nouveau format de nom de fichier : ATTESTATION_NOM_DATECONSULTATION.pdf
    base_filename = f"ATTESTATION_{safe_nom}_{filename_date_str}"
    filename = f"{base_filename}.pdf"
    full_path = os.path.join(output_dir, filename)

    # Gère les doublons pour éviter d'écraser un fichier existant
    counter = 1
    while os.path.exists(full_path):
        filename = f"{base_filename}_{counter}.pdf"
        full_path = os.path.join(output_dir, filename)
        counter += 1

    pdf.output(full_path)
    return full_path

def generate_expenses_report(year, df_expenses):
    """Génère un PDF récapitulatif des frais pour l'année."""
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()

    # Titre
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Registre des Dépenses - Année {year}", ln=True, align='C')
    pdf.ln(10)

    def draw_header(pdf_instance):
        # Tableau
        pdf_instance.set_font("Arial", 'B', 10)
        pdf_instance.set_fill_color(240, 240, 240)
        
        # En-têtes
        pdf_instance.cell(30, 8, "Date", 1, 0, 'C', fill=True)
        pdf_instance.cell(40, 8, "Catégorie", 1, 0, 'C', fill=True)
        pdf_instance.cell(90, 8, "Description", 1, 0, 'C', fill=True)
        pdf_instance.cell(30, 8, "Montant", 1, 1, 'C', fill=True)

        pdf_instance.set_font("Arial", '', 10)

    draw_header(pdf)

    total = 0.0
    row_count = 0
    ENTRIES_PER_PAGE = 20

    # Create a copy to avoid SettingWithCopyWarning and sort by date
    df_expenses_copy = df_expenses.copy()
    try:
        df_expenses_copy['DateObj'] = pd.to_datetime(df_expenses_copy['Date'], format='%d/%m/%Y', errors='coerce')
        df_expenses_copy = df_expenses_copy.sort_values('DateObj')
    except Exception as e:
        print(f"Could not sort expenses by date: {e}")

    for _, row in df_expenses_copy.iterrows():
        if row_count >= ENTRIES_PER_PAGE:
            pdf.add_page()
            draw_header(pdf)
            row_count = 0

        date = str(row['Date'])
        cat = str(row['Categorie'])
        desc = str(row['Description'])
        montant = float(row['Montant'])
        total += montant

        # Gestion basique de la hauteur de ligne (description longue)
        pdf.cell(30, 8, date, 1, 0, 'C')
        pdf.cell(40, 8, cat[:20], 1, 0, 'L') # Tronque si trop long
        pdf.cell(90, 8, desc[:50], 1, 0, 'L')
        pdf.cell(30, 8, f"{montant:.2f} EUR", 1, 1, 'R')

        row_count += 1

    # Total
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(160, 10, "Total des dépenses :", 0, 0, 'R')
    pdf.cell(30, 10, f"{total:.2f} EUR", 1, 1, 'R')

    # --- Section Justificatifs ---
    df_with_proofs = df_expenses_copy[df_expenses_copy['ProofPath'].notna()].copy()

    if not df_with_proofs.empty:
        # Add a title page for the annexes
        pdf.add_page()
        pdf.set_font("Arial", 'B', 24)
        # Center the title vertically and horizontally
        pdf.cell(0, pdf.h - pdf.t_margin - pdf.b_margin, "Annexes - Justificatifs", 0, 1, 'C')

        for _, row in df_with_proofs.iterrows():
            proof_path = str(row['ProofPath'])
            if not os.path.exists(proof_path):
                continue

            pdf.add_page()
            
            # Header for the proof
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 8, f"Justificatif pour dépense du {row['Date']}", ln=True)
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 6, f"Catégorie : {row['Categorie']}", ln=True)
            pdf.cell(0, 6, f"Description : {row['Description']}", ln=True)
            pdf.cell(0, 6, f"Montant : {row['Montant']:.2f} EUR", ln=True)
            pdf.ln(10)

            # Check if it's an image
            image_extensions = ['.png', '.jpg', '.jpeg']
            _, ext = os.path.splitext(proof_path)
            if ext.lower() in image_extensions:
                try:
                    # Calcule l'espace disponible sur la page
                    available_width = pdf.w - pdf.l_margin - pdf.r_margin
                    available_height = pdf.h - pdf.b_margin - pdf.get_y() - 5 # Marge de 5mm

                    # Récupère les dimensions de l'image
                    with Image.open(proof_path) as img:
                        img_w, img_h = img.size
                    
                    if img_w == 0 or img_h == 0:
                        raise ValueError("Image invalide")

                    aspect_ratio = img_h / img_w

                    # Calcule la hauteur si on ajuste à la largeur disponible
                    scaled_height = available_width * aspect_ratio

                    if scaled_height > available_height:
                        pdf.image(proof_path, h=available_height)
                    else:
                        pdf.image(proof_path, w=available_width)
                except Exception as e:
                    pdf.set_font("Arial", 'I', 10)
                    pdf.set_text_color(255, 0, 0)
                    pdf.cell(0, 10, f"Erreur lors du chargement de l'image : {os.path.basename(proof_path)}", ln=True)
                    pdf.set_text_color(0)
            else: # For PDFs or other file types
                 pdf.set_font("Arial", 'I', 10)
                 pdf.cell(0, 10, f"Le justificatif est un fichier non-image (ex: PDF).", ln=True)
                 pdf.cell(0, 10, f"Nom du fichier : {os.path.basename(proof_path)}", ln=True)

    # Sauvegarde
    output_dir = os.path.join(config.FRAIS_DIR, str(year))
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"Rapport_Frais_{year}.pdf"
    full_path = os.path.join(output_dir, filename)
    pdf.output(full_path)
    return full_path

def generate_budget_report(year, month, quarter, df_budget):
    """Génère un rapport PDF pour le budget (mensuel ou annuel)."""
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()

    pdf.set_y(20) # Marge haute pour le titre

    # Titre
    title = f"Registre des Recettes - {year}"
    if month:
        title += f" - {month}"
    elif quarter:
        title += f" - {quarter}"
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, title, ln=True, align='C')
    pdf.ln(5)

    # Résumé
    total = df_budget['Montant'].sum() if not df_budget.empty and 'Montant' in df_budget.columns else 0
    count = len(df_budget)
    
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, f"Nombre de consultations : {count}", ln=True)
    pdf.cell(0, 8, f"Total Brut : {total:.2f} EUR", ln=True)
    pdf.ln(10)

    def draw_header(pdf_instance):
        # Tableau
        pdf_instance.set_font("Arial", 'B', 9)
        pdf_instance.set_fill_color(240, 240, 240)
        
        # En-têtes
        pdf_instance.cell(22, 8, "Date", 1, 0, 'C', fill=True)
        pdf_instance.cell(35, 8, "N Facture", 1, 0, 'C', fill=True)
        pdf_instance.cell(45, 8, "Patient", 1, 0, 'C', fill=True)
        pdf_instance.cell(45, 8, "Prestation", 1, 0, 'C', fill=True)
        pdf_instance.cell(23, 8, "Paiement", 1, 0, 'C', fill=True)
        pdf_instance.cell(20, 8, "Montant", 1, 1, 'C', fill=True)

        pdf_instance.set_font("Arial", '', 8)

    draw_header(pdf)

    if not df_budget.empty:
        # Tri par date
        try:
            df_budget = df_budget.copy()
            df_budget['DateObj'] = pd.to_datetime(df_budget['Date'], format='%d/%m/%Y', errors='coerce')
            df_budget = df_budget.sort_values('DateObj')
        except:
            pass

        row_count = 0
        ENTRIES_PER_PAGE = 20

        for _, row in df_budget.iterrows():
            if row_count >= ENTRIES_PER_PAGE:
                pdf.add_page()
                draw_header(pdf)
                row_count = 0

            patient_name = row.get('Nom_Enfant')
            if pd.isna(patient_name) or not patient_name:
                patient_name = f"{row.get('Prenom', '')} {row.get('Nom', '')}"
            
            patient = str(patient_name)

            pdf.cell(22, 8, str(row.get('Date', '')), 1, 0, 'C')
            pdf.cell(35, 8, str(row.get('ID', '')), 1, 0, 'C')
            pdf.cell(45, 8, patient[:25], 1, 0, 'L') # Tronque si trop long
            pdf.cell(45, 8, str(row.get('Prestation', ''))[:25], 1, 0, 'L')
            pdf.cell(23, 8, str(row.get('Methode_Paiement', ''))[:12], 1, 0, 'C')
            pdf.cell(20, 8, f"{row.get('Montant', 0):.2f}", 1, 1, 'R')
            
            row_count += 1

    # Sauvegarde
    os.makedirs(config.BUDGET_DIR, exist_ok=True)
    
    filename_part = f"{year}"
    if month:
        filename_part += f"_{month}"
    elif quarter:
        filename_part += f"_{quarter}"

    filename = f"Registre_Recettes_{filename_part}.pdf"
    full_path = os.path.join(config.BUDGET_DIR, filename)
    pdf.output(full_path)
    return full_path