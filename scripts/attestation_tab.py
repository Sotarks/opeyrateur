import customtkinter as ctk
from datetime import datetime

def create_attestation_tab(app):
    """Crée les widgets pour l'onglet 'Attestation'."""
    app.attestation_tab.grid_columnconfigure(0, weight=1)
    app.attestation_tab.grid_rowconfigure(1, weight=1)

    # --- Formulaire ---
    form_frame = ctk.CTkFrame(app.attestation_tab, corner_radius=10)
    form_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
    form_frame.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(form_frame, text="Générer une Attestation", font=app.font_large).grid(row=0, column=0, columnspan=2, pady=(10, 20), padx=10)

    # Date de la consultation
    ctk.CTkLabel(form_frame, text="Date de la consultation :").grid(row=1, column=0, padx=10, pady=10, sticky="w")
    app.attestation_consult_date = ctk.CTkEntry(form_frame, placeholder_text="JJ/MM/AAAA")
    app.attestation_consult_date.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
    app.attestation_consult_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
    app.attestation_consult_date.configure(state="readonly")
    app.attestation_consult_date.bind("<1>", lambda event: app._open_calendar(app.attestation_consult_date))

    # Date de génération
    ctk.CTkLabel(form_frame, text="Date de génération :").grid(row=2, column=0, padx=10, pady=10, sticky="w")
    app.attestation_generation_date = ctk.CTkEntry(form_frame)
    app.attestation_generation_date.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
    app.attestation_generation_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
    app.attestation_generation_date.configure(state="readonly")
    app.attestation_generation_date.bind("<1>", lambda event: app._open_calendar(app.attestation_generation_date))

    # Genre du patient
    ctk.CTkLabel(form_frame, text="Genre du patient :").grid(row=3, column=0, padx=10, pady=10, sticky="w")
    app.attestation_gender = ctk.CTkOptionMenu(form_frame, values=["Madame", "Monsieur"])
    app.attestation_gender.grid(row=3, column=1, padx=10, pady=10, sticky="w")
    app.attestation_gender.set("Madame")

    # Nom du patient
    ctk.CTkLabel(form_frame, text="Nom complet du patient :").grid(row=4, column=0, padx=10, pady=10, sticky="w")
    app.attestation_patient_name = ctk.CTkEntry(form_frame, placeholder_text="Prénom Nom")
    app.attestation_patient_name.grid(row=4, column=1, padx=10, pady=10, sticky="ew")

    # Bouton Générer
    app.generate_attestation_btn = ctk.CTkButton(app.attestation_tab, text="Générer l'attestation PDF", command=app._generate_attestation_pdf, height=45, font=app.font_button)
    app.generate_attestation_btn.grid(row=2, column=0, padx=20, pady=20, sticky="sew")