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
        # Utilisation de add="+" pour ne pas écraser les événements existants (ex: hover effects)
        self.widget.bind("<Enter>", self.show_tooltip, add="+")
        self.widget.bind("<Leave>", self.hide_tooltip, add="+")
        self.widget.bind("<ButtonPress>", self.hide_tooltip, add="+")

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
            window_to_destroy = self.tooltip_window
            self.tooltip_window = None
            try:
                # Add a tiny delay to ensure CustomTkinter internal events (like titlebar color setting) finish first
                self.widget.after(50, lambda: window_to_destroy.destroy() if window_to_destroy.winfo_exists() else None)
            except Exception:
                pass

def validate_fec_content(lines):
    """Vérifie la conformité des lignes FEC (18 colonnes, dates, équilibre)."""
    errors = []
    if not lines:
        return False, ["Le fichier est vide."]

    header = lines[0].split('|')
    if len(header) != 18:
        errors.append(f"En-tête invalide : {len(header)} colonnes (attendu : 18).")

    ecritures = {} # EcritureNum -> balance

    for i, line in enumerate(lines[1:], start=2):
        cols = line.split('|')
        if len(cols) != 18:
            errors.append(f"Ligne {i} : {len(cols)} colonnes (attendu : 18).")
            continue
        
        # Vérification Date (YYYYMMDD)
        date_ecr = cols[3]
        if len(date_ecr) != 8 or not date_ecr.isdigit():
            errors.append(f"Ligne {i} : Date incorrecte '{date_ecr}' (attendu YYYYMMDD).")
            
        # Vérification Montants (Virgule obligatoire pour FEC France)
        debit, credit = cols[11], cols[12]
        if '.' in debit or '.' in credit:
            errors.append(f"Ligne {i} : Montant invalide (point détecté). Utilisez une virgule (ex: 12,50).")

    if errors:
        return False, errors
    return True, []

class FECPreviewWindow(ctk.CTkToplevel):
    """Fenêtre de prévisualisation du contenu FEC avant enregistrement."""
    def __init__(self, parent, lines, save_command):
        super().__init__(parent)
        self.title("Prévisualisation FEC")
        self.geometry("1100x600")
        self.transient(parent)
        self.grab_set()
        
        ctk.CTkLabel(self, text="Aperçu du fichier FEC", font=("Montserrat", 16, "bold")).pack(pady=(15, 5))
        ctk.CTkLabel(self, text="Vérifiez le contenu avant l'enregistrement.", text_color="gray").pack(pady=(0, 10))

        self.textbox = ctk.CTkTextbox(self, font=("Courier New", 12), wrap="none")
        self.textbox.pack(fill="both", expand=True, padx=20, pady=10)
        self.textbox.insert("1.0", "\n".join(lines))
        self.textbox.configure(state="disabled")
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(btn_frame, text="Enregistrer le fichier", command=self.save_and_close, fg_color="#2ecc71", hover_color="#27ae60", height=40).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Annuler", command=self.destroy, fg_color="gray50", hover_color="gray30", height=40).pack(side="right", padx=5)
        
    def save_and_close(self):
        self.destroy()
        self.save_command()