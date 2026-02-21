import customtkinter as ctk
import os
from PIL import Image
from .utils import resource_path

def create_menu(app):
    """Construit l'interface du menu principal."""
    # Configuration de la grille principale : Sidebar (fixe) + Contenu (extensible)
    app.menu_frame.grid_columnconfigure(0, weight=0, minsize=280) # Sidebar
    app.menu_frame.grid_columnconfigure(1, weight=1) # Dashboard
    app.menu_frame.grid_rowconfigure(0, weight=1)

    # =================================================================================
    # 1. SIDEBAR DE NAVIGATION (GAUCHE)
    # =================================================================================
    sidebar = ctk.CTkFrame(app.menu_frame, corner_radius=0, fg_color=("gray90", "gray16"))
    sidebar.grid(row=0, column=0, sticky="nsew")
    sidebar.grid_columnconfigure(0, weight=1)
    sidebar.grid_rowconfigure(10, weight=1) # Spacer pour pousser les réglages en bas

    # --- Logo & Titre ---
    logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
    logo_frame.grid(row=0, column=0, pady=(30, 20), sticky="ew")
    
    try:
        logo_path = resource_path(os.path.join("src", "logo.png"))
        if os.path.exists(logo_path):
            pil_image = Image.open(logo_path)
            my_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(100, 100))
            ctk.CTkLabel(logo_frame, image=my_image, text="").pack()
    except Exception as e:
        print(f"Erreur chargement logo menu: {e}")

    ctk.CTkLabel(logo_frame, text="L'Opeyrateur", font=ctk.CTkFont(family="Montserrat", size=24, weight="bold")).pack(pady=(10, 0))
    ctk.CTkLabel(logo_frame, text="Gestion de cabinet", font=ctk.CTkFont(family="Montserrat", size=12), text_color="gray").pack()

    # --- Menu de Navigation ---
    nav_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
    nav_frame.grid(row=1, column=0, sticky="ew", padx=20)
    
    # Style des boutons du menu
    btn_params = {
        "font": ctk.CTkFont(family="Montserrat", size=14, weight="bold"),
        "fg_color": "transparent",
        "text_color": ("gray20", "gray90"),
        "hover_color": ("gray80", "gray25"),
        "anchor": "w",
        "height": 45,
        "corner_radius": 8
    }

    ctk.CTkButton(nav_frame, text="📝  Nouvelle Facture", command=lambda: app._show_tool(app.new_invoice_wrapper), **btn_params).pack(fill="x", pady=2)
    ctk.CTkButton(nav_frame, text="🔍  Rechercher", command=lambda: app._show_tool(app.search_wrapper), **btn_params).pack(fill="x", pady=2)
    ctk.CTkButton(nav_frame, text="💰  Budget & Analyse", command=lambda: app._show_tool(app.budget_wrapper), **btn_params).pack(fill="x", pady=2)
    ctk.CTkButton(nav_frame, text="💸  Gestion des Frais", command=lambda: app._show_tool(app.expenses_wrapper), **btn_params).pack(fill="x", pady=2)
    ctk.CTkButton(nav_frame, text="📄  Attestation", command=lambda: app._show_tool(app.attestation_wrapper), **btn_params).pack(fill="x", pady=2)

    # --- Bas de Sidebar (Réglages & Quitter) ---
    bottom_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
    bottom_frame.grid(row=11, column=0, sticky="ew", padx=20, pady=20)
    
    ctk.CTkButton(bottom_frame, text="⚙️  Réglages", command=app._open_settings_window, **btn_params).pack(fill="x", pady=2)
    
    quit_btn_params = btn_params.copy()
    quit_btn_params.update({"fg_color": ("#ffebee", "#3e2723"), "text_color": "#e74c3c", "hover_color": ("#ffcdd2", "#5d4037")})
    ctk.CTkButton(bottom_frame, text="🚪  Quitter", command=app.on_closing, **quit_btn_params).pack(fill="x", pady=(10, 0))

    # =================================================================================
    # 2. TABLEAU DE BORD (DROITE)
    # =================================================================================
    content = ctk.CTkScrollableFrame(app.menu_frame, corner_radius=0, fg_color="transparent")
    content.grid(row=0, column=1, sticky="nsew", padx=40, pady=40)
    content.grid_columnconfigure((0, 1), weight=1)

    # Titre Dashboard
    ctk.CTkLabel(content, text="Tableau de Bord", font=ctk.CTkFont(family="Montserrat", size=28, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))

    # --- Fonctions KPI ---
    def on_kpi_enter(event, frame):
        frame.configure(border_color="gray70")

    def on_kpi_leave(event, frame):
        frame.configure(border_color=("gray90", "gray20"))

    def create_kpi_card(parent, row, col, title, value_attr, color, icon="📊", command_key=None):
        card = ctk.CTkFrame(parent, corner_radius=15, fg_color=("white", "gray20"), border_width=2, border_color=("gray90", "gray20"), cursor="hand2")
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        
        # Header (Icon + Title)
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(header, text=icon, font=ctk.CTkFont(size=20)).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(header, text=title, font=ctk.CTkFont(family="Montserrat", size=13, weight="bold"), text_color="gray").pack(side="left")
        
        # Value
        value_label = ctk.CTkLabel(card, text="...", font=ctk.CTkFont(family="Montserrat", size=28, weight="bold"), text_color=color)
        value_label.pack(padx=20, pady=(0, 15), anchor="w")
        
        # Assign to app attribute
        setattr(app, value_attr, value_label)
        
        # Bindings
        for w in [card, header, value_label] + header.winfo_children():
            w.bind("<Enter>", lambda e, f=card: on_kpi_enter(e, f))
            w.bind("<Leave>", lambda e, f=card: on_kpi_leave(e, f))
            if command_key:
                w.bind("<Button-1>", lambda e: app._on_kpi_click(command_key))
        
        return card

    # --- Grille des KPIs ---
    create_kpi_card(content, 1, 0, "CA Encaissé (Mois)", "kpi_revenue_label", "#2ecc71", "📈", "revenue_month")
    create_kpi_card(content, 1, 1, "Consultations (Mois / Année)", "kpi_sessions_label", ("gray10", "gray90"), "👥", "sessions_month")
    create_kpi_card(content, 2, 0, "Total Impayés", "kpi_unpaid_label", "#e74c3c", "⚠️", "unpaid")
    create_kpi_card(content, 2, 1, "Dépenses (Mois)", "kpi_expenses_label", "#f39c12", "📉", "expenses_month")

    # --- Section Santé Financière ---
    ctk.CTkLabel(content, text="Santé Financière", font=ctk.CTkFont(family="Montserrat", size=20, weight="bold")).grid(row=3, column=0, columnspan=2, sticky="w", pady=(30, 10))

    salary_frame = ctk.CTkFrame(content, corner_radius=15, fg_color=("white", "gray20"), border_width=2, border_color=("gray90", "gray20"))
    salary_frame.grid(row=4, column=0, columnspan=2, padx=10, sticky="ew")
    salary_frame.grid_columnconfigure(1, weight=1)
    
    # Icone & Titre
    info_box = ctk.CTkFrame(salary_frame, fg_color="transparent")
    info_box.pack(side="left", padx=20, pady=20)
    ctk.CTkLabel(info_box, text="💰", font=ctk.CTkFont(size=30)).pack()
    
    # Détails
    details_box = ctk.CTkFrame(salary_frame, fg_color="transparent")
    details_box.pack(side="left", fill="x", expand=True, padx=10, pady=20)
    
    ctk.CTkLabel(details_box, text="Salaire Net Disponible (Mensuel)", font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), text_color="gray").pack(anchor="w")
    app.kpi_salary_label = ctk.CTkLabel(details_box, text="...", font=ctk.CTkFont(family="Montserrat", size=32, weight="bold"), text_color="#3498db")
    app.kpi_salary_label.pack(anchor="w")
    app.kpi_salary_details = ctk.CTkLabel(details_box, text="...", font=ctk.CTkFont(size=12), text_color="gray")
    app.kpi_salary_details.pack(anchor="w")
    
    # Barre de progression vers l'objectif
    progress_box = ctk.CTkFrame(salary_frame, fg_color="transparent")
    progress_box.pack(side="right", padx=30, pady=20)
    
    ctk.CTkLabel(progress_box, text="Objectif : 2 000 €", font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="e", pady=(0, 5))
    app.salary_progress_bar = ctk.CTkProgressBar(progress_box, width=200, height=12, corner_radius=6)
    app.salary_progress_bar.pack()
    app.salary_progress_bar.set(0)

    # --- Graphique Évolution ---
    ctk.CTkLabel(content, text="Évolution du Chiffre d'Affaires (6 mois)", font=ctk.CTkFont(family="Montserrat", size=20, weight="bold")).grid(row=5, column=0, columnspan=2, sticky="w", pady=(30, 10))
    
    app.dashboard_chart_frame = ctk.CTkFrame(content, corner_radius=15, fg_color=("white", "gray20"), border_width=2, border_color=("gray90", "gray20"))
    app.dashboard_chart_frame.grid(row=6, column=0, columnspan=2, padx=10, sticky="ew")

    # --- Dernières Factures ---
    ctk.CTkLabel(content, text="Dernières Factures", font=ctk.CTkFont(family="Montserrat", size=20, weight="bold")).grid(row=7, column=0, columnspan=2, sticky="w", pady=(30, 10))
    
    app.dashboard_recent_invoices_frame = ctk.CTkFrame(content, corner_radius=15, fg_color=("white", "gray20"), border_width=2, border_color=("gray90", "gray20"))
    app.dashboard_recent_invoices_frame.grid(row=8, column=0, columnspan=2, padx=10, sticky="ew")