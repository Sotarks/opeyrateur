import customtkinter as ctk
import pandas as pd
from datetime import datetime
import os
import ast
import time
import threading
import queue 
from tkinter import messagebox, PhotoImage
import tkinter as tk
from tkcalendar import Calendar
import webbrowser
import shutil

# --- Imports des modules séparés ---
from . import config 
from . import pin_manager
from . import settings_manager
from .utils import resource_path
from .pdf_viewer import PDFViewer
from .pdf_generator import generate_pdf, generate_attestation_pdf
from .data_manager import (save_to_excel, get_invoice_path, get_yearly_invoice_count, load_all_data, load_year_data, backup_database, MONTHS_FR, delete_invoice, get_available_years)
from .new_invoice_tab import create_new_invoice_tab
from .search_tab import create_search_tab
from .budget_tab import create_budget_tab, calculate_budget
from .expenses_tab import create_expenses_tab, refresh_expenses_list
from tkinter import filedialog
from .attestation_tab import create_attestation_tab
from .menu import create_menu

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

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Opeyrateur - A. Peyrat")
        self.geometry("600x850")

        # --- Définir l'icône de la fenêtre ---
        try:
            logo_path = resource_path(os.path.join("src", "logo.png"))
            if os.path.exists(logo_path):
                self.iconphoto(False, PhotoImage(file=logo_path))
        except Exception as e:
            # Affiche une erreur dans la console si l'icône ne peut pas être chargée, mais ne bloque pas l'app
            print(f"Erreur lors du chargement de l'icône : {e}")

        self.prestations_prix = {
            "1ère consultation enfants et adolescents": 75.0,
            "Consultation de suivi enfants": 55.0,
            "Consultation de suivi adolescents": 60.0,
            "Consultation adulte": 60.0,
            "Consultation familiale": 75.0,
            "Consultation de couple": 75.0
        }

        self.family_member_entries = []
        self.expense_sort_state = ('date', False) # (column_id, is_reversed)

        # Ajout des flags pour le chargement paresseux (lazy loading)
        self.is_new_invoice_tab_initialized = False
        self.is_search_tab_initialized = False
        self.is_budget_tab_initialized = False
        self.is_expenses_tab_initialized = False
        self.is_attestation_tab_initialized = False

        # --- Caches pour la performance ---
        self.data_cache = {}
        self.regeneration_queue = queue.Queue()
        self.current_search_results_df = pd.DataFrame()

        # Assure que la configuration du PIN existe
        pin_manager.setup_pin_if_needed()

        # Assure que la configuration des PDF existe
        settings_manager.setup_default_settings()

        # --- Configuration de la grille principale ---
        self.grid_rowconfigure(0, weight=1) # Ligne pour le contenu principal
        self.grid_rowconfigure(1, weight=0) # Ligne pour la barre de statut
        self.grid_columnconfigure(0, weight=1)

        # --- Frame de Connexion (affichée au démarrage) ---
        self.login_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.login_frame.grid(row=0, column=0, sticky="nsew")
        self._create_login_screen()

        # --- Frame du Menu Principal ---
        self.menu_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        # --- Création des Wrappers pour les outils ---
        self.new_invoice_wrapper = self._create_tool_wrapper("Nouvelle Facture")
        self.new_invoice_tab = self.new_invoice_wrapper.content_frame 

        self.search_wrapper = self._create_tool_wrapper("Rechercher")
        self.search_tab = self.search_wrapper.content_frame

        self.budget_wrapper = self._create_tool_wrapper("Budget")
        self.budget_tab = self.budget_wrapper.content_frame

        self.expenses_wrapper = self._create_tool_wrapper("Frais")
        self.expenses_tab = self.expenses_wrapper.content_frame

        self.attestation_wrapper = self._create_tool_wrapper("Attestation")
        self.attestation_tab = self.attestation_wrapper.content_frame

        # --- Construction du Menu (via script externe) ---
        create_menu(self)

        # --- Raccourci Clavier ---
        self.bind("<Escape>", lambda event: self._show_menu())

        # --- Barre de Statut ---
        self.status_bar = ctk.CTkLabel(self, text="", height=25, anchor="w")
        self.status_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))

        # --- Raccourcis Clavier contextuels ---
        self.bind("<Control-f>", self._focus_search)
        # Le bind sur le wrapper assure que le raccourci n'est actif que sur cet écran
        self.new_invoice_wrapper.bind("<Control-Return>", lambda event: self.valider())

    def _create_login_screen(self):
        """Crée l'interface de connexion par code PIN."""
        self.login_frame.grid_columnconfigure(0, weight=1)
        self.login_frame.grid_rowconfigure((0, 5), weight=1)

        ctk.CTkLabel(self.login_frame, text="Application Verrouillée", font=ctk.CTkFont(size=24, weight="bold")).grid(row=1, column=0, pady=20)
        
        self.pin_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Code PIN", show="*", width=200, justify="center", font=ctk.CTkFont(size=18))
        self.pin_entry.grid(row=2, column=0, pady=10)
        self.pin_entry.bind("<Return>", self._check_pin)
        self.pin_entry.focus()

        # --- Pad Numérique ---
        numpad_frame = ctk.CTkFrame(self.login_frame, fg_color="transparent")
        numpad_frame.grid(row=3, column=0, pady=10)

        buttons = [
            '1', '2', '3',
            '4', '5', '6',
            '7', '8', '9',
            'C', '0', '⌫'
        ]

        for i, btn_text in enumerate(buttons):
            row, col = divmod(i, 3)
            
            action = None
            if btn_text.isdigit():
                action = lambda t=btn_text: self._on_numpad_press(t)
            elif btn_text == 'C':
                action = self._on_numpad_clear
            elif btn_text == '⌫':
                action = self._on_numpad_backspace
                
            btn = ctk.CTkButton(numpad_frame, text=btn_text, width=70, height=70, font=ctk.CTkFont(size=18), command=action)
            btn.grid(row=row, column=col, padx=5, pady=5)

        ctk.CTkButton(self.login_frame, text="Déverrouiller", command=self._check_pin, width=230, height=40).grid(row=4, column=0, pady=20)

    def _check_pin(self, event=None):
        """Vérifie le code PIN saisi."""
        pin = self.pin_entry.get()
        if pin_manager.verify_pin(pin):
            self.login_frame.grid_forget()
            self.menu_frame.grid(row=0, column=0, sticky="nsew")
        else:
            self.pin_entry.delete(0, 'end')
            messagebox.showerror("Erreur", "Code PIN incorrect.")

    def _on_numpad_press(self, digit):
        """Ajoute un chiffre au champ PIN."""
        self.pin_entry.insert(ctk.END, digit)

    def _on_numpad_clear(self):
        """Efface le champ PIN."""
        self.pin_entry.delete(0, ctk.END)

    def _on_numpad_backspace(self):
        """Supprime le dernier chiffre du champ PIN."""
        current_text = self.pin_entry.get()
        self.pin_entry.delete(len(current_text) - 1, ctk.END)

    def _open_settings_window(self):
        """Ouvre la fenêtre des réglages."""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Réglages")
        settings_window.geometry("500x700")
        settings_window.transient(self)
        settings_window.grab_set()

        settings_window.grid_columnconfigure(0, weight=1)

        btn_font = ctk.CTkFont(size=14)

        ctk.CTkLabel(settings_window, text="Personnalisation", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 10))
        ctk.CTkButton(settings_window, text="Modifier les informations des PDF", font=btn_font, command=self._open_pdf_settings_window).pack(pady=10, padx=40, fill="x")
        ctk.CTkButton(settings_window, text="Changer le code PIN", font=btn_font, command=self._open_change_pin_window).pack(pady=10, padx=40, fill="x")

        theme_frame = ctk.CTkFrame(settings_window, fg_color="transparent")
        theme_frame.pack(pady=10, padx=40, fill="x")
        theme_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(theme_frame, text="Thème de l'application :").grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        themes = ["blue", "green", "dark-blue", "red", "yellow", "black"]
        current_theme = settings_manager.get_appearance_theme()
        
        theme_menu = ctk.CTkOptionMenu(theme_frame, values=themes, command=self._change_theme)
        theme_menu.set(current_theme)
        theme_menu.grid(row=0, column=1, sticky="ew")

        ctk.CTkLabel(settings_window, text="Outils de Maintenance", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 10))
        ctk.CTkLabel(settings_window, text="Ces outils permettent de corriger des problèmes de données.").pack(pady=(0, 10))
        
        ctk.CTkButton(settings_window, text="Régénérer les PDF des factures", font=btn_font, command=self._regenerate_all_invoice_pdfs, fg_color="#2980b9").pack(pady=10, padx=40, fill="x")
        ctk.CTkButton(settings_window, text="Regénérer les fichiers Excel des factures", font=btn_font, command=self._regenerate_all_invoices_excel, fg_color="#3498db").pack(pady=10, padx=40, fill="x")

        ctk.CTkLabel(settings_window, text="Zone de Danger", font=ctk.CTkFont(size=20, weight="bold"), text_color="#e74c3c").pack(pady=(20, 10))
        ctk.CTkLabel(settings_window, text="Ces actions sont irréversibles.", font=ctk.CTkFont(size=12)).pack(pady=(0, 20))

        ctk.CTkButton(settings_window, text="Supprimer TOUTES les données", font=btn_font, command=self._delete_all_data, fg_color="#992d22").pack(pady=10, padx=40, fill="x")
        ctk.CTkButton(settings_window, text="Supprimer toutes les FACTURES", font=btn_font, command=self._delete_invoices, fg_color="#c0392b").pack(pady=10, padx=40, fill="x")
        ctk.CTkButton(settings_window, text="Supprimer tous les FRAIS", font=btn_font, command=self._delete_expenses, fg_color="#c0392b").pack(pady=10, padx=40, fill="x")
        ctk.CTkButton(settings_window, text="Supprimer tous les budgets", font=btn_font, command=self._delete_budgets, fg_color="#c0392b").pack(pady=10, padx=40, fill="x")

    def _open_pdf_settings_window(self):
        """Ouvre la fenêtre de modification des informations PDF."""
        from . import settings_manager
        
        pdf_info = settings_manager.get_pdf_info()

        pdf_settings_window = ctk.CTkToplevel(self)
        pdf_settings_window.title("Réglages des informations PDF")
        pdf_settings_window.geometry("700x750")
        pdf_settings_window.transient(self)
        pdf_settings_window.grab_set()

        scrollable_frame = ctk.CTkScrollableFrame(pdf_settings_window, label_text="Informations pour les documents PDF")
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        entries = {}

        # --- Section Société ---
        ctk.CTkLabel(scrollable_frame, text="Informations Société", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5), anchor="w")
        
        ctk.CTkLabel(scrollable_frame, text="Nom de la société :").pack(anchor="w", padx=10)
        entries['company_name'] = ctk.CTkEntry(scrollable_frame)
        entries['company_name'].pack(fill="x", padx=10, pady=(0, 5))
        entries['company_name'].insert(0, pdf_info.get('company_name', ''))

        ctk.CTkLabel(scrollable_frame, text="Adresse (ligne 1) :").pack(anchor="w", padx=10)
        entries['address_line1'] = ctk.CTkEntry(scrollable_frame)
        entries['address_line1'].pack(fill="x", padx=10, pady=(0, 5))
        entries['address_line1'].insert(0, pdf_info.get('address_line1', ''))
        
        ctk.CTkLabel(scrollable_frame, text="Adresse (ligne 2 - CP Ville) :").pack(anchor="w", padx=10)
        entries['address_line2'] = ctk.CTkEntry(scrollable_frame)
        entries['address_line2'].pack(fill="x", padx=10, pady=(0, 5))
        entries['address_line2'].insert(0, pdf_info.get('address_line2', ''))

        ctk.CTkLabel(scrollable_frame, text="N° Siret :").pack(anchor="w", padx=10)
        entries['siret'] = ctk.CTkEntry(scrollable_frame)
        entries['siret'].pack(fill="x", padx=10, pady=(0, 5))
        entries['siret'].insert(0, pdf_info.get('siret', ''))

        ctk.CTkLabel(scrollable_frame, text="N° RPPS :").pack(anchor="w", padx=10)
        entries['rpps'] = ctk.CTkEntry(scrollable_frame)
        entries['rpps'].pack(fill="x", padx=10, pady=(0, 15))
        entries['rpps'].insert(0, pdf_info.get('rpps', ''))

        # --- Section Signature ---
        ctk.CTkLabel(scrollable_frame, text="Informations Signature & Contact", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5), anchor="w")
        
        ctk.CTkLabel(scrollable_frame, text="Nom complet (pour signature) :").pack(anchor="w", padx=10)
        entries['practitioner_name'] = ctk.CTkEntry(scrollable_frame)
        entries['practitioner_name'].pack(fill="x", padx=10, pady=(0, 5))
        entries['practitioner_name'].insert(0, pdf_info.get('practitioner_name', ''))
        
        ctk.CTkLabel(scrollable_frame, text="Titre / Profession :").pack(anchor="w", padx=10)
        entries['practitioner_title'] = ctk.CTkEntry(scrollable_frame)
        entries['practitioner_title'].pack(fill="x", padx=10, pady=(0, 5))
        entries['practitioner_title'].insert(0, pdf_info.get('practitioner_title', ''))

        ctk.CTkLabel(scrollable_frame, text="Numéro de téléphone :").pack(anchor="w", padx=10)
        entries['phone_number'] = ctk.CTkEntry(scrollable_frame)
        entries['phone_number'].pack(fill="x", padx=10, pady=(0, 5))
        entries['phone_number'].insert(0, pdf_info.get('phone_number', ''))

        ctk.CTkLabel(scrollable_frame, text="Email (optionnel) :").pack(anchor="w", padx=10)
        entries['email'] = ctk.CTkEntry(scrollable_frame)
        entries['email'].pack(fill="x", padx=10, pady=(0, 15))
        entries['email'].insert(0, pdf_info.get('email', ''))

        # --- Section Attestation ---
        ctk.CTkLabel(scrollable_frame, text="Informations Attestation", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5), anchor="w")
        
        ctk.CTkLabel(scrollable_frame, text="Ville pour 'Fait à...' :").pack(anchor="w", padx=10)
        entries['attestation_city'] = ctk.CTkEntry(scrollable_frame)
        entries['attestation_city'].pack(fill="x", padx=10, pady=(0, 5))
        entries['attestation_city'].insert(0, pdf_info.get('attestation_city', ''))

        ctk.CTkLabel(scrollable_frame, text="Modèle du message de l'attestation :").pack(anchor="w", padx=10)
        ctk.CTkLabel(scrollable_frame, text="Variables: {practitioner_name}, {practitioner_title}, {gender}, {patient_name}, {consultation_date}", font=ctk.CTkFont(size=10, slant="italic")).pack(anchor="w", padx=10)
        entries['attestation_message'] = ctk.CTkTextbox(scrollable_frame, height=100)
        entries['attestation_message'].pack(fill="x", expand=True, padx=10, pady=(0, 15))
        entries['attestation_message'].insert("1.0", pdf_info.get('attestation_message', ''))

        button_frame = ctk.CTkFrame(pdf_settings_window, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10)
        button_frame.grid_columnconfigure((0, 1), weight=1)

        save_button = ctk.CTkButton(button_frame, text="Enregistrer", command=lambda: self._save_pdf_settings(entries, pdf_settings_window))
        save_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        cancel_button = ctk.CTkButton(button_frame, text="Annuler", command=pdf_settings_window.destroy, fg_color="gray50")
        cancel_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def _save_pdf_settings(self, entries, window):
        """Sauvegarde les paramètres PDF modifiés."""
        from . import settings_manager

        new_data = {}
        for key, widget in entries.items():
            if isinstance(widget, ctk.CTkTextbox):
                new_data[key] = widget.get("1.0", "end-1c")
            else:
                new_data[key] = widget.get()
        
        try:
            settings_manager.save_pdf_info(new_data)
            messagebox.showinfo("Succès", "Les informations ont été enregistrées.", parent=window)
            window.destroy()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'enregistrer les informations:\n{e}", parent=window)

    def _open_change_pin_window(self):
        """Ouvre la fenêtre pour changer le code PIN."""
        pin_window = ctk.CTkToplevel(self)
        pin_window.title("Changer le code PIN")
        pin_window.geometry("400x350")
        pin_window.transient(self)
        pin_window.grab_set()

        pin_window.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(pin_window, text="Changer votre code PIN", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 15))

        entries = {}
        
        ctk.CTkLabel(pin_window, text="Code PIN actuel :").pack(anchor="w", padx=20)
        entries['current'] = ctk.CTkEntry(pin_window, show="*")
        entries['current'].pack(fill="x", padx=20, pady=(0, 10))
        entries['current'].focus()

        ctk.CTkLabel(pin_window, text="Nouveau code PIN (4 chiffres min.) :").pack(anchor="w", padx=20)
        entries['new'] = ctk.CTkEntry(pin_window, show="*")
        entries['new'].pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(pin_window, text="Confirmer le nouveau code PIN :").pack(anchor="w", padx=20)
        entries['confirm'] = ctk.CTkEntry(pin_window, show="*")
        entries['confirm'].pack(fill="x", padx=20, pady=(0, 20))
        entries['confirm'].bind("<Return>", lambda event, e=entries, w=pin_window: self._change_pin(e, w))

        button_frame = ctk.CTkFrame(pin_window, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=10)
        button_frame.grid_columnconfigure((0, 1), weight=1)

        save_button = ctk.CTkButton(button_frame, text="Enregistrer", command=lambda: self._change_pin(entries, pin_window))
        save_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        cancel_button = ctk.CTkButton(button_frame, text="Annuler", command=pin_window.destroy, fg_color="gray50")
        cancel_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def _change_pin(self, entries, window):
        """Valide et change le code PIN."""
        success, message = pin_manager.change_pin(entries['current'].get(), entries['new'].get(), entries['confirm'].get())
        if success:
            messagebox.showinfo("Succès", message, parent=window)
            window.destroy()
        else:
            messagebox.showerror("Erreur", message, parent=window)
            entries['current'].focus()

    def _change_theme(self, new_theme):
        """Sauvegarde le nouveau thème et informe l'utilisateur."""
        settings_manager.save_appearance_theme(new_theme)
        messagebox.showinfo("Thème modifié", "Le nouveau thème sera appliqué au prochain redémarrage de l'application.")

    def _delete_directory(self, dir_path, dir_name):
        if messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer définitivement le dossier '{dir_name}' et tout son contenu ?"):
            try:
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path)
                self._show_status_message(f"Dossier '{dir_name}' supprimé avec succès.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de supprimer le dossier '{dir_name}':\n{e}")

    def _delete_all_data(self):
        if messagebox.askyesno("Confirmation FINALE", "ATTENTION : Vous êtes sur le point de supprimer TOUTES les données (factures, frais, budgets, sauvegardes).\n\nCette action est IRREVERSIBLE.\n\nContinuer ?"):
            dirs_to_delete = { "factures": config.FACTURES_DIR, "frais": config.FRAIS_DIR, "budget": config.BUDGET_DIR, "backups": config.BACKUPS_DIR }
            for name, path in dirs_to_delete.items():
                try:
                    if os.path.exists(path): shutil.rmtree(path)
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible de supprimer le dossier '{name}':\n{e}")
            self._show_status_message("Toutes les données ont été supprimées.")

    def _delete_invoices(self): self._delete_directory(config.FACTURES_DIR, "factures")
    def _delete_expenses(self): self._delete_directory(config.FRAIS_DIR, "frais")
    def _delete_budgets(self): self._delete_directory(config.BUDGET_DIR, "budget")

    def _regenerate_all_invoices_excel(self):
        """Lit toutes les factures, les sauvegarde, puis les ré-enregistre pour nettoyer les fichiers Excel."""
        if not messagebox.askyesno("Confirmation", "Cette opération va lire toutes vos factures, sauvegarder les fichiers Excel actuels, puis les recréer.\n\nCela peut corriger des erreurs de formatage ou de colonnes manquantes. L'opération peut prendre un certain temps.\n\nContinuer ?"):
            return

        self._show_status_message("Démarrage de la regénération des fichiers Excel...")
        self.update_idletasks() # Force UI update

        try:
            all_invoices_df = load_all_data()
            if all_invoices_df.empty:
                messagebox.showinfo("Information", "Aucune facture à traiter.")
                return

            available_years = get_available_years()
            for year in available_years:
                backup_database(year)
            
            self._show_status_message(f"Sauvegardes créées. Traitement de {len(all_invoices_df)} factures...")
            self.update_idletasks()

            for year in available_years:
                excel_path = os.path.join(config.FACTURES_DIR, str(year), f"factures_{year}.xlsx")
                if os.path.exists(excel_path):
                    os.remove(excel_path)

            all_invoices_df = all_invoices_df.where(pd.notnull(all_invoices_df), None)
            invoices_to_save = all_invoices_df.to_dict('records')

            for i, invoice_data in enumerate(invoices_to_save):
                save_to_excel(invoice_data)

            messagebox.showinfo("Succès", "La regénération des fichiers Excel est terminée avec succès.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue durant la regénération :\n{e}")

    def _load_data_with_cache(self, year=None):
        """Charge les données depuis le cache ou le disque."""
        cache_key = str(year) if year else "all"
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]

        if year:
            df = load_year_data(year)
        else:
            df = load_all_data()
        
        self.data_cache[cache_key] = df
        return df

    def _invalidate_data_cache(self):
        """Vide le cache des données pour forcer une relecture."""
        self.data_cache.clear()

    def _regenerate_all_invoice_pdfs(self):
        """
        Ouvre une fenêtre pour régénérer tous les PDF de factures existantes.
        """
        if not messagebox.askyesno("Confirmation", "Cette opération va écraser et remplacer tous les PDF de factures existants avec le format actuel.\n\nL'opération peut prendre plusieurs minutes et est irréversible.\n\nContinuer ?"):
            return

        all_invoices_df = self._load_data_with_cache()
        if all_invoices_df.empty:
            messagebox.showinfo("Information", "Aucune facture à régénérer.")
            return

        invoices_to_process = all_invoices_df.to_dict('records')
        total_invoices = len(invoices_to_process)

        # --- Fenêtre de progression ---
        progress_window = ctk.CTkToplevel(self)
        progress_window.title("Régénération en cours")
        progress_window.geometry("450x200")
        progress_window.transient(self)
        progress_window.grab_set()
        progress_window.protocol("WM_DELETE_WINDOW", lambda: None) # Disable closing
        progress_window.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(progress_window, text="Régénération des PDF en cours...", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(20, 10))

        progress_bar = ctk.CTkProgressBar(progress_window, width=400)
        progress_bar.pack(pady=10, padx=20)
        progress_bar.set(0)

        progress_label = ctk.CTkLabel(progress_window, text=f"Facture 0 / {total_invoices}")
        progress_label.pack()
        
        time_label = ctk.CTkLabel(progress_window, text="Temps restant estimé : calcul...")
        time_label.pack(pady=5)

        # Lancement de la régénération dans un thread séparé pour ne pas bloquer l'UI
        thread = threading.Thread(target=self._regenerate_pdfs_worker, args=(invoices_to_process,))
        thread.start()

        # Démarrage du moniteur de progression
        self._update_regeneration_progress(progress_window, progress_bar, progress_label, time_label, total_invoices, time.time())

    def _regenerate_pdfs_worker(self, invoices_to_process):
        """Tâche de fond pour la régénération des PDF."""
        try:
            for i, invoice_data in enumerate(invoices_to_process):
                clean_data = {k: v for k, v in invoice_data.items() if pd.notna(v)}
                
                if 'Membres_Famille' in clean_data and isinstance(clean_data.get('Membres_Famille'), str):
                    try:
                        clean_data['Membres_Famille'] = ast.literal_eval(clean_data['Membres_Famille'])
                    except (ValueError, SyntaxError):
                        if 'Membres_Famille' in clean_data: del clean_data['Membres_Famille']

                generate_pdf(clean_data, is_duplicate=False)
                self.regeneration_queue.put(('progress', i + 1))
            
            self.regeneration_queue.put(('done', len(invoices_to_process)))
        except Exception as e:
            self.regeneration_queue.put(('error', str(e)))

    def _update_regeneration_progress(self, window, bar, p_label, t_label, total, start_time):
        """Met à jour la fenêtre de progression en lisant la file d'attente."""
        try:
            message_type, data = self.regeneration_queue.get_nowait()

            if message_type == 'progress':
                progress = data / total
                bar.set(progress)
                p_label.configure(text=f"Facture {data} / {total}")

                elapsed_time = time.time() - start_time
                if data > 5:
                    time_per_item = elapsed_time / data
                    remaining_items = total - data
                    estimated_time = remaining_items * time_per_item
                    mins, secs = divmod(estimated_time, 60)
                    t_label.configure(text=f"Temps restant estimé : {int(mins)} min {int(secs)} sec")
                
                self.after(100, self._update_regeneration_progress, window, bar, p_label, t_label, total, start_time)
            elif message_type == 'done':
                window.destroy()
                messagebox.showinfo("Succès", f"{data} factures ont été régénérées avec succès.")
            elif message_type == 'error':
                window.destroy()
                messagebox.showerror("Erreur", f"Une erreur est survenue pendant la régénération:\n{data}")
        except queue.Empty:
            self.after(100, self._update_regeneration_progress, window, bar, p_label, t_label, total, start_time)

    def _show_status_message(self, message, duration=3000):
        """Affiche un message dans la barre de statut pour une durée limitée."""
        self.status_bar.configure(text=message)
        self.status_bar.after(duration, lambda: self.status_bar.configure(text=""))

    def _display_invoices_in_frame(self, dataframe, label):
        """Vide et remplit le cadre de résultats avec les factures d'un dataframe."""
        self.current_search_results_df = dataframe
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        self.results_frame.configure(label_text=label)

        if dataframe.empty:
            # Affiche un message différent si la recherche n'a pas encore été lancée
            if label == "Utilisez les filtres pour lancer une recherche":
                message = "🔎\nUtilisez les filtres ci-dessus et cliquez sur 'Appliquer' pour commencer."
            else:
                message = "🧐\nAucune facture ne correspond à votre recherche."
            empty_label = ctk.CTkLabel(self.results_frame, text=message, font=ctk.CTkFont(size=16), text_color="gray")
            empty_label.pack(pady=50, padx=20, expand=True)
            return

        for _, row in dataframe.iterrows():
            invoice_frame = ctk.CTkFrame(self.results_frame, corner_radius=6)
            invoice_frame.pack(fill="x", pady=(0, 8), padx=5)
            
            # Utilise grid pour que les boutons ne soient pas cachés
            invoice_frame.grid_columnconfigure(0, weight=0) # Colonne pour l'indicateur
            invoice_frame.grid_columnconfigure(1, weight=1) # La colonne du texte s'étend
            
            patient_name = f"{row.get('Prenom', '')} {row.get('Nom', '')}"
            payment_status = row.get('Methode_Paiement', 'N/A')

            # Indicateur visuel de statut
            status_color = "gray"
            if payment_status == "Impayé":
                invoice_frame.configure(border_width=1, border_color="#e74c3c")
                status_color = "#e74c3c"
            elif payment_status != "N/A":
                status_color = "#2ecc71"
            
            status_indicator = ctk.CTkLabel(invoice_frame, text="●", text_color=status_color, font=ctk.CTkFont(size=20))
            status_indicator.grid(row=0, column=0, sticky="w", padx=(10, 0))

            info_text = f"ID: {row['ID']} | Date: {row['Date']} | Patient: {patient_name} | {row['Montant']:.2f} € | Statut: {payment_status}"
            
            info_label = ctk.CTkLabel(invoice_frame, text=info_text, anchor="w")
            info_label.grid(row=0, column=1, sticky="ew", padx=(5, 10), pady=10)

            row_data = row.to_dict()
            
            # --- Effet de survol (Highlight) ---
            original_color = invoice_frame.cget("fg_color")
            hover_color = ("gray75", "gray25") # Gris clair (Light) / Gris foncé (Dark)

            def on_enter(event, frame=invoice_frame, color=hover_color):
                frame.configure(fg_color=color)

            def on_leave(event, frame=invoice_frame, orig=original_color):
                frame.configure(fg_color=orig)

            invoice_frame.bind("<Enter>", on_enter)
            invoice_frame.bind("<Leave>", on_leave)
            info_label.bind("<Enter>", on_enter)
            status_indicator.bind("<Enter>", on_enter)
            
            # Clic droit sur le cadre ou le texte pour ouvrir le menu
            invoice_frame.bind("<Button-3>", lambda event, data=row_data: self._show_invoice_context_menu(event, data))
            info_label.bind("<Button-3>", lambda event, data=row_data: self._show_invoice_context_menu(event, data))
            status_indicator.bind("<Button-3>", lambda event, data=row_data: self._show_invoice_context_menu(event, data))

            # Double-clic pour ouvrir le PDF
            invoice_frame.bind("<Double-1>", lambda event, data=row_data: self._view_invoice_pdf(data))
            info_label.bind("<Double-1>", lambda event, data=row_data: self._view_invoice_pdf(data))
            status_indicator.bind("<Double-1>", lambda event, data=row_data: self._view_invoice_pdf(data))

    def _create_tool_wrapper(self, title):
        """Crée un cadre contenant une barre de titre avec bouton Retour et un cadre de contenu."""
        wrapper = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        # Header
        header = ctk.CTkFrame(wrapper, height=50, corner_radius=0, fg_color=("gray85", "gray20"))
        header.pack(fill="x", side="top")
        
        btn_back = ctk.CTkButton(header, text="⬅ Menu", width=80, height=30, command=self._show_menu)
        btn_back.pack(side="left", padx=10, pady=10)
        
        lbl_title = ctk.CTkLabel(header, text=title, font=ctk.CTkFont(size=18, weight="bold"))
        lbl_title.pack(side="left", padx=20)
        
        content = ctk.CTkFrame(wrapper, corner_radius=0, fg_color="transparent")
        content.pack(fill="both", expand=True)
        
        wrapper.content_frame = content
        return wrapper

    def _show_tool(self, wrapper):
        self.menu_frame.grid_forget()

        # Chargement paresseux (lazy loading) des onglets
        if wrapper == self.new_invoice_wrapper and not self.is_new_invoice_tab_initialized:
            create_new_invoice_tab(self)
            # Initialise le formulaire après sa création
            self.prestation.set("Consultation adulte")
            self._update_form(self.prestation.get())
            self._toggle_payment_date_field()
            self.is_new_invoice_tab_initialized = True
        elif wrapper == self.search_wrapper and not self.is_search_tab_initialized:
            create_search_tab(self)
            self.is_search_tab_initialized = True
        elif wrapper == self.budget_wrapper and not self.is_budget_tab_initialized:
            create_budget_tab(self)
            self.is_budget_tab_initialized = True
        elif wrapper == self.expenses_wrapper and not self.is_expenses_tab_initialized:
            create_expenses_tab(self)
            self.is_expenses_tab_initialized = True
        elif wrapper == self.attestation_wrapper and not self.is_attestation_tab_initialized:
            create_attestation_tab(self)
            self.is_attestation_tab_initialized = True

        wrapper.grid(row=0, column=0, sticky="nsew")
        
        if wrapper == self.expenses_wrapper:
            self.geometry("1500x850")
            refresh_expenses_list(self)
        elif wrapper == self.search_wrapper:
            self.geometry("1200x850")
            # N'affiche rien par défaut pour éviter de charger des milliers de factures.
            self._display_invoices_in_frame(pd.DataFrame(), "Utilisez les filtres pour lancer une recherche")
        elif wrapper == self.budget_wrapper:
            self.geometry("600x850")
            calculate_budget(self)
        else:
            self.geometry("600x850")

    def _show_menu(self):
        self.new_invoice_wrapper.grid_forget()
        self.search_wrapper.grid_forget()
        self.budget_wrapper.grid_forget()
        self.expenses_wrapper.grid_forget()
        self.attestation_wrapper.grid_forget()
        self.menu_frame.grid(row=0, column=0, sticky="nsew")
        self.geometry("600x850")

    def _focus_search(self, event=None):
        """Passe à l'onglet de recherche et met le focus sur le champ de saisie."""
        self._show_tool(self.search_wrapper)
        self.search_entry.focus()

    def _open_invoice_folder(self, invoice_data):
        """Ouvre le dossier contenant le PDF de la facture."""
        folder_path = get_invoice_path(invoice_data, get_folder=True)
        
        if not os.path.isdir(folder_path):
            messagebox.showwarning("Dossier introuvable", f"Le dossier de la facture n'a pas été trouvé:\n{folder_path}")
            return
        
        try:
            os.startfile(folder_path)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le dossier:\n{e}")

    def _open_invoice_pdf_externally(self, invoice_data):
        """Ouvre le fichier PDF de la facture."""
        pdf_path = get_invoice_path(invoice_data)
        
        if not os.path.exists(pdf_path):
            messagebox.showwarning("Fichier introuvable", f"Le fichier PDF n'a pas été trouvé:\n{pdf_path}")
            return
        
        try:
            os.startfile(pdf_path)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le PDF:\n{e}")

    def _show_invoice_context_menu(self, event, invoice_data):
        """Affiche le menu contextuel pour une facture."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Visualiser le PDF", command=lambda: self._view_invoice_pdf(invoice_data))
        menu.add_command(label="Modifier la facture", command=lambda: self._open_modify_window(invoice_data))
        menu.add_command(label="Ouvrir le dossier", command=lambda: self._open_invoice_folder(invoice_data))
        menu.add_command(label="Ouvrir le PDF (externe)", command=lambda: self._open_invoice_pdf_externally(invoice_data))
        menu.add_separator()
        menu.add_command(label="Supprimer la facture", command=lambda: self._confirm_delete_invoice(invoice_data))
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _confirm_delete_invoice(self, invoice_data):
        """Demande confirmation et supprime la facture."""
        confirm = messagebox.askyesno("Confirmation", f"Voulez-vous vraiment supprimer la facture {invoice_data['ID']} ?\nCette action supprimera la ligne du fichier Excel (le PDF reste conservé).")
        if confirm:
            success = delete_invoice(invoice_data)
            if success:
                self._invalidate_data_cache()
                self._show_status_message("Facture supprimée du fichier Excel.")
                # Rafraîchir la liste actuelle
                self._apply_filters_and_search()
            else:
                messagebox.showerror("Erreur", "Impossible de supprimer la facture (fichier introuvable ou erreur d'accès).")

    def _apply_filters_and_search(self):
        """Applique tous les filtres de l'onglet recherche et affiche les résultats."""
        year = self.search_year_var.get()
        month = self.search_month_var.get()
        prestation = self.search_prestation_var.get()
        status = self.search_status_var.get()
        query = self.search_entry.get().lower().strip()

        # 1. Charger les données de base (année ou toutes)
        year_to_load = year if year != "Toutes" else None
        df = self._load_data_with_cache(year=year_to_load)

        if df.empty:
            self._display_invoices_in_frame(pd.DataFrame(), "Aucune facture trouvée")
            return
        
        try:
            results = df.copy()

            # 2. Filtrer par mois (si une année est sélectionnée)
            if year != "Toutes" and month != "Tous":
                month_index = MONTHS_FR.index(month) + 1
                # S'assure que la colonne Date est au format datetime
                if 'Date' in results.columns:
                    results['Date'] = pd.to_datetime(results['Date'], format='%d/%m/%Y', errors='coerce')
                    results = results[results['Date'].dt.month == month_index]

            # 3. Filtrer par type de prestation
            if prestation != "Toutes":
                results = results[results['Prestation'] == prestation]

            # 4. Filtrer par statut
            if status == "Impayées":
                results = results[results['Methode_Paiement'] == 'Impayé']
            elif status == "Payées":
                results = results[results['Methode_Paiement'] != 'Impayé']
            elif status == "Non-lieu":
                if 'Date_Seance' in results.columns:
                    results = results[results['Date_Seance'].astype(str).str.lower() == 'non-lieu']

            # 5. Filtrer par nom/prénom
            if query:
                results['FullName'] = results['Prenom'].str.lower() + ' ' + results['Nom'].str.lower()
                results = results[results['FullName'].str.contains(query, na=False)]
                if 'FullName' in results.columns:
                    results = results.drop(columns=['FullName'])

            self._display_invoices_in_frame(results, "Résultats des filtres")
        except Exception as e:
            messagebox.showerror("Erreur de filtrage", f"Une erreur est survenue : {e}")

    def _reset_filters(self):
        """Réinitialise tous les champs de filtre de la recherche."""
        self.search_year_var.set("Toutes")
        self.search_month_var.set("Tous")
        self.search_month_menu.configure(state="disabled")
        self.search_prestation_var.set("Toutes")
        self.search_status_var.set("Tous")
        self.search_entry.delete(0, 'end')
        # Pas besoin d'invalider le cache, on ré-applique juste les filtres
        self._apply_filters_and_search()

    def _on_search_year_change(self, selected_year):
        """Active ou désactive le filtre du mois en fonction de l'année."""
        if selected_year == "Toutes":
            self.search_month_menu.configure(state="disabled")
            self.search_month_var.set("Tous")
        else:
            self.search_month_menu.configure(state="normal")

    def _export_search_results(self):
        """Exporte les résultats de recherche actuels dans un fichier Excel."""
        if not hasattr(self, 'current_search_results_df') or self.current_search_results_df.empty:
            messagebox.showwarning("Export impossible", "Aucun résultat à exporter.")
            return

        try:
            # Proposer un nom de fichier par défaut
            default_filename = f"Export_Factures_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
            filepath = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Fichiers Excel", "*.xlsx"), ("Tous les fichiers", "*.*")],
                initialfile=default_filename,
                title="Enregistrer l'export Excel"
            )

            if not filepath:
                return # User cancelled

            # Exporter le DataFrame
            self.current_search_results_df.to_excel(filepath, index=False, engine='openpyxl')
            
            messagebox.showinfo("Succès", f"Les résultats ont été exportés avec succès vers :\n{filepath}")
        except Exception as e:
            messagebox.showerror("Erreur d'export", f"Une erreur est survenue lors de l'exportation :\n{e}")

    def _view_invoice_pdf(self, invoice_data):
        """Ouvre le visualiseur de PDF interne."""
        pdf_path = get_invoice_path(invoice_data)
        if not os.path.exists(pdf_path):
            messagebox.showwarning("Fichier introuvable", f"Le fichier PDF n'a pas été trouvé:\n{pdf_path}")
            return
        PDFViewer(self, pdf_path)

    def _open_modify_window(self, invoice_data):
        """Ouvre une fenêtre pour modifier le statut d'une facture."""
        modify_window = ctk.CTkToplevel(self)
        modify_window.title("Modifier la Facture")
        modify_window.geometry("400x520")
        modify_window.transient(self)
        modify_window.grab_set()

        info_frame = ctk.CTkFrame(modify_window, fg_color="transparent")
        info_frame.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(info_frame, text=f"Facture: {invoice_data['ID']}").pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"Patient: {invoice_data.get('Prenom', '')} {invoice_data.get('Nom', '')}").pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"Date de séance actuelle: {invoice_data.get('Date_Seance', 'N/A')}").pack(anchor="w", pady=(5,0))
        ctk.CTkLabel(info_frame, text=f"Statut actuel: {invoice_data['Methode_Paiement']}", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10,0))

        update_frame = ctk.CTkFrame(modify_window)
        update_frame.pack(pady=10, padx=10, fill="x")

        # --- Nouvelle Date de Séance ---
        ctk.CTkLabel(update_frame, text="Nouvelle date de séance :").pack(pady=(10, 5))
        seance_date_frame_modify = ctk.CTkFrame(update_frame, fg_color="transparent")
        seance_date_frame_modify.pack(fill="x", pady=5)
        seance_date_frame_modify.grid_columnconfigure(0, weight=1)

        seance_date_entry = ctk.CTkEntry(seance_date_frame_modify, placeholder_text="JJ/MM/AAAA ou 'Non-lieu'")
        seance_date_entry.grid(row=0, column=0, sticky="ew")
        seance_date_entry.insert(0, invoice_data.get('Date_Seance', ''))
        
        calendar_button = ctk.CTkButton(seance_date_frame_modify, text="📅", width=30, command=lambda: self._open_calendar(seance_date_entry, make_readonly=False))
        calendar_button.grid(row=0, column=1, padx=(5,0))

        # --- Nouveau Statut de Paiement ---
        ctk.CTkLabel(update_frame, text="Nouveau statut de paiement :").pack(pady=(10, 5))
        new_status_var = ctk.CTkOptionMenu(update_frame, values=["Virement", "Espèce", "Chèque"])
        new_status_var.pack(pady=5)
        new_status_var.set("Virement")

        ctk.CTkLabel(update_frame, text="Date de paiement :").pack(pady=(10, 5))
        payment_date_entry = ctk.CTkEntry(update_frame, placeholder_text="JJ/MM/AAAA")
        payment_date_entry.pack(pady=5)
        payment_date_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
        payment_date_entry.configure(state="readonly")
        payment_date_entry.bind("<1>", lambda event: self._open_calendar(payment_date_entry))

        regen_pdf_var = ctk.CTkCheckBox(update_frame, text="Régénérer le PDF de la facture")
        regen_pdf_var.pack(pady=10)
        regen_pdf_var.select()

        ctk.CTkButton(modify_window, text="Mettre à jour", command=lambda: self._update_invoice_status(
            invoice_data, new_status_var.get(), payment_date_entry.get(), seance_date_entry.get(), regen_pdf_var.get(), modify_window
        )).pack(pady=20)

        # Ajoute un raccourci avec la touche Entrée
        modify_window.bind("<Return>", lambda event: self._update_invoice_status(
            invoice_data, new_status_var.get(), payment_date_entry.get(), seance_date_entry.get(), regen_pdf_var.get(), modify_window
        ))

    def _open_calendar(self, entry_widget, make_readonly=True):
        """Ouvre une fenêtre Toplevel avec un calendrier pour sélectionner une date."""
        if hasattr(self, '_calendar_toplevel') and self._calendar_toplevel is not None and self._calendar_toplevel.winfo_exists():
            self._calendar_toplevel.focus()
            return

        def set_date_and_close():
            entry_widget.configure(state="normal")
            entry_widget.delete(0, 'end')
            entry_widget.insert(0, cal.get_date())
            if make_readonly:
                entry_widget.configure(state="readonly")
            self._calendar_toplevel.destroy()
            self._calendar_toplevel = None
            self.focus()

        def on_close():
            self._calendar_toplevel.destroy()
            self._calendar_toplevel = None

        self._calendar_toplevel = ctk.CTkToplevel(self)
        self._calendar_toplevel.title("Choisir une date")
        self._calendar_toplevel.transient(self)
        self._calendar_toplevel.grab_set()
        self._calendar_toplevel.protocol("WM_DELETE_WINDOW", on_close)

        try:
            current_date = datetime.strptime(entry_widget.get(), '%d/%m/%Y')
            cal = Calendar(self._calendar_toplevel, selectmode='day', locale='fr_FR', date_pattern='dd/mm/yyyy',
                           year=current_date.year, month=current_date.month, day=current_date.day)
        except (ValueError, TypeError):
            cal = Calendar(self._calendar_toplevel, selectmode='day', locale='fr_FR', date_pattern='dd/mm/yyyy')

        cal.pack(pady=10, padx=10)

        ok_button = ctk.CTkButton(self._calendar_toplevel, text="Valider", command=set_date_and_close)
        ok_button.pack(pady=10)

        self._calendar_toplevel.after(50, lambda: self._calendar_toplevel.geometry(f"+{self.winfo_x() + (self.winfo_width() - self._calendar_toplevel.winfo_width()) // 2}"
                                                                                   f"+{self.winfo_y() + (self.winfo_height() - self._calendar_toplevel.winfo_height()) // 2}"))

    def _add_family_member(self):
        """Ajoute une ligne de saisie pour un membre de la famille."""
        # Limite à 5 membres supplémentaires (total de 6)
        if len(self.family_member_entries) >= 5:
            return

        member_frame = ctk.CTkFrame(self.family_members_container)
        member_frame.pack(fill="x", pady=2, padx=5)
        member_frame.grid_columnconfigure((0, 1), weight=1)

        prenom_entry = ctk.CTkEntry(member_frame, placeholder_text=f"Prénom Membre {len(self.family_member_entries) + 2}")
        prenom_entry.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        nom_entry = ctk.CTkEntry(member_frame, placeholder_text=f"Nom Membre {len(self.family_member_entries) + 2}")
        nom_entry.grid(row=0, column=1, padx=(0, 5), sticky="ew")
        
        entries = (prenom_entry, nom_entry)

        remove_button = ctk.CTkButton(
            member_frame, text="✕", width=30, height=30,
            command=lambda f=member_frame, e=entries: self._remove_family_member(f, e)
        )
        remove_button.grid(row=0, column=2)

        self.family_member_entries.append(entries)

        if len(self.family_member_entries) >= 5:
            self.add_member_button.configure(state="disabled")

    def _remove_family_member(self, frame_to_destroy, entries_to_remove):
        """Supprime une ligne de saisie de membre de la famille."""
        frame_to_destroy.destroy()
        self.family_member_entries.remove(entries_to_remove)
        self.add_member_button.configure(state="normal")

    def _update_invoice_status(self, invoice_data, new_status, new_payment_date, new_seance_date, regen_pdf, window):
        """Met à jour le statut dans le fichier Excel et régénère le PDF si demandé."""
        try:
            invoice_date_str = invoice_data.get('Date')
            if not invoice_date_str:
                messagebox.showerror("Erreur", "Date de facture manquante, mise à jour impossible.", parent=window)
                return

            invoice_date = datetime.strptime(invoice_date_str, '%d/%m/%Y')
            year = invoice_date.year
            month_name = MONTHS_FR[invoice_date.month - 1]
            excel_path = os.path.join(config.FACTURES_DIR, str(year), f"factures_{year}.xlsx")

            if not os.path.exists(excel_path):
                messagebox.showerror("Erreur", f"Fichier Excel pour l'année {year} introuvable.", parent=window)
                return

            # Sauvegarde avant modification
            backup_database(year)

            all_sheets = pd.read_excel(excel_path, sheet_name=None, dtype={'ID': str, 'SequenceID': str})
            sheet_df = all_sheets.get(month_name)

            if sheet_df is None or 'ID' not in sheet_df.columns:
                messagebox.showerror("Erreur", f"Onglet '{month_name}' invalide ou corrompu.", parent=window)
                return

            invoice_index = sheet_df.index[sheet_df['ID'] == invoice_data['ID']].tolist()
            if not invoice_index:
                messagebox.showerror("Erreur", "Facture non trouvée dans le fichier.", parent=window)
                return
            
            idx = invoice_index[0]
            sheet_df.loc[idx, 'Methode_Paiement'] = new_status
            sheet_df.loc[idx, 'Date_Paiement'] = new_payment_date
            sheet_df.loc[idx, 'Date_Seance'] = new_seance_date
            
            all_sheets[month_name] = sheet_df

            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                for sheet_name, df_to_write in all_sheets.items():
                    df_to_write.to_excel(writer, sheet_name=sheet_name, index=False)

            if regen_pdf:
                updated_data = sheet_df.loc[idx].to_dict()
                clean_data = {k: v for k, v in updated_data.items() if pd.notna(v)}
                
                if 'Membres_Famille' in clean_data and isinstance(clean_data.get('Membres_Famille'), str):
                    try:
                        clean_data['Membres_Famille'] = ast.literal_eval(clean_data['Membres_Famille'])
                    except (ValueError, SyntaxError):
                        # Si ce n'est pas une liste, on la supprime pour éviter une erreur PDF
                        del clean_data['Membres_Famille']

                pdf_file = generate_pdf(clean_data, is_duplicate=True)
                messagebox.showinfo("Succès", f"Statut mis à jour et PDF régénéré:\n{pdf_file}", parent=window)
            else:
                messagebox.showinfo("Succès", "Le statut de la facture a été mis à jour.", parent=window)

            self._invalidate_data_cache()
            window.destroy()
            self._apply_filters_and_search()
        except Exception as e:
            messagebox.showerror("Erreur de mise à jour", f"Une erreur est survenue : {e}", parent=window)

    def _show_success_dialog(self, pdf_path):
        """Affiche une boîte de dialogue de succès avec des options pour ouvrir le fichier/dossier."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Succès")
        dialog.geometry("400x420")
        dialog.transient(self)
        dialog.grab_set()
        
        dialog.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(dialog, text="Facture générée avec succès !", font=ctk.CTkFont(size=18, weight="bold"))
        label.pack(pady=(20, 15))

        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=5, padx=50, fill="both", expand=True)

        def open_pdf():
            dialog.destroy() # Ferme la fenêtre de succès
            try:
                PDFViewer(self, pdf_path)
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'ouvrir le PDF:\n{e}")

        def open_folder():
            try:
                os.startfile(os.path.dirname(pdf_path))
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'ouvrir le dossier:\n{e}", parent=dialog)

        def print_pdf():
            try:
                os.startfile(pdf_path, "print")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de lancer l'impression:\n{e}", parent=dialog)

        def open_doctolib():
            webbrowser.open("https://pro.doctolib.fr/patient_messaging")

        # Ouvrir l'emplacement (Vert)
        folder_button = ctk.CTkButton(button_frame, text="📂  Ouvrir l'emplacement", command=open_folder, fg_color="#2ecc71", hover_color="#27ae60", height=40, font=ctk.CTkFont(size=14))
        folder_button.pack(pady=8, fill="x")

        # Visualiser le PDF (Rouge)
        pdf_button = ctk.CTkButton(button_frame, text="📄  Visualiser le PDF", command=open_pdf, fg_color="#e74c3c", hover_color="#c0392b", height=40, font=ctk.CTkFont(size=14))
        pdf_button.pack(pady=8, fill="x")

        # Imprimer (Orange)
        print_button = ctk.CTkButton(button_frame, text="🖨️  Imprimer", command=print_pdf, fg_color="#e67e22", hover_color="#d35400", height=40, font=ctk.CTkFont(size=14))
        print_button.pack(pady=8, fill="x")

        # Ouvrir Doctolib (Bleu)
        doctolib_button = ctk.CTkButton(button_frame, text="📅  Ouvrir Doctolib", command=open_doctolib, fg_color="#0596DE", hover_color="#047bb7", height=40, font=ctk.CTkFont(size=14))
        doctolib_button.pack(pady=8, fill="x")
        
        ok_button = ctk.CTkButton(dialog, text="Fermer", command=dialog.destroy, fg_color="gray50", hover_color="gray40", height=40)
        ok_button.pack(pady=(10, 20), padx=50, fill="x")

        # Centre la fenêtre par rapport à la fenêtre principale
        dialog.after(10, lambda: dialog.geometry(f"+{self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2}"
                                                 f"+{self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2}"))

    def _generate_attestation_pdf(self):
        """Récupère les données du formulaire d'attestation et génère le PDF."""
        consult_date = self.attestation_consult_date.get()
        gen_date = self.attestation_generation_date.get()
        gender = self.attestation_gender.get()
        patient_name = self.attestation_patient_name.get().strip()

        if not consult_date or not gen_date or not patient_name:
            messagebox.showwarning("Champs requis", "Veuillez remplir tous les champs.")
            return

        data = {
            "consultation_date": consult_date,
            "generation_date": gen_date,
            "gender": gender,
            "patient_name": patient_name
        }

        try:
            pdf_path = generate_attestation_pdf(data)
            self._show_success_dialog(pdf_path)
            self.attestation_patient_name.delete(0, 'end') # Vide le nom pour la prochaine
        except Exception as e:
            messagebox.showerror("Erreur de génération", f"Une erreur est survenue lors de la création du PDF :\n{e}")

    def _toggle_seance_date(self):
        """Active/désactive le champ de date de séance."""
        if self.seance_non_lieu_var.get():
            self.seance_date.configure(state="normal")
            self.seance_date.delete(0, 'end')
            self.seance_date.insert(0, "Non-lieu")
            self.seance_date.configure(state="readonly")
            self.seance_date.unbind("<1>")
        else:
            self.seance_date.configure(state="normal")
            self.seance_date.delete(0, 'end')
            self.seance_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
            self.seance_date.configure(state="readonly")
            self.seance_date.bind("<1>", lambda event: self._open_calendar(self.seance_date))

    def _toggle_payment_date_field(self, *args):
        """Affiche ou masque le champ de la date de paiement."""
        if self.payment_method.get() == "Impayé":
            self.payment_date_entry.grid_forget()
            self.payment_date_label.grid_forget()
        else:
            self.payment_date_label.grid(row=0, column=1, sticky="w")
            self.payment_date_entry.grid(row=1, column=1, pady=5, sticky="ew", padx=(5, 0))

    def _update_form(self, prestation_choisie):
        """Met à jour le montant et l'affichage du formulaire selon la prestation."""
        montant = self.prestations_prix.get(prestation_choisie)
        self.montant.delete(0, 'end')
        if montant is not None:
            self.montant.insert(0, f"{montant:.2f}")

        is_child_session = "enfant" in prestation_choisie.lower() or "adolescent" in prestation_choisie.lower()
        is_family_session = "familiale" in prestation_choisie.lower()
        is_couple_session = "couple" in prestation_choisie.lower()
        
        # Masque les cadres optionnels
        self.child_info_frame.grid_forget()
        self.family_frame.grid_forget()
        self.couple_frame.grid_forget()
        self.p1_civility_frame.grid_forget()

        if is_child_session:
            self.child_info_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
            self.p1_civility_frame.grid(row=1, column=0, sticky='w', padx=(10, 5))
            self.prenom.configure(placeholder_text="Prénom Parent 1")
            self.nom.configure(placeholder_text="Nom Parent 1")
        elif is_family_session:
            self.family_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
            self.prenom.configure(placeholder_text="Prénom Membre 1")
            self.nom.configure(placeholder_text="Nom Membre 1")
        elif is_couple_session:
            self.couple_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
            self.prenom.configure(placeholder_text="Prénom Partenaire 1")
            self.nom.configure(placeholder_text="Nom Partenaire 1")
        else:
            # Cas par défaut
            self.prenom.configure(placeholder_text="Prénom Patient")
            self.nom.configure(placeholder_text="Nom Patient")

    def valider(self):
        try:
            if not self.nom.get() or not self.montant.get():
                messagebox.showwarning("Champs requis", "Veuillez remplir les champs Nom et Montant.")
                return
            
            # --- Détermination de la date de référence pour l'ID, le nom de fichier et le classement ---
            seance_date_str = self.seance_date.get()
            payment_date_str = self.payment_date_entry.get()
            payment_method = self.payment_method.get()

            reference_date = datetime.now() # Fallback: date de création

            try:
                # 1. Priorité à la date de séance si elle est valide
                if seance_date_str and seance_date_str.lower().strip() != 'non-lieu':
                    reference_date = datetime.strptime(seance_date_str, '%d/%m/%Y')
                # 2. Sinon, date de paiement si elle existe et que la facture n'est pas "Impayé"
                elif payment_method != "Impayé" and payment_date_str:
                    reference_date = datetime.strptime(payment_date_str, '%d/%m/%Y')
                # 3. Sinon, la date de création est déjà définie comme fallback
            except ValueError:
                messagebox.showerror("Erreur de date", "Le format de la date de séance ou de paiement est invalide. Veuillez utiliser JJ/MM/AAAA.")
                return

            invoice_year = reference_date.year
            
            invoice_count_this_year = get_yearly_invoice_count(invoice_year)
            sequence_id = f"{invoice_count_this_year + 1:04d}"

            # Le nouveau format d'ID est YYYYMMDD-XXXX, basé sur la date de référence
            facture_id = f"{reference_date.strftime('%Y%m%d')}-{sequence_id}"
            data = {
                "ID": facture_id,
                "Date": reference_date.strftime("%d/%m/%Y"), # La date de référence devient la date de la facture
                "Nom": self.nom.get().strip(),
                "Prenom": self.prenom.get().strip(),
                "Adresse": self.adresse.get().strip(),
                "Prestation": self.prestation.get(),
                "Date_Seance": self.seance_date.get(),
                "Montant": float(self.montant.get()),
                "Methode_Paiement": self.payment_method.get(),
                "Note": self.personal_note.get().strip(),
            }
            data["SequenceID"] = sequence_id

            if data["Methode_Paiement"] != "Impayé":
                if self.payment_date_entry.get():
                    data["Date_Paiement"] = self.payment_date_entry.get()

            is_child_session = "enfant" in data["Prestation"].lower() or "adolescent" in data["Prestation"].lower()
            is_family_session = "familiale" in data["Prestation"].lower()
            is_couple_session = "couple" in data["Prestation"].lower()

            if is_child_session:
                if not self.enfant_nom.get() or not self.enfant_dob.get():
                    messagebox.showwarning("Champs requis", "Pour une séance enfant/ado, veuillez renseigner le nom et la date de naissance de l'enfant.")
                    return
                data["Attention_de"] = self.attention_var.get()
                data["Nom_Enfant"] = self.enfant_nom.get().strip()
                data["Naissance_Enfant"] = self.enfant_dob.get().strip()
                
                prenom2 = self.prenom2.get().strip()
                nom2 = self.nom2.get().strip()
                if prenom2 and nom2:
                    data["Attention_de2"] = self.attention_var2.get()
                    data["Prenom2"], data["Nom2"] = prenom2, nom2
            elif is_family_session:
                family_members = []
                if data["Prenom"] and data["Nom"]:
                    family_members.append(f"{data['Prenom']} {data['Nom']}")
                
                for prenom_entry, nom_entry in self.family_member_entries:
                    prenom = prenom_entry.get().strip()
                    nom = nom_entry.get().strip()
                    if prenom or nom:
                        family_members.append(f"{prenom} {nom}".strip())
                data["Membres_Famille"] = family_members
            elif is_couple_session:
                prenom2 = self.prenom2_couple.get().strip()
                nom2 = self.nom2_couple.get().strip()
                if prenom2 and nom2:
                    data["Prenom2"] = prenom2
                    data["Nom2"] = nom2

            self._invalidate_data_cache()
            save_to_excel(data)
            pdf_file = generate_pdf(data)
            self._show_success_dialog(pdf_file)
            
            # Vide les champs pour la saisie suivante
            self.nom.delete(0, 'end')
            self.prenom.delete(0, 'end')
            self.adresse.delete(0, 'end')
            if is_child_session:
                self.enfant_nom.delete(0, 'end')
                self.enfant_dob.delete(0, 'end')
                self.prenom2.delete(0, 'end')
                self.nom2.delete(0, 'end')
            elif is_family_session:
                for widget in self.family_members_container.winfo_children():
                    widget.destroy()
                self.family_member_entries.clear()
                self.add_member_button.configure(state="normal")
            elif is_couple_session:
                self.prenom2_couple.delete(0, 'end')
                self.nom2_couple.delete(0, 'end')
            
            self.personal_note.delete(0, 'end')
        except ValueError:
            messagebox.showerror("Erreur de format", "Le montant doit être un nombre valide (ex: 60 ou 60.50).")
        except Exception as e:
            messagebox.showerror("Erreur inattendue", f"Une erreur est survenue : {e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()