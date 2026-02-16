import sys
import os
import customtkinter as ctk

def resource_path(relative_path):
    """
    Récupère le chemin absolu d'une ressource, pour le développement et pour PyInstaller.
    """
    try:
        # PyInstaller crée un dossier temporaire et stocke son chemin dans _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # En mode développement, la base est la racine du projet (le parent de 'scripts')
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    return os.path.join(base_path, relative_path)

class ToolTip:
    """Classe pour afficher une infobulle au survol d'un widget."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window: return
        x = self.widget.winfo_rootx() + (self.widget.winfo_width() // 2)
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tooltip_window = ctk.CTkToplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.geometry(f"+{x}+{y}")
        label = ctk.CTkLabel(self.tooltip_window, text=self.text, fg_color="#2B2B2B", text_color="#FFFFFF", corner_radius=6, height=25)
        label.pack(padx=8, pady=4)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None