import customtkinter as ctk
from datetime import datetime

def create_new_invoice_tab(app):
    """Crée tous les widgets pour l'onglet 'Nouvelle Facture' et les attache à l'instance de l'application."""
    # Configuration de la grille principale : 2 colonnes égales
    app.new_invoice_tab.grid_columnconfigure(0, weight=1)
    app.new_invoice_tab.grid_columnconfigure(1, weight=1)
    app.new_invoice_tab.grid_rowconfigure(0, weight=1)

    # =================================================================================
    # COLONNE GAUCHE : INFORMATIONS PATIENT
    # =================================================================================
    left_panel = ctk.CTkFrame(app.new_invoice_tab, fg_color="transparent")
    left_panel.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
    left_panel.grid_columnconfigure(0, weight=1)

    # Titre Section
    ctk.CTkLabel(left_panel, text="1. Informations Patient", font=app.font_title, text_color="#3498db").grid(row=0, column=0, sticky="w", pady=(0, 15))

    # --- Carte Identité Standard ---
    client_frame = ctk.CTkFrame(left_panel, corner_radius=15, fg_color=("white", "gray20"))
    client_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
    client_frame.grid_columnconfigure(1, weight=1)

    # Civilité & Nom
    app.p1_civility_frame = ctk.CTkFrame(client_frame, fg_color="transparent")
    # Note: Le placement grid de p1_civility_frame est géré dynamiquement par InvoiceManager
    
    app.attention_var = ctk.CTkOptionMenu(app.p1_civility_frame, values=["Madame", "Monsieur"], width=100, height=35)
    app.attention_var.pack(pady=5)

    p1_name_frame = ctk.CTkFrame(client_frame, fg_color="transparent")
    p1_name_frame.grid(row=1, column=1, sticky='ew', padx=15, pady=15)
    p1_name_frame.grid_columnconfigure((0, 1), weight=1)
    
    ctk.CTkLabel(p1_name_frame, text="Prénom", font=app.font_bold, text_color="gray").grid(row=0, column=0, sticky="w", padx=(0, 5))
    ctk.CTkLabel(p1_name_frame, text="Nom", font=app.font_bold, text_color="gray").grid(row=0, column=1, sticky="w", padx=(5, 0))
    
    app.prenom = ctk.CTkEntry(p1_name_frame, height=40, font=app.font_large)
    app.prenom.grid(row=1, column=0, padx=(0, 5), sticky="ew")
    
    app.nom = ctk.CTkEntry(p1_name_frame, height=40, font=app.font_large)
    app.nom.grid(row=1, column=1, padx=(5, 0), sticky="ew")

    # Adresse
    ctk.CTkLabel(client_frame, text="Adresse complète (optionnel)", font=app.font_bold, text_color="gray").grid(row=2, column=1, sticky="w", padx=15, pady=(0, 5))
    app.adresse = ctk.CTkEntry(client_frame, height=35)
    app.adresse.grid(row=3, column=1, sticky='ew', padx=15, pady=(0, 15))

    # --- Cadres Dynamiques (Enfant / Famille / Couple) ---
    # Ces cadres seront placés en row=2 par InvoiceManager
    
    # 1. Famille
    app.family_frame = ctk.CTkFrame(left_panel, corner_radius=15, fg_color=("white", "gray20"))
    app.family_frame.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(app.family_frame, text="Membres de la famille", font=app.font_bold, text_color="gray").pack(anchor="w", padx=15, pady=(10, 5))

    app.family_members_container = ctk.CTkFrame(app.family_frame, fg_color="transparent")
    app.family_members_container.pack(fill="x", expand=True, padx=10, pady=5)

    app.add_member_button = ctk.CTkButton(app.family_frame, text="+ Ajouter un membre", command=app.invoice_manager.add_family_member, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))
    app.add_member_button.pack(pady=(5, 10), padx=10, fill="x")

    # 2. Couple
    app.couple_frame = ctk.CTkFrame(left_panel, corner_radius=15, fg_color=("white", "gray20"))
    app.couple_frame.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(app.couple_frame, text="Second Partenaire", font=app.font_bold, text_color="gray").pack(anchor="w", padx=15, pady=(10, 5))

    couple_partner2_frame = ctk.CTkFrame(app.couple_frame, fg_color="transparent")
    couple_partner2_frame.pack(fill="x", expand=True, padx=10, pady=10)
    couple_partner2_frame.grid_columnconfigure((0, 1), weight=1)

    ctk.CTkLabel(couple_partner2_frame, text="Prénom", font=app.font_bold, text_color="gray").grid(row=0, column=0, sticky="w", padx=(0, 5))
    ctk.CTkLabel(couple_partner2_frame, text="Nom", font=app.font_bold, text_color="gray").grid(row=0, column=1, sticky="w", padx=(5, 0))

    app.prenom2_couple = ctk.CTkEntry(couple_partner2_frame, height=35)
    app.prenom2_couple.grid(row=1, column=0, padx=(0, 5), sticky="ew")
    app.nom2_couple = ctk.CTkEntry(couple_partner2_frame, height=35)
    app.nom2_couple.grid(row=1, column=1, padx=(5, 0), sticky="ew")

    # 3. Enfant
    app.child_info_frame = ctk.CTkFrame(left_panel, corner_radius=15, fg_color=("white", "gray20"))
    app.child_info_frame.grid_columnconfigure(0, weight=1)
    
    ctk.CTkLabel(app.child_info_frame, text="Informations Enfant", font=app.font_bold, text_color="gray").pack(anchor="w", padx=15, pady=(10, 5))
    
    ctk.CTkLabel(app.child_info_frame, text="Prénom & Nom", font=app.font_bold, text_color="gray").pack(anchor="w", padx=15, pady=(5, 0))
    app.enfant_nom = ctk.CTkEntry(app.child_info_frame, height=35)
    app.enfant_nom.pack(fill="x", padx=15, pady=(0, 5))
    
    ctk.CTkLabel(app.child_info_frame, text="Date de naissance", font=app.font_bold, text_color="gray").pack(anchor="w", padx=15, pady=(5, 0))
    app.enfant_dob = ctk.CTkEntry(app.child_info_frame, height=35)
    app.enfant_dob.pack(fill="x", padx=15, pady=(0, 10))
    app.enfant_dob.configure(state="readonly")
    app.enfant_dob.bind("<1>", lambda event: app._open_calendar(app.enfant_dob))

    ctk.CTkLabel(app.child_info_frame, text="Second Parent (Optionnel)", font=app.font_bold, text_color="gray").pack(anchor="w", padx=15, pady=(10, 5))
    
    parent2_frame = ctk.CTkFrame(app.child_info_frame, fg_color="transparent")
    parent2_frame.pack(fill="x", padx=10, pady=(0, 15))
    parent2_frame.grid_columnconfigure(1, weight=1)
    parent2_frame.grid_columnconfigure(2, weight=1)
    
    ctk.CTkLabel(parent2_frame, text="Prénom", font=app.font_bold, text_color="gray").grid(row=0, column=1, sticky="w", padx=(0, 5))
    ctk.CTkLabel(parent2_frame, text="Nom", font=app.font_bold, text_color="gray").grid(row=0, column=2, sticky="w", padx=(5, 0))

    app.attention_var2 = ctk.CTkOptionMenu(parent2_frame, values=["Madame", "Monsieur"], width=100, height=35)
    app.attention_var2.grid(row=1, column=0, padx=(0, 5))
    app.prenom2 = ctk.CTkEntry(parent2_frame, height=35)
    app.prenom2.grid(row=1, column=1, padx=(0, 5), sticky="ew")
    app.nom2 = ctk.CTkEntry(parent2_frame, height=35)
    app.nom2.grid(row=1, column=2, padx=(5, 0), sticky="ew")

    # =================================================================================
    # COLONNE DROITE : FACTURATION
    # =================================================================================
    right_panel = ctk.CTkFrame(app.new_invoice_tab, fg_color="transparent")
    right_panel.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
    right_panel.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(right_panel, text="2. Détails de la séance", font=app.font_title, text_color="#e67e22").grid(row=0, column=0, sticky="w", pady=(0, 15))

    # --- Carte Détails ---
    details_frame = ctk.CTkFrame(right_panel, corner_radius=15, fg_color=("white", "gray20"))
    details_frame.grid(row=1, column=0, sticky="ew")
    details_frame.grid_columnconfigure(0, weight=1)

    # Date Séance
    ctk.CTkLabel(details_frame, text="Date de la séance", font=app.font_bold).pack(anchor="w", padx=20, pady=(15, 5))
    
    date_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
    date_frame.pack(fill="x", padx=20)
    
    app.seance_date = ctk.CTkEntry(date_frame, placeholder_text="JJ/MM/AAAA", height=40)
    app.seance_date.pack(side="left", fill="x", expand=True)
    app.seance_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
    app.seance_date.configure(state="readonly")
    app.seance_date.bind("<1>", lambda event: app._open_calendar(app.seance_date))

    app.seance_non_lieu_var = ctk.BooleanVar()
    app.seance_non_lieu_check = ctk.CTkCheckBox(date_frame, text="Non-lieu", variable=app.seance_non_lieu_var, command=app.invoice_manager.toggle_seance_date)
    app.seance_non_lieu_check.pack(side="left", padx=(15, 0))

    # Prestation & Montant
    ctk.CTkLabel(details_frame, text="Prestation & Prix", font=app.font_bold).pack(anchor="w", padx=20, pady=(15, 5))
    
    pres_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
    pres_frame.pack(fill="x", padx=20)
    
    app.prestation = ctk.CTkOptionMenu(pres_frame, values=list(app.prestations_prix.keys()), command=app.invoice_manager.update_form, height=40)
    app.prestation.pack(side="left", fill="x", expand=True, padx=(0, 10))
    
    app.montant = ctk.CTkEntry(pres_frame, placeholder_text="Prix", width=100, height=40, font=ctk.CTkFont(size=16, weight="bold"))
    app.montant.pack(side="right")

    # Paiement
    ctk.CTkLabel(details_frame, text="Règlement", font=app.font_bold).pack(anchor="w", padx=20, pady=(15, 5))
    
    payment_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
    payment_frame.pack(fill="x", padx=20, pady=(0, 15))
    payment_frame.grid_columnconfigure((0, 1), weight=1)

    app.payment_method = ctk.CTkOptionMenu(payment_frame, values=["Virement", "Espèce", "Chèque", "Impayé"], command=app.invoice_manager.toggle_payment_date_field, height=40)
    app.payment_method.grid(row=0, column=0, sticky="ew", padx=(0, 5))
    app.payment_method.set("Virement")

    app.payment_date_label = ctk.CTkLabel(payment_frame, text="Date :", width=40) # Sera caché/affiché
    app.payment_date_entry = ctk.CTkEntry(payment_frame, placeholder_text="JJ/MM/AAAA", height=40)
    app.payment_date_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
    app.payment_date_entry.configure(state="readonly")
    app.payment_date_entry.bind("<1>", lambda event: app._open_calendar(app.payment_date_entry))

    # Note personnelle
    ctk.CTkLabel(details_frame, text="Note interne (optionnel)", font=app.font_bold, text_color="gray").pack(anchor="w", padx=20, pady=(5, 5))
    app.personal_note = ctk.CTkEntry(details_frame, placeholder_text="Ne sera pas affiché sur le PDF", height=35)
    app.personal_note.pack(fill="x", padx=20, pady=(0, 20))

    # Boutons d'action
    action_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
    action_frame.grid(row=2, column=0, sticky="ew", pady=20)
    action_frame.grid_columnconfigure(0, weight=1)
    action_frame.grid_columnconfigure(1, weight=1)

    app.clear_btn = ctk.CTkButton(action_frame, text="Effacer", command=app.invoice_manager.reset_form, height=50, font=app.font_button, fg_color="gray50", hover_color="gray30")
    app.clear_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")

    app.btn = ctk.CTkButton(action_frame, text="VALIDER LA FACTURE", command=app.invoice_manager.valider, height=50, font=app.font_button)
    app.btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")