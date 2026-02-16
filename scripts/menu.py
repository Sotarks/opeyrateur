import customtkinter as ctk
import os
from PIL import Image
from .utils import resource_path, ToolTip

def create_menu(app):
    """Construit l'interface du menu principal."""
    app.menu_frame.grid_columnconfigure(0, weight=1)
    app.menu_frame.grid_rowconfigure((0, 12), weight=1) # Espacement vertical
    app.menu_frame.grid_rowconfigure(4, weight=1) # Ligne pour le graphique

    # --- Logo ---
    try:
        logo_path = resource_path(os.path.join("src", "logo.png"))
        if os.path.exists(logo_path):
            # Charge l'image avec PIL et crée un CTkImage pour une meilleure qualité
            pil_image = Image.open(logo_path)
            my_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(150, 150))
            
            logo_label = ctk.CTkLabel(app.menu_frame, image=my_image, text="")
            logo_label.grid(row=1, column=0, pady=(20, 10))
    except Exception as e:
        print(f"Erreur chargement logo menu: {e}")

    # Titre
    title_label = ctk.CTkLabel(app.menu_frame, text="L'Opeyrateur", font=app.font_title)
    title_label.grid(row=2, column=0, pady=(10, 20))

    # --- Tableau de Bord (Dashboard) ---
    dashboard_frame = ctk.CTkFrame(app.menu_frame, fg_color="transparent")
    dashboard_frame.grid(row=3, column=0, pady=(0, 15), padx=20, sticky="ew")
    dashboard_frame.grid_columnconfigure((0, 1), weight=1)

    # --- Fonctions pour l'effet de survol et le clic ---
    def on_kpi_enter(event, frame):
        frame.configure(fg_color=("gray85", "gray25"))
    
    def on_kpi_leave(event, frame):
        # Utilise la couleur par défaut du thème pour les CTkFrame
        frame.configure(fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"])

    # KPI 1: CA ce mois-ci
    kpi1_frame = ctk.CTkFrame(dashboard_frame, corner_radius=10, cursor="hand2")
    kpi1_frame.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="nsew")
    kpi1_frame.grid_columnconfigure(0, weight=1)
    kpi1_title = ctk.CTkLabel(kpi1_frame, text="CA (encaissé) ce mois-ci", font=app.font_regular, text_color="gray")
    kpi1_title.pack(pady=(10, 0))
    app.kpi_revenue_label = ctk.CTkLabel(kpi1_frame, text="...", font=ctk.CTkFont(size=22, weight="bold"), text_color="#2ecc71")
    app.kpi_revenue_label.pack(pady=(0, 10))
    for widget in [kpi1_frame, kpi1_title, app.kpi_revenue_label]:
        widget.bind("<Enter>", lambda e, f=kpi1_frame: on_kpi_enter(e, f))
        widget.bind("<Leave>", lambda e, f=kpi1_frame: on_kpi_leave(e, f))
        widget.bind("<Button-1>", lambda e: app._on_kpi_click("revenue_month"))

    # KPI 2: Consultations ce mois-ci
    kpi2_frame = ctk.CTkFrame(dashboard_frame, corner_radius=10, cursor="hand2")
    kpi2_frame.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="nsew")
    kpi2_frame.grid_columnconfigure(0, weight=1)
    kpi2_title = ctk.CTkLabel(kpi2_frame, text="Consultations ce mois-ci", font=app.font_regular, text_color="gray")
    kpi2_title.pack(pady=(10, 0))
    app.kpi_sessions_label = ctk.CTkLabel(kpi2_frame, text="...", font=ctk.CTkFont(size=22, weight="bold"))
    app.kpi_sessions_label.pack(pady=(0, 10))
    for widget in [kpi2_frame, kpi2_title, app.kpi_sessions_label]:
        widget.bind("<Enter>", lambda e, f=kpi2_frame: on_kpi_enter(e, f))
        widget.bind("<Leave>", lambda e, f=kpi2_frame: on_kpi_leave(e, f))
        widget.bind("<Button-1>", lambda e: app._on_kpi_click("sessions_month"))

    # KPI 3: Total Impayés
    kpi3_frame = ctk.CTkFrame(dashboard_frame, corner_radius=10, cursor="hand2")
    kpi3_frame.grid(row=1, column=0, padx=(0, 5), pady=5, sticky="nsew")
    kpi3_frame.grid_columnconfigure(0, weight=1)
    kpi3_title = ctk.CTkLabel(kpi3_frame, text="Total des impayés", font=app.font_regular, text_color="gray")
    kpi3_title.pack(pady=(10, 0))
    app.kpi_unpaid_label = ctk.CTkLabel(kpi3_frame, text="...", font=ctk.CTkFont(size=22, weight="bold"), text_color="#e74c3c")
    app.kpi_unpaid_label.pack(pady=(0, 10))
    for widget in [kpi3_frame, kpi3_title, app.kpi_unpaid_label]:
        widget.bind("<Enter>", lambda e, f=kpi3_frame: on_kpi_enter(e, f))
        widget.bind("<Leave>", lambda e, f=kpi3_frame: on_kpi_leave(e, f))
        widget.bind("<Button-1>", lambda e: app._on_kpi_click("unpaid"))

    # KPI 4: Dépenses ce mois-ci
    kpi4_frame = ctk.CTkFrame(dashboard_frame, corner_radius=10, cursor="hand2")
    kpi4_frame.grid(row=1, column=1, padx=(5, 0), pady=5, sticky="nsew")
    kpi4_frame.grid_columnconfigure(0, weight=1)
    kpi4_title = ctk.CTkLabel(kpi4_frame, text="Dépenses ce mois-ci", font=app.font_regular, text_color="gray")
    kpi4_title.pack(pady=(10, 0))
    app.kpi_expenses_label = ctk.CTkLabel(kpi4_frame, text="...", font=ctk.CTkFont(size=22, weight="bold"), text_color="#f39c12")
    app.kpi_expenses_label.pack(pady=(0, 10))
    for widget in [kpi4_frame, kpi4_title, app.kpi_expenses_label]:
        widget.bind("<Enter>", lambda e, f=kpi4_frame: on_kpi_enter(e, f))
        widget.bind("<Leave>", lambda e, f=kpi4_frame: on_kpi_leave(e, f))
        widget.bind("<Button-1>", lambda e: app._on_kpi_click("expenses_month"))

    # --- Cadre pour le graphique ---
    app.dashboard_chart_frame = ctk.CTkFrame(app.menu_frame, corner_radius=10)
    app.dashboard_chart_frame.grid(row=4, column=0, pady=(10, 5), padx=20, sticky="ewns")

    # Bouton d'exportation du graphique
    export_chart_btn = ctk.CTkButton(
        app.dashboard_chart_frame, 
        text="🖼️", 
        width=35, height=35, 
        font=ctk.CTkFont(size=20),
        command=app._export_dashboard_chart,
        fg_color="transparent",
        text_color=("#1E1E1E", "#E0E0E0"),
        hover_color=("gray85", "gray25")
    )
    export_chart_btn.place(relx=0.98, rely=0.02, anchor="ne")
    ToolTip(export_chart_btn, "Exporter le graphique en image")

    # Boutons
    btn_width = 300
    btn_height = 50
    
    # Note : On utilise des lambdas pour appeler la méthode _show_tool de l'application
    ctk.CTkButton(app.menu_frame, text="Nouvelle Facture", font=app.font_button, width=btn_width, height=btn_height, command=lambda: app._show_tool(app.new_invoice_wrapper)).grid(row=5, column=0, pady=5)
    ctk.CTkButton(app.menu_frame, text="Rechercher", font=app.font_button, width=btn_width, height=btn_height, command=lambda: app._show_tool(app.search_wrapper)).grid(row=6, column=0, pady=5)
    ctk.CTkButton(app.menu_frame, text="Budget", font=app.font_button, width=btn_width, height=btn_height, command=lambda: app._show_tool(app.budget_wrapper)).grid(row=7, column=0, pady=5)
    ctk.CTkButton(app.menu_frame, text="Frais", font=app.font_button, width=btn_width, height=btn_height, command=lambda: app._show_tool(app.expenses_wrapper)).grid(row=8, column=0, pady=5)
    ctk.CTkButton(app.menu_frame, text="Attestation", font=app.font_button, width=btn_width, height=btn_height, command=lambda: app._show_tool(app.attestation_wrapper)).grid(row=9, column=0, pady=5)
    
    ctk.CTkButton(app.menu_frame, text="Quitter", font=app.font_button, width=btn_width, height=btn_height, fg_color="#D32F2F", hover_color="#B71C1C", command=app.destroy).grid(row=10, column=0, pady=(20, 20))

    ctk.CTkButton(app.menu_frame, text="⚙️", font=ctk.CTkFont(family="Montserrat", size=24), width=50, height=50, command=app._open_settings_window, fg_color="transparent", text_color=("#1E1E1E", "#E0E0E0")).grid(row=11, column=0, sticky="se", padx=20, pady=20)