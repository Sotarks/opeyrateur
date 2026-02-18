import customtkinter as ctk

def create_search_tab(app):
    """Crée les widgets pour l'onglet 'Rechercher' et les attache à l'instance de l'application."""
    app.search_tab.grid_columnconfigure(0, weight=1)
    app.search_tab.grid_rowconfigure(2, weight=1) # Ligne pour les résultats

    # --- Cadre de recherche et actions ---
    controls_frame = ctk.CTkFrame(app.search_tab, corner_radius=10)
    controls_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
    controls_frame.grid_columnconfigure((1, 3), weight=1)

    ctk.CTkLabel(controls_frame, text="Filtres & Recherche", font=app.font_large).grid(row=0, column=0, columnspan=4, pady=(10,5), padx=10, sticky="w")

    from .data_manager import get_available_years, MONTHS_FR

    # Période
    ctk.CTkLabel(controls_frame, text="Année :").grid(row=1, column=0, padx=(10, 0), pady=5, sticky="w")
    years = ["Toutes"] + get_available_years()
    app.search_year_var = ctk.StringVar(value=years[0])
    app.search_year_menu = ctk.CTkOptionMenu(controls_frame, variable=app.search_year_var, values=years, command=app._on_search_year_change)
    app.search_year_menu.grid(row=1, column=1, padx=(0, 10), pady=5, sticky="ew")

    ctk.CTkLabel(controls_frame, text="Mois :").grid(row=1, column=2, padx=(10, 0), pady=5, sticky="w")
    months = ["Tous"] + MONTHS_FR
    app.search_month_var = ctk.StringVar(value="Tous")
    app.search_month_menu = ctk.CTkOptionMenu(controls_frame, variable=app.search_month_var, values=months)
    app.search_month_menu.grid(row=1, column=3, padx=(0, 10), pady=5, sticky="ew")
    app.search_month_menu.configure(state="disabled")

    # Type de séance
    ctk.CTkLabel(controls_frame, text="Type de séance :").grid(row=2, column=0, padx=(10,0), pady=5, sticky="w")
    prestations = ["Toutes"] + list(app.prestations_prix.keys())
    app.search_prestation_var = ctk.StringVar(value="Toutes")
    app.search_prestation_menu = ctk.CTkOptionMenu(controls_frame, variable=app.search_prestation_var, values=prestations)
    app.search_prestation_menu.grid(row=2, column=1, columnspan=3, padx=10, pady=5, sticky="ew")

    # Statut
    ctk.CTkLabel(controls_frame, text="Statut :").grid(row=3, column=0, padx=(10,0), pady=5, sticky="w")
    app.search_status_var = ctk.StringVar(value="Tous")
    app.search_status_segmented = ctk.CTkSegmentedButton(controls_frame, values=["Tous", "Payées", "Impayées", "Non-lieu"], variable=app.search_status_var)
    app.search_status_segmented.grid(row=3, column=1, columnspan=3, padx=10, pady=5, sticky="ew")

    # Recherche par nom
    ctk.CTkLabel(controls_frame, text="Recherche par nom :").grid(row=4, column=0, columnspan=4, padx=(10,0), pady=(10,0), sticky="w")
    app.search_entry = ctk.CTkEntry(controls_frame, placeholder_text="Entrez un nom ou prénom...")
    app.search_entry.grid(row=5, column=0, columnspan=4, padx=10, pady=(0, 10), sticky="ew")
    app.search_entry.bind("<Return>", lambda event: app._apply_filters_and_search())

    # Boutons d'action
    action_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
    action_frame.grid(row=6, column=0, columnspan=4, padx=10, pady=10, sticky="ew")
    action_frame.grid_columnconfigure((0,1), weight=1)

    app.search_button = ctk.CTkButton(action_frame, text="Appliquer les filtres", command=app._apply_filters_and_search, font=app.font_button)
    app.search_button.grid(row=0, column=0, padx=(0,5), sticky="ew")
    
    app.reset_button = ctk.CTkButton(action_frame, text="Réinitialiser", command=app._reset_filters, fg_color="gray50", font=app.font_button)
    app.reset_button.grid(row=0, column=1, padx=(5,0), sticky="ew")

    app.export_button = ctk.CTkButton(controls_frame, text="Exporter les résultats en Excel", command=app._export_search_results, fg_color="#34D399", hover_color="#10B981", font=app.font_button)
    app.export_button.grid(row=7, column=0, columnspan=4, padx=10, pady=(5,10), sticky="ew")

    # --- Cadre des résultats ---
    app.results_frame = ctk.CTkScrollableFrame(app.search_tab, label_text="Résultats", label_font=ctk.CTkFont(size=14, weight="bold"), corner_radius=10)
    app.results_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")