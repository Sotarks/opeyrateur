import customtkinter as ctk
import os
from PIL import Image
from .utils import resource_path
from .utils import ToolTip

def create_menu(app):
    """Construit l'interface du menu principal."""
    # Configure la grille principale pour centrer le contenu
    app.menu_frame.grid_columnconfigure(0, weight=1)
    app.menu_frame.grid_rowconfigure(1, weight=1)

    # --- Cadre pour le logo et le titre en haut ---
    header_frame = ctk.CTkFrame(app.menu_frame, fg_color="transparent")
    header_frame.grid(row=0, column=0, pady=(20, 10), sticky="ew")
    header_frame.grid_columnconfigure(0, weight=1)

    try:
        logo_path = resource_path(os.path.join("src", "logo.png"))
        if os.path.exists(logo_path):
            # Charge l'image avec PIL et crée un CTkImage pour une meilleure qualité
            pil_image = Image.open(logo_path)
            my_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(150, 150))
            logo_label = ctk.CTkLabel(header_frame, image=my_image, text="")
            logo_label.pack()
    except Exception as e:
        print(f"Erreur chargement logo menu: {e}")

    title_label = ctk.CTkLabel(header_frame, text="L'Opeyrateur", font=app.font_title)
    title_label.pack(pady=(10, 10))

    # --- Cadre principal pour centrer les deux colonnes ---
    center_frame = ctk.CTkFrame(app.menu_frame, fg_color="transparent")
    center_frame.grid(row=1, column=0, sticky="") # sticky="" dans une cellule qui s'étend va centrer le widget

    # --- Colonne de gauche pour les boutons ---
    buttons_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
    buttons_frame.grid(row=0, column=0, sticky="n", padx=(20, 10), pady=20)

    # --- Colonne de droite pour le tableau de bord (KPIs) ---
    dashboard_frame = ctk.CTkFrame(center_frame, corner_radius=10)
    dashboard_frame.grid(row=0, column=1, sticky="n", padx=(10, 20), pady=10)
    # Les colonnes et lignes du dashboard ne doivent pas s'étirer
    dashboard_frame.grid_columnconfigure((0, 1), weight=0)
    dashboard_frame.grid_rowconfigure((0, 1), weight=0)

    # --- Fonctions pour l'effet de survol et le clic ---
    def on_kpi_enter(event, frame):
        frame.configure(fg_color=("gray85", "gray25"))

    def on_kpi_leave(event, frame):
        # Utilise la couleur par défaut du thème pour les CTkFrame
        frame.configure(fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"])

    # KPI 1: CA ce mois-ci
    kpi1_frame = ctk.CTkFrame(dashboard_frame, corner_radius=10, cursor="hand2", width=220, height=100)
    kpi1_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
    kpi1_frame.grid_columnconfigure(0, weight=1)
    kpi1_title = ctk.CTkLabel(kpi1_frame, text="CA (encaissé) ce mois-ci", font=app.font_regular, text_color="gray")
    kpi1_title.pack(pady=(10, 0), expand=True)
    app.kpi_revenue_label = ctk.CTkLabel(kpi1_frame, text="...", font=ctk.CTkFont(size=22, weight="bold"), text_color="#2ecc71")
    app.kpi_revenue_label.pack(pady=(0, 10), expand=True)
    for widget in [kpi1_frame, kpi1_title, app.kpi_revenue_label]:
        widget.bind("<Enter>", lambda e, f=kpi1_frame: on_kpi_enter(e, f))
        widget.bind("<Leave>", lambda e, f=kpi1_frame: on_kpi_leave(e, f))
        widget.bind("<Button-1>", lambda e: app._on_kpi_click("revenue_month"))

    # KPI 2: Consultations ce mois-ci
    kpi2_frame = ctk.CTkFrame(dashboard_frame, corner_radius=10, cursor="hand2", width=220, height=100)
    kpi2_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
    kpi2_frame.grid_columnconfigure(0, weight=1)
    kpi2_title = ctk.CTkLabel(kpi2_frame, text="Consultations ce mois-ci", font=app.font_regular, text_color="gray")
    kpi2_title.pack(pady=(10, 0), expand=True)
    app.kpi_sessions_label = ctk.CTkLabel(kpi2_frame, text="...", font=ctk.CTkFont(size=22, weight="bold"))
    app.kpi_sessions_label.pack(pady=(0, 10), expand=True)
    for widget in [kpi2_frame, kpi2_title, app.kpi_sessions_label]:
        widget.bind("<Enter>", lambda e, f=kpi2_frame: on_kpi_enter(e, f))
        widget.bind("<Leave>", lambda e, f=kpi2_frame: on_kpi_leave(e, f))
        widget.bind("<Button-1>", lambda e: app._on_kpi_click("sessions_month"))

    # KPI 3: Total Impayés
    kpi3_frame = ctk.CTkFrame(dashboard_frame, corner_radius=10, cursor="hand2", width=220, height=100)
    kpi3_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
    kpi3_frame.grid_columnconfigure(0, weight=1)
    kpi3_title = ctk.CTkLabel(kpi3_frame, text="Total des impayés", font=app.font_regular, text_color="gray")
    kpi3_title.pack(pady=(10, 0), expand=True)
    app.kpi_unpaid_label = ctk.CTkLabel(kpi3_frame, text="...", font=ctk.CTkFont(size=22, weight="bold"), text_color="#e74c3c")
    app.kpi_unpaid_label.pack(pady=(0, 10), expand=True)
    for widget in [kpi3_frame, kpi3_title, app.kpi_unpaid_label]:
        widget.bind("<Enter>", lambda e, f=kpi3_frame: on_kpi_enter(e, f))
        widget.bind("<Leave>", lambda e, f=kpi3_frame: on_kpi_leave(e, f))
        widget.bind("<Button-1>", lambda e: app._on_kpi_click("unpaid"))

    # KPI 4: Dépenses ce mois-ci
    kpi4_frame = ctk.CTkFrame(dashboard_frame, corner_radius=10, cursor="hand2", width=220, height=100)
    kpi4_frame.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
    kpi4_frame.grid_columnconfigure(0, weight=1)
    kpi4_title = ctk.CTkLabel(kpi4_frame, text="Dépenses ce mois-ci", font=app.font_regular, text_color="gray")
    kpi4_title.pack(pady=(10, 0), expand=True)
    app.kpi_expenses_label = ctk.CTkLabel(kpi4_frame, text="...", font=ctk.CTkFont(size=22, weight="bold"), text_color="#f39c12")
    app.kpi_expenses_label.pack(pady=(0, 10), expand=True)
    for widget in [kpi4_frame, kpi4_title, app.kpi_expenses_label]:
        widget.bind("<Enter>", lambda e, f=kpi4_frame: on_kpi_enter(e, f))
        widget.bind("<Leave>", lambda e, f=kpi4_frame: on_kpi_leave(e, f))
        widget.bind("<Button-1>", lambda e: app._on_kpi_click("expenses_month"))

    # --- Section Salaire / Répartition (Nouveau) ---
    salary_frame = ctk.CTkFrame(dashboard_frame, corner_radius=10)
    salary_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
    
    ctk.CTkLabel(salary_frame, text="Salaire Net Disponible (Mensuel)", font=app.font_bold, text_color="gray").pack(pady=(10, 0))
    app.kpi_salary_label = ctk.CTkLabel(salary_frame, text="...", font=ctk.CTkFont(size=24, weight="bold"), text_color="#3498db")
    app.kpi_salary_label.pack(pady=(0, 5))
    
    app.kpi_salary_details = ctk.CTkLabel(salary_frame, text="...", font=ctk.CTkFont(size=11), text_color="gray")
    app.kpi_salary_details.pack(pady=(0, 10))
    
    # Barre de progression vers l'objectif
    app.salary_progress_bar = ctk.CTkProgressBar(salary_frame, width=250, height=12, corner_radius=6)
    app.salary_progress_bar.pack(pady=(0, 5))
    app.salary_progress_bar.set(0)
    
    ctk.CTkLabel(salary_frame, text="Objectif : 2 000 € / mois", font=ctk.CTkFont(size=10), text_color="gray").pack(pady=(0, 10))
    
    ToolTip(salary_frame, "Calcul basé sur la règle des 3 tiers pour le mois en cours :\n1/3 Charges, 1/3 Frais, 1/3 Salaire.\nLe montant affiché est ce qu'il reste après déduction\ndes frais réels du mois et des provisions nécessaires.")

    # Boutons
    btn_width = 300
    btn_height = 50

    ctk.CTkButton(buttons_frame, text="Nouvelle Facture", font=app.font_button, width=btn_width, height=btn_height, command=lambda: app._show_tool(app.new_invoice_wrapper)).pack(pady=5, fill="x")
    ctk.CTkButton(buttons_frame, text="Rechercher", font=app.font_button, width=btn_width, height=btn_height, command=lambda: app._show_tool(app.search_wrapper)).pack(pady=5, fill="x")
    ctk.CTkButton(buttons_frame, text="Budget", font=app.font_button, width=btn_width, height=btn_height, command=lambda: app._show_tool(app.budget_wrapper)).pack(pady=5, fill="x")
    ctk.CTkButton(buttons_frame, text="Frais", font=app.font_button, width=btn_width, height=btn_height, command=lambda: app._show_tool(app.expenses_wrapper)).pack(pady=5, fill="x")
    ctk.CTkButton(buttons_frame, text="Attestation", font=app.font_button, width=btn_width, height=btn_height, command=lambda: app._show_tool(app.attestation_wrapper)).pack(pady=5, fill="x")
    ctk.CTkButton(buttons_frame, text="Quitter", font=app.font_button, width=btn_width, height=btn_height, fg_color="#D32F2F", hover_color="#B71C1C", command=app.destroy).pack(pady=(20, 0), fill="x")

    # Bouton des paramètres en bas à droite de la fenêtre
    ctk.CTkButton(center_frame, text="⚙️", font=ctk.CTkFont(family="Montserrat", size=24), width=50, height=50, command=app._open_settings_window, fg_color="transparent", text_color=("#1E1E1E", "#E0E0E0")).grid(row=1, column=1, sticky="se", padx=20, pady=20)