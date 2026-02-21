import customtkinter as ctk

def create_search_tab(app):
    """Crée les widgets pour l'onglet 'Rechercher' et les attache à l'instance de l'application."""
    # Configuration : 2 colonnes (Sidebar Filtres | Contenu Résultats)
    app.search_tab.grid_columnconfigure(0, weight=0, minsize=320) # Sidebar fixe
    app.search_tab.grid_columnconfigure(1, weight=1) # Contenu extensible
    app.search_tab.grid_rowconfigure(0, weight=1)

    # =================================================================================
    # 1. SIDEBAR (GAUCHE) - Filtres & Recherche
    # =================================================================================
    sidebar = ctk.CTkFrame(app.search_tab, corner_radius=0, fg_color=("gray90", "gray16"))
    sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 1))
    sidebar.grid_columnconfigure(0, weight=1)

    # Titre
    ctk.CTkLabel(sidebar, text="Filtres & Recherche", font=app.font_large).pack(pady=(20, 15), padx=20, anchor="w")

    from .data_manager import get_available_years, MONTHS_FR

    # --- Carte Filtres ---
    filter_card = ctk.CTkFrame(sidebar, corner_radius=15, fg_color=("white", "gray20"))
    filter_card.pack(fill="x", padx=20, pady=(0, 20))

    # Période (Année / Mois)
    ctk.CTkLabel(filter_card, text="Période", font=app.font_bold).pack(anchor="w", padx=15, pady=(15, 5))
    
    period_frame = ctk.CTkFrame(filter_card, fg_color="transparent")
    period_frame.pack(fill="x", padx=10, pady=(0, 10))
    
    years = ["Toutes"] + get_available_years()
    app.search_year_var = ctk.StringVar(value=years[0])
    app.search_year_menu = ctk.CTkOptionMenu(period_frame, variable=app.search_year_var, values=years, command=app._on_search_year_change, width=100)
    app.search_year_menu.pack(side="left", padx=(0, 5), fill="x", expand=True)

    months = ["Tous"] + MONTHS_FR
    app.search_month_var = ctk.StringVar(value="Tous")
    app.search_month_menu = ctk.CTkOptionMenu(period_frame, variable=app.search_month_var, values=months, width=120)
    app.search_month_menu.pack(side="left", fill="x", expand=True)
    app.search_month_menu.configure(state="disabled")

    # Type de séance
    ctk.CTkLabel(filter_card, text="Type de séance", font=app.font_bold).pack(anchor="w", padx=15, pady=(5, 5))
    prestations = ["Toutes"] + list(app.prestations_prix.keys())
    app.search_prestation_var = ctk.StringVar(value="Toutes")
    app.search_prestation_menu = ctk.CTkOptionMenu(filter_card, variable=app.search_prestation_var, values=prestations)
    app.search_prestation_menu.pack(fill="x", padx=15, pady=(0, 15))

    # Statut
    ctk.CTkLabel(filter_card, text="Statut", font=app.font_bold).pack(anchor="w", padx=15, pady=(5, 5))
    app.search_status_var = ctk.StringVar(value="Tous")
    app.search_status_segmented = ctk.CTkSegmentedButton(filter_card, values=["Tous", "Payées", "Impayées", "Non-lieu"], variable=app.search_status_var)
    app.search_status_segmented.pack(fill="x", padx=15, pady=(0, 20))

    # --- Filtres Rapides ---
    ctk.CTkLabel(filter_card, text="Filtres Rapides", font=app.font_bold).pack(anchor="w", padx=15, pady=(5, 5))
    ctk.CTkButton(filter_card, text="📅 Aujourd'hui", command=app._filter_today, height=35, fg_color="#546E7A", hover_color="#455A64").pack(fill="x", padx=15, pady=(0, 20))

    # --- Carte Recherche Nom ---
    search_card = ctk.CTkFrame(sidebar, corner_radius=15, fg_color=("white", "gray20"))
    search_card.pack(fill="x", padx=20, pady=(0, 20))

    # Recherche par nom
    ctk.CTkLabel(search_card, text="Recherche par nom", font=app.font_bold).pack(anchor="w", padx=15, pady=(15, 5))
    app.search_entry = ctk.CTkEntry(search_card, placeholder_text="Nom ou prénom...", height=35)
    app.search_entry.pack(fill="x", padx=15, pady=(0, 15))
    app.search_entry.bind("<Return>", lambda event: app._apply_filters_and_search())

    # Boutons d'action
    app.search_button = ctk.CTkButton(search_card, text="Rechercher", command=app._apply_filters_and_search, font=app.font_button, height=40)
    app.search_button.pack(fill="x", padx=15, pady=(0, 5))
    
    app.reset_button = ctk.CTkButton(search_card, text="Réinitialiser", command=app._reset_filters, fg_color="gray50", hover_color="gray30", font=app.font_button, height=30)
    app.reset_button.pack(fill="x", padx=15, pady=(0, 15))

    # Bouton Export (Sidebar)
    app.export_button = ctk.CTkButton(sidebar, text="Exporter en Excel", command=app._export_search_results, fg_color="#34D399", hover_color="#10B981", font=app.font_button, height=40)
    app.export_button.pack(fill="x", padx=20, pady=(0, 20))

    # =================================================================================
    # 2. CONTENU PRINCIPAL (DROITE) - Résultats
    # =================================================================================
    main_content = ctk.CTkFrame(app.search_tab, corner_radius=0, fg_color="transparent")
    main_content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
    main_content.grid_columnconfigure(0, weight=1)
    main_content.grid_rowconfigure(1, weight=1)

    ctk.CTkLabel(main_content, text="Résultats de la recherche", font=app.font_title, text_color="#3498db").grid(row=0, column=0, sticky="w", pady=(0, 15))

    # --- Cadre des résultats ---
    app.results_frame = ctk.CTkScrollableFrame(main_content, label_text="", corner_radius=15, fg_color=("white", "gray20"))
    app.results_frame.grid(row=1, column=0, sticky="nsew")

    # --- Pagination ---
    app.pagination_frame = ctk.CTkFrame(main_content, fg_color="transparent", height=50)
    app.pagination_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
    app.pagination_frame.grid_columnconfigure((0, 4), weight=1)

    app.btn_prev_page = ctk.CTkButton(app.pagination_frame, text="◀", width=40, command=app._prev_page, state="disabled", height=30, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))
    app.btn_prev_page.grid(row=0, column=1, padx=5)

    app.lbl_page_info = ctk.CTkLabel(app.pagination_frame, text="Page 1 / 1", font=app.font_bold)
    app.lbl_page_info.grid(row=0, column=2, padx=10)

    app.btn_next_page = ctk.CTkButton(app.pagination_frame, text="▶", width=40, command=app._next_page, state="disabled", height=30, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))
    app.btn_next_page.grid(row=0, column=3, padx=5)