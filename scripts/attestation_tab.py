import customtkinter as ctk
from datetime import datetime
import os
from . import config

def create_attestation_tab(app):
    """Crée les widgets pour l'onglet 'Attestation'."""
    # Configuration : 2 colonnes égales
    app.attestation_tab.grid_columnconfigure(0, weight=1)
    app.attestation_tab.grid_columnconfigure(1, weight=1)
    app.attestation_tab.grid_rowconfigure(1, weight=1)

    # =================================================================================
    # COLONNE GAUCHE : INFORMATIONS PATIENT
    # =================================================================================
    left_panel = ctk.CTkFrame(app.attestation_tab, fg_color="transparent")
    left_panel.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
    left_panel.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(left_panel, text="1. Informations Patient", font=app.font_title, text_color="#3498db").grid(row=0, column=0, sticky="w", pady=(0, 15))

    # Carte Patient
    patient_frame = ctk.CTkFrame(left_panel, corner_radius=15, fg_color=("white", "gray20"))
    patient_frame.grid(row=1, column=0, sticky="ew")
    patient_frame.grid_columnconfigure(0, weight=1)

    # Civilité
    ctk.CTkLabel(patient_frame, text="Civilité", font=app.font_bold, text_color="gray").pack(anchor="w", padx=20, pady=(15, 5))
    app.attestation_gender = ctk.CTkOptionMenu(patient_frame, values=["Madame", "Monsieur"], height=40)
    app.attestation_gender.pack(fill="x", padx=20, pady=(0, 15))
    app.attestation_gender.set("Madame")

    # Nom
    ctk.CTkLabel(patient_frame, text="Nom complet du patient", font=app.font_bold, text_color="gray").pack(anchor="w", padx=20, pady=(5, 5))
    app.attestation_patient_name = ctk.CTkEntry(patient_frame, placeholder_text="Prénom Nom", height=40, font=app.font_large)
    app.attestation_patient_name.pack(fill="x", padx=20, pady=(0, 20))

    # =================================================================================
    # COLONNE DROITE : DÉTAILS & ACTION
    # =================================================================================
    right_panel = ctk.CTkFrame(app.attestation_tab, fg_color="transparent")
    right_panel.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
    right_panel.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(right_panel, text="2. Détails de l'acte", font=app.font_title, text_color="#e67e22").grid(row=0, column=0, sticky="w", pady=(0, 15))

    # Carte Détails
    details_frame = ctk.CTkFrame(right_panel, corner_radius=15, fg_color=("white", "gray20"))
    details_frame.grid(row=1, column=0, sticky="ew")
    details_frame.grid_columnconfigure(0, weight=1)

    # Date Consultation
    ctk.CTkLabel(details_frame, text="Date de la consultation", font=app.font_bold, text_color="gray").pack(anchor="w", padx=20, pady=(15, 5))
    
    date_consult_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
    date_consult_frame.pack(fill="x", padx=20, pady=(0, 15))
    
    app.attestation_consult_date = ctk.CTkEntry(date_consult_frame, placeholder_text="JJ/MM/AAAA", height=40)
    app.attestation_consult_date.pack(side="left", fill="x", expand=True)
    app.attestation_consult_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
    app.attestation_consult_date.configure(state="readonly")
    app.attestation_consult_date.bind("<1>", lambda event: app._open_calendar(app.attestation_consult_date))

    # Date Génération
    ctk.CTkLabel(details_frame, text="Date de l'attestation", font=app.font_bold, text_color="gray").pack(anchor="w", padx=20, pady=(5, 5))
    
    date_gen_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
    date_gen_frame.pack(fill="x", padx=20, pady=(0, 20))
    
    app.attestation_generation_date = ctk.CTkEntry(date_gen_frame, placeholder_text="JJ/MM/AAAA", height=40)
    app.attestation_generation_date.pack(side="left", fill="x", expand=True)
    app.attestation_generation_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
    app.attestation_generation_date.configure(state="readonly")
    app.attestation_generation_date.bind("<1>", lambda event: app._open_calendar(app.attestation_generation_date))

    # Bouton Action
    action_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
    action_frame.grid(row=2, column=0, sticky="ew", pady=20)
    action_frame.grid_columnconfigure(0, weight=1)

    app.generate_attestation_btn = ctk.CTkButton(action_frame, text="GÉNÉRER L'ATTESTATION PDF", command=app._generate_attestation_pdf, height=50, font=app.font_button)
    app.generate_attestation_btn.grid(row=0, column=0, sticky="ew")

    # --- Historique (Bas de page) ---
    history_container = ctk.CTkFrame(app.attestation_tab, corner_radius=0, fg_color="transparent")
    history_container.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=20, pady=(0, 20))
    history_container.grid_columnconfigure(0, weight=1)
    history_container.grid_rowconfigure(1, weight=1)

    ctk.CTkLabel(history_container, text="Historique des attestations", font=app.font_title, text_color="#3498db").grid(row=0, column=0, sticky="w", pady=(10, 10))

    app.attestation_history_frame = ctk.CTkScrollableFrame(history_container, corner_radius=15, fg_color=("white", "gray20"), height=200)
    app.attestation_history_frame.grid(row=1, column=0, sticky="nsew")

def refresh_attestation_history(app):
    """Met à jour la liste des attestations générées."""
    for widget in app.attestation_history_frame.winfo_children():
        widget.destroy()

    if not os.path.exists(config.ATTESTATIONS_DIR):
        ctk.CTkLabel(app.attestation_history_frame, text="Aucune attestation générée.", text_color="gray").pack(pady=20)
        return

    files = [f for f in os.listdir(config.ATTESTATIONS_DIR) if f.endswith('.pdf')]
    # Tri par date de modification (plus récent en premier)
    files.sort(key=lambda x: os.path.getmtime(os.path.join(config.ATTESTATIONS_DIR, x)), reverse=True)

    if not files:
        ctk.CTkLabel(app.attestation_history_frame, text="Aucune attestation générée.", text_color="gray").pack(pady=20)
        return

    for filename in files:
        row = ctk.CTkFrame(app.attestation_history_frame, fg_color="transparent")
        row.pack(fill="x", pady=5, padx=10)
        
        # Icone PDF
        ctk.CTkLabel(row, text="📄", font=ctk.CTkFont(size=20)).pack(side="left", padx=(0, 10))
        
        # Nom du fichier
        ctk.CTkLabel(row, text=filename, font=app.font_bold).pack(side="left")
        
        # Date de modification
        filepath = os.path.join(config.ATTESTATIONS_DIR, filename)
        mod_time = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%d/%m/%Y %H:%M")
        ctk.CTkLabel(row, text=mod_time, text_color="gray").pack(side="left", padx=20)
        
        # Boutons
        btn_frame = ctk.CTkFrame(row, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(btn_frame, text="✉️", width=40, height=30, fg_color="#3498db", hover_color="#2980b9", command=lambda f=filepath: app.invoice_actions._prompt_send_email(pdf_path=f)).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Ouvrir", width=80, height=30, command=lambda f=filepath: _open_attestation(app, f)).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Dossier", width=80, height=30, fg_color="gray50", hover_color="gray30", command=lambda f=filepath: os.startfile(os.path.dirname(f))).pack(side="left", padx=5)

def _open_attestation(app, filepath):
    from .pdf_viewer import PDFViewer
    if os.path.exists(filepath):
        PDFViewer(app, filepath)