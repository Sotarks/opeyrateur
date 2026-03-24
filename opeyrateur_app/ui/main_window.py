import customtkinter as ctk
from datetime import datetime
import os
import time
from tkinter import messagebox, PhotoImage
import tkinter as tk
from tkinter import filedialog
from PIL import Image
import threading
import warnings
import sys
import logging

# Ignorer l'avertissement de conflit entre PyFPDF et fpdf2
warnings.filterwarnings("ignore", category=UserWarning, module="fpdf")

# --- Imports des modules séparés ---
from opeyrateur_app.core import config
from opeyrateur_app.utils import pin_manager
from opeyrateur_app.services import updater
from opeyrateur_app.core import settings_manager
from opeyrateur_app.utils.utils import resource_path
from opeyrateur_app.ui.components.menu import create_menu
from opeyrateur_app.ui.views.login_ui import LoginUI
from opeyrateur_app.ui.tabs.dashboard import update_dashboard_kpis, on_kpi_click
from opeyrateur_app.ui.views.settings_ui import SettingsUI
from opeyrateur_app.services.invoice_actions import InvoiceActions
from opeyrateur_app.services.invoice_manager import InvoiceManager

# --- Configuration du Logging ---
LOG_FILE = os.path.join(config.BASE_DIR, "log.txt")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'
)

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
        
    import tkinter as tk
    if issubclass(exc_type, tk.TclError):
        err_msg = str(exc_value).lower()
        if "bad window path name" in err_msg and (".!ctktoplevel" in err_msg or "toplevel" in err_msg):
            # Ignore harmless CustomTkinter bug on rapid window destruction
            return
            
    logging.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Capture des erreurs Tkinter (interface graphique)
        self.report_callback_exception = self._handle_tk_exception
        
        logging.info("==========================================")
        logging.info("Application started")

        # --- Fenêtre de chargement (Splash Screen) ---
        self.overrideredirect(True) # Masque la barre de titre
        self.attributes('-topmost', True) # Au premier plan
        
        # Dimensions et centrage
        splash_w, splash_h = 600, 400
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - splash_w) // 2
        y = (screen_h - splash_h) // 2
        self.geometry(f'{splash_w}x{splash_h}+{x}+{y}')

        # Design du Splash Screen
        self.splash_frame = ctk.CTkFrame(self, corner_radius=20, border_width=2, border_color="#2A2A2A", fg_color=["#F0F0F0", "#1a1a1a"])
        self.splash_frame.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Logo
        try:
            logo_path = resource_path(os.path.join("src", "logo.png"))
            if os.path.exists(logo_path):
                pil_img = Image.open(logo_path)
                logo_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(120, 120))
                ctk.CTkLabel(self.splash_frame, image=logo_img, text="").pack(pady=(50, 20))
        except Exception:
            pass

        # Titre et Sous-titre
        ctk.CTkLabel(self.splash_frame, text="L'Opeyrateur", font=("Montserrat", 36, "bold")).pack(pady=(0, 5))
        ctk.CTkLabel(self.splash_frame, text="Gestion de cabinet simplifiée", font=("Montserrat", 14), text_color="gray").pack(pady=(0, 40))

        # Barre de progression
        self.splash_progress = ctk.CTkProgressBar(self.splash_frame, width=400, height=10, corner_radius=5)
        self.splash_progress.pack(pady=(0, 10))
        self.splash_progress.start()

        self.update() # Force l'affichage immédiat
        start_time = time.time()

        # --- Définir l'icône de la fenêtre ---
        try:
            logo_path = resource_path(os.path.join("src", "logo.png"))
            if os.path.exists(logo_path):
                self.iconphoto(False, PhotoImage(file=logo_path))
        except Exception as e:
            # Affiche une erreur dans la console si l'icône ne peut pas être chargée, mais ne bloque pas l'app
            print(f"Erreur lors du chargement de l'icône : {e}")

        self.prestations_prix = settings_manager.get_prestations()
        # --- Définition des polices ---
        self.font_regular = ctk.CTkFont(family="Montserrat", size=13)
        self.font_bold = ctk.CTkFont(family="Montserrat", size=13, weight="bold")
        self.font_large = ctk.CTkFont(family="Montserrat", size=16, weight="bold")
        self.font_title = ctk.CTkFont(family="Montserrat", size=24, weight="bold")
        self.font_button = ctk.CTkFont(family="Montserrat", size=14, weight="bold")

        self.expense_sort_state = ('date', False) # (column_id, is_reversed)
        
        # --- Pagination ---
        self.current_page = 1
        self.items_per_page = 50

        # Ajout des flags pour le chargement paresseux (lazy loading)
        self.is_new_invoice_tab_initialized = False
        self.is_search_tab_initialized = False
        self.is_budget_tab_initialized = False
        self.is_expenses_tab_initialized = False
        self.is_attestation_tab_initialized = False
        self.is_calendar_tab_initialized = False

        # --- Caches pour la performance ---
        self.data_cache = {}
        self.current_search_results_df = None
        self.dashboard_chart_data_cache = None
        self.dashboard_pie_data_cache = None
        self._search_job = None # Pour dé-bouncer la recherche principale
        self.selected_invoices_vars = {} # Stocke les variables des checkboxes {invoice_id: BooleanVar}

        # Assure que la configuration du PIN existe
        pin_manager.setup_pin_if_needed()

        # Assure que la configuration des PDF existe
        settings_manager.setup_default_settings()
        
        # Lance la migration Excel -> SQLite si nécessaire
        from opeyrateur_app.core.migration import check_and_migrate
        check_and_migrate()

        # --- Frame du Menu Principal ---
        self.menu_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        # --- Création des Wrappers pour les outils ---
        self.new_invoice_wrapper = self._create_tool_wrapper("Nouvelle Facture", scrollable=True)
        self.new_invoice_tab = self.new_invoice_wrapper.content_frame 

        self.search_wrapper = self._create_tool_wrapper("Rechercher", scrollable=False)
        self.search_tab = self.search_wrapper.content_frame

        self.budget_wrapper = self._create_tool_wrapper("Budget", scrollable=True)
        self.budget_tab = self.budget_wrapper.content_frame

        self.expenses_wrapper = self._create_tool_wrapper("Frais", scrollable=False)
        self.expenses_tab = self.expenses_wrapper.content_frame

        self.attestation_wrapper = self._create_tool_wrapper("Attestation", scrollable=True)
        self.attestation_tab = self.attestation_wrapper.content_frame

        self.calendar_wrapper = self._create_tool_wrapper("Agenda", scrollable=False)
        self.calendar_tab = self.calendar_wrapper.content_frame

        # --- Construction du Menu (via script externe) ---
        create_menu(self)

        # --- Raccourci Clavier ---
        self.bind("<Escape>", lambda event: self._show_menu())

        # --- Barre de Statut ---
        self.status_bar_frame = ctk.CTkFrame(self, height=25, fg_color="transparent")
        self.status_bar_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))
        self.status_bar_frame.grid_columnconfigure(1, weight=1)

        self.version_label = ctk.CTkLabel(self.status_bar_frame, text=f"v{updater.APP_VERSION}", height=25, anchor="w", font=ctk.CTkFont(size=11), text_color="gray")
        self.version_label.grid(row=0, column=0, sticky="w")

        self.status_bar = ctk.CTkLabel(self.status_bar_frame, text="", height=25, anchor="w")
        self.status_bar.grid(row=0, column=1, sticky="ew", padx=10)

        # --- Raccourcis Clavier contextuels ---
        self.bind("<Control-f>", self._focus_search)
        self.bind("<F11>", self.toggle_fullscreen)
        # Le bind sur le wrapper assure que le raccourci n'est actif que sur cet écran
        self.new_invoice_wrapper.bind("<Control-Return>", lambda event: self.invoice_manager.valider())
        self.new_invoice_wrapper.bind("<Return>", lambda event: self.invoice_manager.valider())

        # --- Initialisation des modules UI ---
        self.login_ui = LoginUI(self)
        self.settings_ui = SettingsUI(self)
        self.invoice_actions = InvoiceActions(self)
        self.invoice_manager = InvoiceManager(self)

        # --- Fin de l'initialisation, on affiche l'écran de connexion ---
        end_time = time.time()
        # Ce temps ne sera visible que dans la console (mode debug)
        print(f"Temps de chargement de l'initialisation : {end_time - start_time:.2f} secondes.")

        self.splash_progress.stop()
        self.splash_frame.destroy()

        # Restauration de la fenêtre principale
        self.overrideredirect(False)
        self.attributes('-topmost', False)
        self.title("Opeyrateur - A. Peyrat")
        
        # Configuration de la grille principale
        self.grid_rowconfigure(0, weight=1) # Ligne pour le contenu principal
        self.grid_rowconfigure(1, weight=0) # Ligne pour la barre de statut
        self.grid_columnconfigure(0, weight=1)

        # Gestion de l'affichage (DPI & Taille)
        zoom = settings_manager.get_ui_zoom()
        ctk.set_widget_scaling(zoom)
        ctk.set_window_scaling(zoom)
        
        geometry = settings_manager.get_window_geometry()
        self.geometry(geometry)
        self.resizable(True, True)
        # Si c'est la taille par défaut, on maximise, sinon on respecte la taille sauvegardée
        if geometry == '1280x800':
            self.after(0, lambda: self.state('zoomed'))
            
        self.withdraw()
        
        # Animation de fondu (Fade-in)
        self.attributes("-alpha", 0.0)
        self.deiconify()
        self._animate_fade_in()

        self.login_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.login_frame.grid(row=0, column=0, sticky="nsew")
        self.login_ui.create_login_screen()
        
        # Sauvegarde de la position à la fermeture
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _handle_tk_exception(self, exc, val, tb):
        """Gère les exceptions survenues dans les callbacks Tkinter."""
        err_msg = str(val).lower()
        if "bad window path name" in err_msg and "ctktoplevel" in err_msg:
            # Ignore ce bug spécifique de CustomTkinter sur Windows (destruction rapide d'un Toplevel)
            return

        logging.error("Tkinter exception", exc_info=(exc, val, tb))
        messagebox.showerror("Erreur", f"Une erreur est survenue :\n{val}\n\nConsultez log.txt pour plus de détails.")

    def on_closing(self):
        """Sauvegarde la géométrie et ferme l'application."""
        logging.info("Application closed by user")
        settings_manager.save_window_geometry(self.geometry())
        self.destroy()

    def _open_settings_window(self):
        self.settings_ui.open_settings_window()

    def _load_data_with_cache(self, year=None):
        """Charge les données depuis le cache ou le disque."""
        cache_key = str(year) if year else "all"
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
        from opeyrateur_app.core.data_manager import load_year_data, load_all_data

        if year:
            df = load_year_data(year)
        else:
            df = load_all_data()
        
        self.data_cache[cache_key] = df
        return df

    def _invalidate_data_cache(self):
        """Vide le cache des données pour forcer une relecture."""
        self.data_cache.clear()

    def _show_status_message(self, message, duration=3000):
        """Affiche un message dans la barre de statut pour une durée limitée."""
        self.status_bar.configure(text=message)
        self.status_bar.after(duration, lambda: self.status_bar.configure(text=""))

    def _display_invoices_in_frame(self, dataframe, label):
        """Vide et remplit le cadre de résultats avec les factures d'un dataframe."""
        import pandas as pd
        self.selected_invoices_vars = {} # Reset selection
        self.current_search_results_df = dataframe
        
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        # Ajout du nombre de résultats dans le titre
        count = len(dataframe) if dataframe is not None else 0
        self.results_frame.configure(label_text=f"{label} ({count})")

        if dataframe is None or dataframe.empty:
            # Affiche un message différent si la recherche n'a pas encore été lancée
            if label == "Utilisez les filtres pour lancer une recherche" or dataframe is None:
                message = "🔎\nUtilisez les filtres ci-dessus et cliquez sur 'Appliquer' pour commencer."
            else:
                message = "🧐\nAucune facture ne correspond à votre recherche."
            empty_label = ctk.CTkLabel(self.results_frame, text=message, font=self.font_large, text_color="gray")
            empty_label.pack(pady=50, padx=20, expand=True)
            if hasattr(self, 'pagination_frame'):
                self._update_pagination_controls(0)
            return

        # --- Logique de Pagination ---
        import math
        total_items = len(dataframe)
        total_pages = math.ceil(total_items / self.items_per_page)
        
        if self.current_page < 1: self.current_page = 1
        if self.current_page > total_pages: self.current_page = total_pages

        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        
        page_data = dataframe.iloc[start_idx:end_idx]

        for _, row in page_data.iterrows():
            # --- Design Compact (Liste) ---
            invoice_frame = ctk.CTkFrame(self.results_frame, corner_radius=8, fg_color=("white", "gray20"), border_width=1, border_color=("gray90", "gray30"))
            invoice_frame.pack(fill="x", pady=(0, 2), padx=5)
            
            invoice_frame.grid_columnconfigure(3, weight=1) # La colonne détails s'étend
            
            patient_name = f"{row.get('Prenom', '')} {row.get('Nom', '')}"
            nom_enfant = row.get('Nom_Enfant', '')
            if pd.notna(nom_enfant) and str(nom_enfant).strip() and str(nom_enfant).strip().lower() != 'nan':
                patient_name += f" (Enfant : {nom_enfant})"
            payment_status = row.get('Methode_Paiement', 'N/A')

            # Couleurs selon statut
            status_color = "gray"
            if payment_status == "Impayé": status_color = "#e74c3c"
            elif payment_status != "N/A": status_color = "#2ecc71"
            
            # 0. Checkbox de sélection
            row_data = row.to_dict()
            chk_var = ctk.BooleanVar()
            self.selected_invoices_vars[row.get('ID')] = (chk_var, row_data)
            chk = ctk.CTkCheckBox(invoice_frame, text="", variable=chk_var, width=24, height=24, corner_radius=4)
            chk.grid(row=0, column=0, padx=(10, 5), pady=2)

            # 1. Barre de statut
            status_strip = ctk.CTkFrame(invoice_frame, width=5, fg_color=status_color, corner_radius=0)
            status_strip.grid(row=0, column=1, sticky="ns", padx=(0, 10))

            # 2. Nom Patient
            name_label = ctk.CTkLabel(invoice_frame, text=patient_name, font=ctk.CTkFont(family="Montserrat", size=13, weight="bold"), anchor="w")
            name_label.grid(row=0, column=2, sticky="w", padx=(0, 10), pady=2)
            
            # 3. Détails (Date - Prestation)
            details_text = f"#{row.get('ID', '')}  |  {row['Date']}  |  {row.get('Prestation', 'Consultation')}"
            details_label = ctk.CTkLabel(invoice_frame, text=details_text, font=ctk.CTkFont(family="Montserrat", size=12), text_color="gray", anchor="w")
            details_label.grid(row=0, column=3, sticky="w", pady=2)
            
            # 3b. Info "Envoyé le"
            sent_date = row.get('Date_Envoi_Email')
            if pd.notna(sent_date) and str(sent_date).strip():
                sent_label = ctk.CTkLabel(invoice_frame, text=f"Envoyé le {sent_date}", font=ctk.CTkFont(size=10), text_color="#3498db")
                sent_label.grid(row=0, column=4, padx=10)
            else:
                # Placeholder vide pour alignement
                ctk.CTkLabel(invoice_frame, text="").grid(row=0, column=4)
            
            # 4. Statut
            status_label = ctk.CTkLabel(invoice_frame, text=payment_status.upper(), font=ctk.CTkFont(family="Montserrat", size=10, weight="bold"), text_color=status_color, anchor="e")
            status_label.grid(row=0, column=5, sticky="e", padx=15, pady=2)

            # 5. Montant
            amount_label = ctk.CTkLabel(invoice_frame, text=f"{row['Montant']:.2f} €", font=ctk.CTkFont(family="Montserrat", size=13, weight="bold"), text_color="#3498db", anchor="e")
            amount_label.grid(row=0, column=6, sticky="e", padx=(0, 10), pady=2)

            # 6. Actions (Email)
            email_btn = ctk.CTkButton(invoice_frame, text="✉️", width=30, height=25, fg_color="transparent", text_color=("gray50", "gray70"), hover_color=("gray80", "gray30"), command=lambda d=row_data: self.invoice_actions._prompt_send_email(invoice_data=d))
            email_btn.grid(row=0, column=7, sticky="e", padx=(0, 5), pady=2)

            # --- Effet de survol (Highlight) ---
            row_data = row.to_dict()
            original_color = invoice_frame.cget("fg_color")
            hover_color = ("gray95", "gray25")

            def on_enter(event, frame=invoice_frame, color=hover_color):
                frame.configure(fg_color=color)

            def on_leave(event, frame=invoice_frame, orig=original_color):
                frame.configure(fg_color=orig)

            # Applique les événements sur le cadre et ses enfants pour gérer correctement la sortie de la souris
            for widget in [invoice_frame, status_strip, name_label, details_label, amount_label, status_label, email_btn, chk]:
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)
                widget.bind("<Button-3>", lambda event, data=row_data: self.invoice_actions.show_invoice_context_menu(event, data))
                widget.bind("<Double-1>", lambda event, data=row_data: self.invoice_actions.view_invoice_pdf(data))
            
        if hasattr(self, 'pagination_frame'):
            self._update_pagination_controls(total_pages)

    def _update_pagination_controls(self, total_pages):
        """Met à jour l'état des boutons de pagination."""
        if total_pages <= 1:
            self.pagination_frame.grid_remove()
        else:
            self.pagination_frame.grid()
            self.lbl_page_info.configure(text=f"Page {self.current_page} / {total_pages}")
            
            state_prev = "normal" if self.current_page > 1 else "disabled"
            self.btn_prev_page.configure(state=state_prev)
            
            state_next = "normal" if self.current_page < total_pages else "disabled"
            self.btn_next_page.configure(state=state_next)

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._display_invoices_in_frame(self.current_search_results_df, self.results_frame.cget("label_text"))

    def _next_page(self):
        import math
        total_pages = math.ceil(len(self.current_search_results_df) / self.items_per_page)
        if self.current_page < total_pages:
            self.current_page += 1
            self._display_invoices_in_frame(self.current_search_results_df, self.results_frame.cget("label_text"))

    def _create_tool_wrapper(self, title, scrollable=False):
        """Crée un cadre contenant une barre de titre avec bouton Retour et un cadre de contenu."""
        wrapper = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        # Header
        header = ctk.CTkFrame(wrapper, height=50, corner_radius=0, fg_color=["#FFFFFF", "#1E1E1E"])
        header.pack(fill="x", side="top")
        
        btn_back = ctk.CTkButton(header, text="⬅  Menu", width=80, height=30, command=self._show_menu, font=self.font_bold, fg_color="transparent", text_color="#0596DE", hover_color=["#F0F0F0", "#2A2A2A"])
        btn_back.pack(side="left", padx=10, pady=10)
        
        lbl_title = ctk.CTkLabel(header, text=title, font=self.font_large)
        lbl_title.pack(side="left", padx=20)

        # Ligne de séparation sous l'en-tête
        line = ctk.CTkFrame(wrapper, height=1, fg_color=["#E0E0E0", "#2A2A2A"])
        line.pack(fill="x", side="top")
        
        if scrollable:
            content = ctk.CTkScrollableFrame(wrapper, corner_radius=0, fg_color="transparent")
        else:
            content = ctk.CTkFrame(wrapper, corner_radius=0, fg_color="transparent")
        content.pack(fill="both", expand=True)
        
        wrapper.content_frame = content
        return wrapper

    def _show_tool(self, wrapper):
        self.menu_frame.grid_forget()

        # Chargement paresseux (lazy loading) des onglets
        if wrapper == self.new_invoice_wrapper and not self.is_new_invoice_tab_initialized:
            from opeyrateur_app.ui.tabs.new_invoice_tab import create_new_invoice_tab
            create_new_invoice_tab(self)
            # Initialise le formulaire après sa création
            self.prestation.set("Consultation adulte")
            self.invoice_manager.update_form(self.prestation.get())
            self.invoice_manager.toggle_payment_date_field()
            self.is_new_invoice_tab_initialized = True
        
        if wrapper == self.new_invoice_wrapper:
            # Place le curseur dans le champ Prénom après un court délai
            self.after(100, lambda: self.prenom.focus_set() if self.prenom.winfo_exists() else None)
            
        elif wrapper == self.search_wrapper and not self.is_search_tab_initialized:
            from opeyrateur_app.ui.tabs.search_tab import create_search_tab
            create_search_tab(self)
            self.is_search_tab_initialized = True
        elif wrapper == self.budget_wrapper and not self.is_budget_tab_initialized:
            from opeyrateur_app.ui.tabs.budget_tab import create_budget_tab, calculate_budget
            create_budget_tab(self)
            self.is_budget_tab_initialized = True
        elif wrapper == self.expenses_wrapper and not self.is_expenses_tab_initialized:
            from opeyrateur_app.ui.tabs.expenses_tab import create_expenses_tab
            create_expenses_tab(self)
            self.is_expenses_tab_initialized = True
        elif wrapper == self.attestation_wrapper and not self.is_attestation_tab_initialized:
            from opeyrateur_app.ui.tabs.attestation_tab import create_attestation_tab
            create_attestation_tab(self)
            self.is_attestation_tab_initialized = True
        elif wrapper == self.calendar_wrapper and not self.is_calendar_tab_initialized:
            from opeyrateur_app.ui.tabs.calendar_tab import create_calendar_tab
            create_calendar_tab(self)
            self.is_calendar_tab_initialized = True

        wrapper.grid(row=0, column=0, sticky="nsew")
        
        if wrapper == self.expenses_wrapper:
            from opeyrateur_app.ui.tabs.expenses_tab import refresh_expenses_list
            refresh_expenses_list(self)
        elif wrapper == self.search_wrapper:
            import pandas as pd
            # N'affiche rien par défaut pour éviter de charger des milliers de factures.
            self._display_invoices_in_frame(pd.DataFrame(), "Utilisez les filtres pour lancer une recherche")
        elif wrapper == self.budget_wrapper:
            from opeyrateur_app.ui.tabs.budget_tab import calculate_budget
            calculate_budget(self)
        elif wrapper == self.attestation_wrapper:
            from opeyrateur_app.ui.tabs.attestation_tab import refresh_attestation_history
            refresh_attestation_history(self)
        elif wrapper == self.calendar_wrapper:
            from opeyrateur_app.ui.tabs.calendar_tab import _refresh_calendar_view
            _refresh_calendar_view(self)

    def _show_menu(self):
        self.new_invoice_wrapper.grid_forget()
        self.search_wrapper.grid_forget()
        self.budget_wrapper.grid_forget()
        self.expenses_wrapper.grid_forget()
        self.attestation_wrapper.grid_forget()
        self.calendar_wrapper.grid_forget()
        self.menu_frame.grid(row=0, column=0, sticky="nsew")
        
        # Force l'affichage immédiat du menu
        self.update_idletasks()
        
        # Chargement des données en arrière-plan pour éviter le gel de l'interface
        def _refresh_bg():
            from opeyrateur_app.ui.tabs.dashboard import load_dashboard_data, update_dashboard_views
            if not self.winfo_exists(): return
            try:
                data = load_dashboard_data(self)
                if self.winfo_exists():
                    self.after(0, lambda: update_dashboard_views(self, data))
            except Exception: pass
            
        threading.Thread(target=_refresh_bg, daemon=True).start()

    def _update_dashboard_kpis(self):
        update_dashboard_kpis(self)

    def _on_kpi_click(self, kpi_name):
        on_kpi_click(self, kpi_name)

    def _focus_search(self, event=None):
        """Passe à l'onglet de recherche et met le focus sur le champ de saisie."""
        self._show_tool(self.search_wrapper)
        self.search_entry.focus()

    def _filter_today(self):
        """Affiche les factures de la date du jour."""
        import pandas as pd
        
        now = datetime.now()
        today_str = now.strftime("%d/%m/%Y")
        year_str = str(now.year)
        
        # Charge les données de l'année en cours
        df = self._load_data_with_cache(year=year_str)
        
        if df.empty:
            self._display_invoices_in_frame(pd.DataFrame(), f"Aucune facture pour aujourd'hui ({today_str})")
            return

        # Filtrage
        try:
            results = df[df['Date'] == today_str]
            self._display_invoices_in_frame(results, f"Factures du {today_str}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du filtrage : {e}")

    def _apply_filters_and_search(self):
        """Applique tous les filtres de l'onglet recherche et affiche les résultats."""
        import pandas as pd
        from opeyrateur_app.core.data_manager import MONTHS_FR
        from opeyrateur_app.core.db_manager import advanced_search_invoices

        year = self.search_year_var.get()
        month = self.search_month_var.get()
        prestation = self.search_prestation_var.get()
        status = self.search_status_var.get()
        query = self.search_entry.get().strip()

        self.current_page = 1 # Réinitialise la pagination à la première page

        try:
            month_index = None
            if year != "Toutes" and month != "Tous":
                try:
                    month_index = MONTHS_FR.index(month) + 1
                except ValueError:
                    pass

            # Recherche optimisée directement en SQL
            results_dict = advanced_search_invoices(
                year=year,
                month_index=month_index,
                prestation=prestation,
                status=status,
                query=query
            )
            
            # Conversion en DataFrame pour compatibilité avec l'affichage et l'export
            df_results = pd.DataFrame(results_dict) if results_dict else pd.DataFrame()

            if df_results.empty:
                self._update_search_summary(pd.DataFrame())
                self._display_invoices_in_frame(pd.DataFrame(), "Aucune facture trouvée")
            else:
                self._update_search_summary(df_results)
                self._display_invoices_in_frame(df_results, "Résultats des filtres")
                
        except Exception as e:
            messagebox.showerror("Erreur de filtrage", f"Une erreur est survenue : {e}")

    def _update_search_summary(self, df):
        """Met à jour le cadre récapitulatif des revenus dans l'onglet Recherche."""
        if not hasattr(self, 'search_summary_frame'):
            return
            
        if df.empty:
            self.search_summary_frame.grid_remove()
            return
            
        self.search_summary_frame.grid()
        
        # Filtre les non-lieux qui ne comptent pas dans le CA
        valid_df = df[df['Methode_Paiement'] != 'Non-lieu'] if 'Methode_Paiement' in df.columns else df
        
        if valid_df.empty:
            self.lbl_summary_total.configure(text="Total: 0 €", text_color=("gray10", "gray90"))
            self.lbl_summary_details.configure(text="Aucune donnée financière")
            return
            
        total_revenue = valid_df[valid_df['Methode_Paiement'] != 'Impayé']['Montant'].sum()
        total_unpaid = valid_df[valid_df['Methode_Paiement'] == 'Impayé']['Montant'].sum()
        
        # Grouper par méthode de paiement
        try:
            grouped = valid_df.groupby('Methode_Paiement')['Montant'].sum()
            details = []
            for method, amount in grouped.items():
                if amount > 0:
                    details.append(f"{method}: {amount:,.0f}€".replace(',', ' '))
                    
            details_str = " | ".join(details)
            
            # Formattage global
            total_text = f"Encaissé: {total_revenue:,.0f} €".replace(',', ' ')
            if total_unpaid > 0:
                total_text += f"\nImpayés: {total_unpaid:,.0f} €"
                self.lbl_summary_total.configure(text=total_text, text_color="#e74c3c")
            else:
                self.lbl_summary_total.configure(text=total_text, text_color="#2ecc71")
                
            self.lbl_summary_details.configure(text=details_str)
            
        except Exception as e:
            print(f"Erreur de calcul du résumé: {e}")

    def _on_main_search_change(self, event=None):
        """Lance la recherche principale avec un délai pour améliorer la réactivité."""
        if hasattr(self, '_search_job') and self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(300, self._apply_filters_and_search)

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

    def _refresh_search_data(self):
        """Invalide le cache et ré-applique les filtres de recherche (Asynchrone)."""
        self.configure(cursor="watch")
        self.search_refresh_progress.grid()
        self.search_refresh_progress.start()
        self._show_status_message("Rafraîchissement des données en cours...", 5000)
        self._invalidate_data_cache()
        
        year = self.search_year_var.get()
        year_to_load = year if year != "Toutes" else None

        def _worker():
            self._load_data_with_cache(year=year_to_load)
            if self.winfo_exists():
                self.after(0, _on_complete)

        def _on_complete():
            self.configure(cursor="")
            self.search_refresh_progress.stop()
            self.search_refresh_progress.grid_remove()
            self._show_status_message("Données à jour.", 2000)
            self._apply_filters_and_search()

        threading.Thread(target=_worker, daemon=True).start()

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

    def _export_search_results_pdf(self):
        """Exporte les résultats de recherche actuels dans un fichier PDF."""
        if not hasattr(self, 'current_search_results_df') or self.current_search_results_df.empty:
            messagebox.showwarning("Export impossible", "Aucun résultat à exporter.")
            return

        try:
            from opeyrateur_app.services.pdf_generator import generate_search_report
            
            # Titre du rapport basé sur les filtres
            year = self.search_year_var.get()
            month = self.search_month_var.get()
            title = f"Rapport Recherche - {year}"
            if month != "Tous":
                title += f" - {month}"
            
            path = generate_search_report(title, self.current_search_results_df)
            
            from opeyrateur_app.ui.components.pdf_viewer import PDFViewer
            PDFViewer(self, path, download_filename=os.path.basename(path))
            
        except Exception as e:
            messagebox.showerror("Erreur d'export", f"Une erreur est survenue lors de l'exportation PDF :\n{e}")

    def _open_calendar(self, entry_widget, make_readonly=True):
        """Ouvre une fenêtre Toplevel avec un calendrier pour sélectionner une date."""
        # Protection contre les doubles clics (ouverture multiple)
        if getattr(self, '_is_calendar_opening', False):
            return

        from tkcalendar import Calendar
        if hasattr(self, '_calendar_toplevel') and self._calendar_toplevel is not None and self._calendar_toplevel.winfo_exists():
            self._calendar_toplevel.lift()
            self._calendar_toplevel.focus()
            return

        self._is_calendar_opening = True
        def set_date_and_close():
            entry_widget.configure(state="normal")
            entry_widget.delete(0, 'end')
            entry_widget.insert(0, cal.get_date())
            if make_readonly:
                entry_widget.configure(state="readonly")
            if self._calendar_toplevel:
                self._calendar_toplevel.destroy()
                self._calendar_toplevel = None
            entry_widget.focus()
            
        def set_today():
            cal.selection_set(datetime.now())
            set_date_and_close()

        def on_close():
            if self._calendar_toplevel:
                self._calendar_toplevel.destroy()
                self._calendar_toplevel = None

        # Fermeture au clic en dehors (perte de focus)
        def on_focus_out(event):
            self.after(100, check_focus)
            
        def check_focus():
            if not self._calendar_toplevel or not self._calendar_toplevel.winfo_exists(): return
            focused = self.focus_get()
            
            # Si le focus est perdu (clic hors appli) ou sur une autre fenêtre
            if focused is None:
                 on_close()
                 return
            
            # Vérifie si le widget focus est dans le calendrier
            widget = focused
            while widget:
                if widget == self._calendar_toplevel: return
                widget = widget.master
            on_close()

        # Détermine la fenêtre parente (pour gérer les modales correctement)
        try:
            try:
                parent = entry_widget.winfo_toplevel()
            except Exception:
                parent = self

            self._calendar_toplevel = ctk.CTkToplevel(parent)
            self._calendar_toplevel.title("Choisir une date")
            self._calendar_toplevel.transient(parent)
            
            # Si la fenêtre parente n'est pas l'application principale (ex: fenêtre modale),
            # on doit forcer le grab_set pour garder le focus et éviter la fermeture immédiate.
            if parent != self:
                self._calendar_toplevel.grab_set()
                
            self._calendar_toplevel.protocol("WM_DELETE_WINDOW", on_close)
            self._calendar_toplevel.bind("<FocusOut>", on_focus_out)

            # --- Navigation Rapide (Année & Mois) ---
            nav_frame = ctk.CTkFrame(self._calendar_toplevel, fg_color="transparent")
            nav_frame.pack(pady=(10, 0), padx=10, fill="x")
            
            # Import pour les mois
            from opeyrateur_app.core.data_manager import MONTHS_FR
            
            ctk.CTkLabel(nav_frame, text="Année :", font=("Montserrat", 12)).pack(side="left", padx=(10, 5))
            
            year_entry = ctk.CTkEntry(nav_frame, width=60, height=25)
            year_entry.pack(side="left", padx=5)
            
            def update_calendar_year(event=None):
                try:
                    new_year = int(year_entry.get())
                    try:
                        sel_date = datetime.strptime(cal.get_date(), '%d/%m/%Y')
                        try: new_date = sel_date.replace(year=new_year)
                        except ValueError: new_date = sel_date.replace(day=28, year=new_year)
                    except: new_date = datetime(new_year, 1, 1)
                    cal.selection_set(new_date)
                    cal.see(new_date)
                except ValueError: pass

            year_entry.bind("<Return>", update_calendar_year)
            ctk.CTkButton(nav_frame, text="OK", width=40, height=25, command=update_calendar_year).pack(side="left", padx=5)

            # Sélection du Mois
            ctk.CTkLabel(nav_frame, text="Mois :", font=("Montserrat", 12)).pack(side="left", padx=(10, 5))
            
            def update_calendar_month(choice):
                try:
                    month_idx = MONTHS_FR.index(choice) + 1
                    sel_date = datetime.strptime(cal.get_date(), '%d/%m/%Y')
                    import calendar
                    last_day = calendar.monthrange(sel_date.year, month_idx)[1]
                    new_day = min(sel_date.day, last_day)
                    new_date = sel_date.replace(month=month_idx, day=new_day)
                    cal.selection_set(new_date)
                    cal.see(new_date)
                except Exception: pass

            month_menu = ctk.CTkOptionMenu(nav_frame, values=MONTHS_FR, width=110, height=25, command=update_calendar_month)
            month_menu.pack(side="left", padx=5)

            try:
                current_date = datetime.strptime(entry_widget.get(), '%d/%m/%Y')
                cal = Calendar(self._calendar_toplevel, selectmode='day', locale='fr_FR', date_pattern='dd/mm/yyyy',
                            year=current_date.year, month=current_date.month, day=current_date.day)
                year_entry.insert(0, str(current_date.year))
                month_menu.set(MONTHS_FR[current_date.month - 1])
            except (ValueError, TypeError):
                cal = Calendar(self._calendar_toplevel, selectmode='day', locale='fr_FR', date_pattern='dd/mm/yyyy')
                year_entry.insert(0, str(datetime.now().year))
                month_menu.set(MONTHS_FR[datetime.now().month - 1])

            cal.pack(pady=10, padx=10)

            btn_frame = ctk.CTkFrame(self._calendar_toplevel, fg_color="transparent")
            btn_frame.pack(pady=10, padx=10, fill="x")

            ctk.CTkButton(btn_frame, text="Aujourd'hui", command=set_today, fg_color="#3498db", width=100).pack(side="left", padx=5, expand=True)
            ctk.CTkButton(btn_frame, text="Valider", command=set_date_and_close, width=100).pack(side="left", padx=5, expand=True)

            self._calendar_toplevel.after(50, lambda: self._calendar_toplevel.geometry(f"+{parent.winfo_x() + (parent.winfo_width() - self._calendar_toplevel.winfo_width()) // 2}"
                                                                                    f"+{parent.winfo_y() + (parent.winfo_height() - self._calendar_toplevel.winfo_height()) // 2}"))
            self._calendar_toplevel.after(100, lambda: self._calendar_toplevel.focus_set())
        finally:
            self._is_calendar_opening = False

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
            from opeyrateur_app.services.pdf_generator import generate_attestation_pdf
            pdf_path = generate_attestation_pdf(data)
            self.invoice_actions.show_success_dialog(pdf_path)
            self.attestation_patient_name.delete(0, 'end') # Vide le nom pour la prochaine
            
            from opeyrateur_app.ui.tabs.attestation_tab import refresh_attestation_history
            refresh_attestation_history(self)
        except Exception as e:
            messagebox.showerror("Erreur de génération", f"Une erreur est survenue lors de la création du PDF :\n{e}")

    def check_automatic_expenses(self):
        """Vérifie si les frais récurrents doivent être générés (1er du mois)."""
        from datetime import datetime
        from opeyrateur_app.core import settings_manager
        from opeyrateur_app.core.data_manager import save_expense
        
        now = datetime.now()
        
        # On vérifie si on est le 1er du mois
        if now.day != 1:
            return

        current_month_key = now.strftime("%Y-%m")
        last_run = settings_manager.get_last_recurring_run()

        # Si déjà exécuté pour ce mois, on ne fait rien
        if last_run == current_month_key:
            return

        # On demande confirmation pour ne pas surprendre l'utilisateur
        if messagebox.askyesno("Frais Récurrents", "📅 Nous sommes le 1er du mois.\n\nVoulez-vous générer automatiquement vos frais récurrents ?"):
            recurring_data = settings_manager.get_recurring_expenses()
            
            if not recurring_data:
                messagebox.showinfo("Info", "Aucun frais récurrent configuré.")
                settings_manager.set_last_recurring_run(current_month_key)
                return

            count = 0
            today_str = now.strftime("%d/%m/%Y")
            
            for item in recurring_data:
                data = item.copy()
                data['Date'] = today_str
                if save_expense(data):
                    count += 1
            
            # Enregistre que c'est fait pour ce mois
            settings_manager.set_last_recurring_run(current_month_key)
            
            self._show_status_message(f"{count} frais récurrents générés.")
            
            # Mise à jour de l'interface si nécessaire
            if self.is_expenses_tab_initialized:
                from opeyrateur_app.ui.tabs.expenses_tab import refresh_expenses_list
                refresh_expenses_list(self)
            
            self._update_dashboard_kpis()

    def check_unpaid_invoices(self):
        """Vérifie les factures impayées de plus de 30 jours."""
        import pandas as pd
        from opeyrateur_app.core import settings_manager
        from datetime import timedelta

        # --- OPTIMISATION: Charger uniquement les 2 dernières années pour la vérification ---
        now = datetime.now()
        df_current_year = self._load_data_with_cache(year=now.year)
        df_prev_year = self._load_data_with_cache(year=now.year - 1) if now.year > 2000 else pd.DataFrame()
        df = pd.concat([df_current_year, df_prev_year], ignore_index=True)

        if df.empty or 'Methode_Paiement' not in df.columns: return

        # Filtrage des impayés
        unpaid = df[df['Methode_Paiement'] == 'Impayé'].copy()
        if unpaid.empty: return

        try:
            # Conversion date et calcul du seuil (30 jours)
            unpaid['DateObj'] = pd.to_datetime(unpaid['Date'], format='%d/%m/%Y', errors='coerce')
            limit_date = datetime.now() - timedelta(days=30)
            
            # Factures antérieures à la date limite
            late_invoices = unpaid[(unpaid['DateObj'].notna()) & (unpaid['DateObj'] < limit_date)]

            if not late_invoices.empty:
                ignored_ids = settings_manager.get_ignored_invoices()
                new_late_invoices = late_invoices[~late_invoices['ID'].isin(ignored_ids)]

                if not new_late_invoices.empty:
                    count = len(new_late_invoices)
                    total = new_late_invoices['Montant'].sum()
                    
                    # Affichage différé pour ne pas bloquer le chargement visuel
                    self.after(1500, lambda: self._prompt_unpaid_invoices(count, total, new_late_invoices['ID'].tolist()))
        except Exception as e:
            print(f"Erreur vérification impayés: {e}")

    def _prompt_unpaid_invoices(self, count, total, late_invoice_ids):
        """Affiche une boîte de dialogue personnalisée pour les factures en retard."""
        from opeyrateur_app.core import settings_manager
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Rappel de paiement")
        dialog.geometry("450x250")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        dialog.after(10, lambda: dialog.geometry(f"+{self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2}"
                                                 f"+{self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2}"))

        msg = f"⚠️ ALERTE RETARDS\n\nVous avez {count} nouvelle(s) facture(s) impayée(s)\ndepuis plus de 30 jours.\n\nMontant total en attente : {total:.2f} €"
        
        ctk.CTkLabel(dialog, text=msg, justify="left", font=self.font_regular).pack(pady=20, padx=20, anchor="w")
        
        dont_notify_var = ctk.BooleanVar()
        ctk.CTkCheckBox(dialog, text="Ne plus me notifier pour ces factures", variable=dont_notify_var, font=self.font_regular).pack(pady=10, padx=20, anchor="w")

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20, padx=20, fill="x")
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        def handle_yes():
            dialog.destroy()
            self._show_tool(self.search_wrapper)
            self.search_year_var.set("Toutes")
            self._on_search_year_change("Toutes")
            self.search_status_var.set("Impayées")
            self._apply_filters_and_search()

        def handle_no():
            if dont_notify_var.get():
                ignored_ids = settings_manager.get_ignored_invoices()
                ignored_ids.extend(late_invoice_ids)
                settings_manager.save_ignored_invoices(list(set(ignored_ids)))
            dialog.destroy()

        ctk.CTkButton(btn_frame, text="Afficher la liste", command=handle_yes, height=40).grid(row=0, column=1, padx=(5,0), sticky="ew")
        ctk.CTkButton(btn_frame, text="Plus tard", command=handle_no, fg_color="gray50", height=40).grid(row=0, column=0, padx=(0,5), sticky="ew")
        
        dialog.protocol("WM_DELETE_WINDOW", handle_no)

    def _animate_fade_in(self, alpha=0.0):
        """Gère l'animation de fondu à l'ouverture."""
        if not self.winfo_exists(): return
        if alpha < 1.0:
            alpha += 0.05
            self.attributes("-alpha", alpha)
            self.after(15, lambda: self._animate_fade_in(alpha))
        else:
            self.attributes("-alpha", 1.0)

    def toggle_fullscreen(self, event=None):
        """Bascule le mode plein écran."""
        self.attributes("-fullscreen", not self.attributes("-fullscreen"))

if __name__ == "__main__":
    app = App()
    app.mainloop()