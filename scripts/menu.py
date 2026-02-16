import customtkinter as ctk
import os
from PIL import Image
from .utils import resource_path

def create_menu(app):
    """Construit l'interface du menu principal."""
    app.menu_frame.grid_columnconfigure(0, weight=1)
    app.menu_frame.grid_rowconfigure((0, 9), weight=1) # Espacement vertical

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
    title_label.grid(row=2, column=0, pady=(10, 30))

    # Boutons
    btn_width = 300
    btn_height = 50
    
    # Note : On utilise des lambdas pour appeler la méthode _show_tool de l'application
    ctk.CTkButton(app.menu_frame, text="Nouvelle Facture", font=app.font_button, width=btn_width, height=btn_height, command=lambda: app._show_tool(app.new_invoice_wrapper)).grid(row=3, column=0, pady=10)
    ctk.CTkButton(app.menu_frame, text="Rechercher", font=app.font_button, width=btn_width, height=btn_height, command=lambda: app._show_tool(app.search_wrapper)).grid(row=4, column=0, pady=10)
    ctk.CTkButton(app.menu_frame, text="Budget", font=app.font_button, width=btn_width, height=btn_height, command=lambda: app._show_tool(app.budget_wrapper)).grid(row=5, column=0, pady=10)
    ctk.CTkButton(app.menu_frame, text="Frais", font=app.font_button, width=btn_width, height=btn_height, command=lambda: app._show_tool(app.expenses_wrapper)).grid(row=6, column=0, pady=10)
    ctk.CTkButton(app.menu_frame, text="Attestation", font=app.font_button, width=btn_width, height=btn_height, command=lambda: app._show_tool(app.attestation_wrapper)).grid(row=7, column=0, pady=10)
    
    ctk.CTkButton(app.menu_frame, text="Quitter", font=app.font_button, width=btn_width, height=btn_height, fg_color="#D32F2F", hover_color="#B71C1C", command=app.destroy).grid(row=8, column=0, pady=(30, 20))

    ctk.CTkButton(app.menu_frame, text="⚙️", font=ctk.CTkFont(family="Montserrat", size=24), width=50, height=50, command=app._open_settings_window, fg_color="transparent", text_color=("#1E1E1E", "#E0E0E0")).grid(row=9, column=0, sticky="se", padx=20, pady=20)