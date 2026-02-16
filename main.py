# main.py
# This is the main entry point for the application, especially for PyInstaller.

# By running the app from this top-level script, Python can correctly
# resolve the package structure and the relative imports within the 'scripts' folder.

import os
import customtkinter as ctk
from scripts.app import App
from scripts import settings_manager
from scripts.utils import resource_path

if __name__ == "__main__":
    # Applique le thème et le mode d'apparence avant de créer la fenêtre principale
    theme_name = settings_manager.get_appearance_theme()

    # Liste des thèmes personnalisés
    custom_themes = ["red", "yellow", "black"]

    if theme_name in custom_themes:
        # Construit le chemin vers le fichier JSON du thème personnalisé
        theme_path = resource_path(os.path.join("src", "themes", f"{theme_name}.json"))
        if os.path.exists(theme_path):
            ctk.set_default_color_theme(theme_path)
        else:
            print(f"Avertissement : Fichier de thème '{theme_name}.json' introuvable. Utilisation du thème 'blue'.")
            ctk.set_default_color_theme("blue")
    else:
        ctk.set_default_color_theme(theme_name)

    ctk.set_appearance_mode("System")
    app = App()
    app.mainloop()