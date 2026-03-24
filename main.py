# main.py
# This is the main entry point for the application, especially for PyInstaller.

# By running the app from this top-level script, Python can correctly
# resolve the package structure and the relative imports within the 'scripts' folder.

import os
import traceback
from datetime import datetime
from tkinter import messagebox
import customtkinter as ctk
from opeyrateur_app.ui.main_window import App
from opeyrateur_app.core import settings_manager
from opeyrateur_app.utils.utils import resource_path

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Intercepte toutes les exceptions non gérées issues de Tkinter."""
    
    # Ignore un bug inoffensif et connu de CustomTkinter sur la destruction de fenêtres
    err_msg = str(exc_value).lower()
    if "bad window path name" in err_msg and (".!ctktoplevel" in err_msg or "toplevel" in err_msg):
        return
        
    log_dir = os.path.join(os.path.expanduser("~"), "Documents", "Opeyrateur_Logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"crash_log_{datetime.now().strftime('%Y%m%d')}.txt")
    
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n--- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        f.write(error_msg)
        
    print(error_msg) # Toujours afficher dans la console si présente
    
    messagebox.showerror(
        "Erreur Inattendue",
        "Une erreur inattendue s'est produite lors d'une action.\nL'application va tenter de s'en remettre, "
        "mais il est conseillé de la redémarrer si le problème persiste.\n\n"
        f"Détails enregistrés dans :\n{log_file}\n\nErreur :\n{exc_value}"
    )

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
    app.report_callback_exception = global_exception_handler
    
    # Effectue une sauvegarde journalière au lancement
    from opeyrateur_app.core import data_manager
    try:
        data_manager.backup_database()
    except Exception as e:
        print(f"Erreur lors de la sauvegarde initiale : {e}")
        
    app.mainloop()