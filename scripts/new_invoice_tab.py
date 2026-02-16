import customtkinter as ctk
from datetime import datetime

def create_new_invoice_tab(app):
    """Crée tous les widgets pour l'onglet 'Nouvelle Facture' et les attache à l'instance de l'application."""
    app.new_invoice_tab.grid_columnconfigure(0, weight=1)

    # --- Cadre Client/Patient ---
    client_frame = ctk.CTkFrame(app.new_invoice_tab, corner_radius=10)
    client_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
    client_frame.grid_columnconfigure(1, weight=1)

    client_label = ctk.CTkLabel(client_frame, text="Patient(s) :", font=ctk.CTkFont(size=16, weight="bold"))
    client_label.grid(row=0, column=0, columnspan=2, pady=(10, 15), sticky="w", padx=10)

    app.p1_civility_frame = ctk.CTkFrame(client_frame, fg_color="transparent")
    app.attention_var = ctk.CTkOptionMenu(app.p1_civility_frame, values=["Madame", "Monsieur"], width=110)
    app.attention_var.pack()

    p1_name_frame = ctk.CTkFrame(client_frame, fg_color="transparent")
    p1_name_frame.grid(row=1, column=1, sticky='ew', padx=(0, 10))
    p1_name_frame.grid_columnconfigure((0, 1), weight=1)
    app.prenom = ctk.CTkEntry(p1_name_frame, placeholder_text="Prénom")
    app.prenom.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="ew")
    app.nom = ctk.CTkEntry(p1_name_frame, placeholder_text="Nom")
    app.nom.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="ew")

    # Adresse
    app.adresse = ctk.CTkEntry(client_frame, placeholder_text="Adresse (optionnel)")
    app.adresse.grid(row=2, column=1, sticky='ew', padx=(0, 10), pady=(0, 10))

    # --- Cadre Consultation familiale ---
    app.family_frame = ctk.CTkFrame(app.new_invoice_tab, corner_radius=10)
    app.family_frame.grid_columnconfigure(0, weight=1)

    family_label = ctk.CTkLabel(app.family_frame, text="Membres de la famille (Optionnel)", font=ctk.CTkFont(size=16, weight="bold"))
    family_label.pack(fill="x", padx=15, pady=(10, 15))

    app.family_members_container = ctk.CTkFrame(app.family_frame, fg_color="transparent")
    app.family_members_container.pack(fill="x", expand=True, padx=10, pady=5)

    app.add_member_button = ctk.CTkButton(app.family_frame, text="Ajouter un membre", command=app._add_family_member)
    app.add_member_button.pack(pady=(5, 10), padx=10, fill="x")

    # --- Cadre Consultation de couple ---
    app.couple_frame = ctk.CTkFrame(app.new_invoice_tab, corner_radius=10)
    app.couple_frame.grid_columnconfigure(0, weight=1)

    p2_couple_label = ctk.CTkLabel(app.couple_frame, text="Second Partenaire (Optionnel)", font=ctk.CTkFont(size=16, weight="bold"))
    p2_couple_label.pack(fill="x", padx=15, pady=(10, 15))

    couple_partner2_frame = ctk.CTkFrame(app.couple_frame, fg_color="transparent")
    couple_partner2_frame.pack(fill="x", expand=True, padx=10, pady=(0, 5))
    couple_partner2_frame.grid_columnconfigure((0, 1), weight=1)

    app.prenom2_couple = ctk.CTkEntry(couple_partner2_frame, placeholder_text="Prénom Partenaire 2")
    app.prenom2_couple.grid(row=0, column=0, padx=(0, 5), sticky="ew")
    app.nom2_couple = ctk.CTkEntry(couple_partner2_frame, placeholder_text="Nom Partenaire 2")
    app.nom2_couple.grid(row=0, column=1, padx=(5, 0), sticky="ew")

    # --- Cadre Informations enfant ---
    app.child_info_frame = ctk.CTkFrame(app.new_invoice_tab, corner_radius=10)
    app.child_info_frame.grid_columnconfigure(0, weight=1)
    
    p2_label = ctk.CTkLabel(app.child_info_frame, text="Second Parent (Optionnel)", font=ctk.CTkFont(size=14, weight="bold"))
    p2_label.pack(fill="x", padx=15, pady=(10, 5))
    
    parent2_frame = ctk.CTkFrame(app.child_info_frame, fg_color="transparent")
    parent2_frame.pack(fill="x", padx=10, pady=(0, 10))
    parent2_frame.grid_columnconfigure(1, weight=1)
    parent2_frame.grid_columnconfigure(2, weight=1)
    app.attention_var2 = ctk.CTkOptionMenu(parent2_frame, values=["Madame", "Monsieur"], width=110)
    app.attention_var2.grid(row=0, column=0, padx=(0, 5))
    app.prenom2 = ctk.CTkEntry(parent2_frame, placeholder_text="Prénom")
    app.prenom2.grid(row=0, column=1, padx=(0, 5), sticky="ew")
    app.nom2 = ctk.CTkEntry(parent2_frame, placeholder_text="Nom")
    app.nom2.grid(row=0, column=2, padx=(5, 0), sticky="ew")

    child_details_label = ctk.CTkLabel(app.child_info_frame, text="Informations sur l'enfant", font=ctk.CTkFont(size=14, weight="bold"))
    child_details_label.pack(fill="x", padx=15, pady=(10, 5))
    
    app.enfant_nom = ctk.CTkEntry(app.child_info_frame, placeholder_text="Prénom & Nom de l'enfant")
    app.enfant_nom.pack(fill="x", padx=10, pady=(0, 5))
    app.enfant_dob = ctk.CTkEntry(app.child_info_frame, placeholder_text="Cliquer pour choisir la date de naissance")
    app.enfant_dob.pack(fill="x", padx=10, pady=(0, 10))
    app.enfant_dob.configure(state="readonly")
    app.enfant_dob.bind("<1>", lambda event: app._open_calendar(app.enfant_dob))

    # --- Cadre Détails Facture ---
    details_frame = ctk.CTkFrame(app.new_invoice_tab, corner_radius=10)
    details_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
    details_frame.grid_columnconfigure(0, weight=1)

    details_label = ctk.CTkLabel(details_frame, text="Détails de la Facture", font=ctk.CTkFont(size=16, weight="bold"))
    details_label.grid(row=0, column=0, pady=(10, 15), sticky="w", padx=10)

    seance_date_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
    seance_date_frame.grid(row=1, column=0, sticky="ew", padx=10)
    seance_date_frame.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(seance_date_frame, text="Date de la séance").grid(row=0, column=0, columnspan=2, pady=(5, 0), sticky="w")
    app.seance_date = ctk.CTkEntry(seance_date_frame, placeholder_text="JJ/MM/AAAA")
    app.seance_date.grid(row=1, column=0, pady=(0, 10), sticky="ew")
    app.seance_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
    app.seance_date.configure(state="readonly")
    app.seance_date.bind("<1>", lambda event: app._open_calendar(app.seance_date))

    app.seance_non_lieu_var = ctk.BooleanVar()
    app.seance_non_lieu_check = ctk.CTkCheckBox(seance_date_frame, text="Non-lieu", variable=app.seance_non_lieu_var, command=app._toggle_seance_date)
    app.seance_non_lieu_check.grid(row=1, column=1, padx=(10, 0), pady=(0, 10))

    prestation_montant_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
    prestation_montant_frame.grid(row=2, column=0, sticky="ew", padx=10)
    prestation_montant_frame.grid_columnconfigure(0, weight=2)
    prestation_montant_frame.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(prestation_montant_frame, text="Type de séance").grid(row=0, column=0, sticky="w")
    app.prestation = ctk.CTkOptionMenu(prestation_montant_frame, values=list(app.prestations_prix.keys()), command=app._update_form)
    app.prestation.grid(row=1, column=0, pady=5, sticky="ew", padx=(0, 5))

    ctk.CTkLabel(prestation_montant_frame, text="Prix").grid(row=0, column=1, sticky="w")
    app.montant = ctk.CTkEntry(prestation_montant_frame, placeholder_text="Montant")
    app.montant.grid(row=1, column=1, pady=5, sticky="ew", padx=(5, 0))

    payment_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
    payment_frame.grid(row=3, column=0, sticky="ew", pady=(10, 10), padx=10)
    payment_frame.grid_columnconfigure((0, 1), weight=1)

    ctk.CTkLabel(payment_frame, text="Mode de paiement").grid(row=0, column=0, sticky="w")
    app.payment_method = ctk.CTkOptionMenu(payment_frame, values=["Virement", "Espèce", "Chèque", "Impayé"], command=app._toggle_payment_date_field)
    app.payment_method.grid(row=1, column=0, pady=5, sticky="ew", padx=(0, 5))
    app.payment_method.set("Virement")

    app.payment_date_label = ctk.CTkLabel(payment_frame, text="Date de paiement")
    app.payment_date_entry = ctk.CTkEntry(payment_frame, placeholder_text="JJ/MM/AAAA")
    app.payment_date_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
    app.payment_date_entry.configure(state="readonly")
    app.payment_date_entry.bind("<1>", lambda event: app._open_calendar(app.payment_date_entry))

    # Note personnelle
    ctk.CTkLabel(details_frame, text="Note personnelle (interne)").grid(row=4, column=0, sticky="w", padx=10, pady=(5, 0))
    app.personal_note = ctk.CTkEntry(details_frame, placeholder_text="Ne sera pas affiché sur le PDF")
    app.personal_note.grid(row=5, column=0, sticky="ew", padx=10, pady=(0, 10))

    app.btn = ctk.CTkButton(app.new_invoice_tab, text="Enregistrer & Générer PDF", command=app.valider, height=45, font=ctk.CTkFont(size=14, weight="bold"))
    app.btn.grid(row=3, column=0, padx=10, pady=20, sticky="sew")
    app.new_invoice_tab.grid_rowconfigure(3, weight=1)