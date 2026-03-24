import os
from fpdf import FPDF
from opeyrateur_app.utils.utils import resource_path
from opeyrateur_app.core import settings_manager

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
