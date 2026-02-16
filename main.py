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
    theme_path = resource_path(os.path.join("src", "themes", "doctolib.json"))
    if os.path.exists(theme_path):
        ctk.set_default_color_theme(theme_path)
    else:
        # Fallback to default blue theme if custom theme is not found
        print("Avertissement : Fichier de thème 'doctolib.json' introuvable. Utilisation du thème 'blue' par défaut.")
        ctk.set_default_color_theme("blue")

    ctk.set_appearance_mode("System")
    app = App()
    app.mainloop()