import customtkinter as ctk
from datetime import datetime
import os
import ast
import time
from tkinter import messagebox, PhotoImage
import tkinter as tk
from tkinter import filedialog
import random

# --- Imports des modules séparés ---
from . import config 
from . import pin_manager
from . import settings_manager 
from .utils import resource_path
from .menu import create_menu
from .login_ui import LoginUI
from .dashboard import update_dashboard_kpis, on_kpi_click
from .settings_ui import SettingsUI
from .invoice_actions import InvoiceActions
from .invoice_manager import InvoiceManager

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Fenêtre de chargement ---
        self.title("Opeyrateur - Chargement en cours...")
        # Centrer la fenêtre de chargement
        start_width = 400
        start_height = 200
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width / 2) - (start_width / 2)
        y = (screen_height / 2) - (start_height / 2)
        self.geometry(f'{start_width}x{start_height}+{int(x)}+{int(y)}')

        loading_frame = ctk.CTkFrame(self)
        ctk.CTkLabel(loading_frame, text="Chargement de l'application...", font=("Montserrat", 16)).pack(pady=(40, 10))
        progress_bar = ctk.CTkProgressBar(loading_frame, width=300)
        progress_bar.pack(pady=10, padx=20)
        progress_bar.start()

        # --- Configuration de la grille principale ---
        self.grid_rowconfigure(0, weight=1) # Ligne pour le contenu principal
        self.grid_rowconfigure(1, weight=0) # Ligne pour la barre de statut
        self.grid_columnconfigure(0, weight=1)
        loading_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")

        self.update_idletasks() # Forcer l'affichage de la fenêtre de chargement
        start_time = time.time()

        self.title("Opeyrateur - A. Peyrat")

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

        # --- Caches pour la performance ---
        self.data_cache = {}
        self.current_search_results_df = None

        # Assure que la configuration du PIN existe
        pin_manager.setup_pin_if_needed()

        # Assure que la configuration des PDF existe
        settings_manager.setup_default_settings()

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
        self.new_invoice_wrapper.bind("<Control-Return>", lambda event: self.invoice_manager.valider())

        # --- Initialisation des modules UI ---
        self.login_ui = LoginUI(self)
        self.settings_ui = SettingsUI(self)
        self.invoice_actions = InvoiceActions(self)
        self.invoice_manager = InvoiceManager(self)

        # --- Fin de l'initialisation, on affiche l'écran de connexion ---
        end_time = time.time()
        # Ce temps ne sera visible que dans la console (mode debug)
        print(f"Temps de chargement de l'initialisation : {end_time - start_time:.2f} secondes.")

        progress_bar.stop()
        loading_frame.destroy()

        self.geometry("1920x1080")
        self.resizable(False, False)

        self.login_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.login_frame.grid(row=0, column=0, sticky="nsew")
        self.login_ui.create_login_screen()

    def _open_settings_window(self):
        self.settings_ui.open_settings_window()

    def _load_data_with_cache(self, year=None):
        """Charge les données depuis le cache ou le disque."""
        cache_key = str(year) if year else "all"
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
        from .data_manager import load_year_data, load_all_data

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
        self.current_search_results_df = dataframe
        
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        self.results_frame.configure(label_text=label)

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
            
            status_indicator = ctk.CTkLabel(invoice_frame, text="●", text_color=status_color, font=ctk.CTkFont(size=24))
            status_indicator.grid(row=0, column=0, sticky="w", padx=(10, 0))

            info_text = f"ID: {row['ID']} | Date: {row['Date']} | Patient: {patient_name} | {row['Montant']:.2f} € | Statut: {payment_status}"
            
            info_label = ctk.CTkLabel(invoice_frame, text=info_text, anchor="w", font=self.font_regular)
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
            invoice_frame.bind("<Button-3>", lambda event, data=row_data: self.invoice_actions.show_invoice_context_menu(event, data))
            info_label.bind("<Button-3>", lambda event, data=row_data: self.invoice_actions.show_invoice_context_menu(event, data))
            status_indicator.bind("<Button-3>", lambda event, data=row_data: self.invoice_actions.show_invoice_context_menu(event, data))

            # Double-clic pour ouvrir le PDF
            invoice_frame.bind("<Double-1>", lambda event, data=row_data: self.invoice_actions.view_invoice_pdf(data))
            info_label.bind("<Double-1>", lambda event, data=row_data: self.invoice_actions.view_invoice_pdf(data))
            status_indicator.bind("<Double-1>", lambda event, data=row_data: self.invoice_actions.view_invoice_pdf(data))
            
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

    def _create_tool_wrapper(self, title):
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
        
        content = ctk.CTkFrame(wrapper, corner_radius=0, fg_color="transparent")
        content.pack(fill="both", expand=True)
        
        wrapper.content_frame = content
        return wrapper

    def _show_tool(self, wrapper):
        self.menu_frame.grid_forget()

        # Chargement paresseux (lazy loading) des onglets
        if wrapper == self.new_invoice_wrapper and not self.is_new_invoice_tab_initialized:
            from .new_invoice_tab import create_new_invoice_tab
            create_new_invoice_tab(self)
            # Initialise le formulaire après sa création
            self.prestation.set("Consultation adulte")
            self.invoice_manager.update_form(self.prestation.get())
            self.invoice_manager.toggle_payment_date_field()
            self.is_new_invoice_tab_initialized = True
        elif wrapper == self.search_wrapper and not self.is_search_tab_initialized:
            from .search_tab import create_search_tab
            create_search_tab(self)
            self.is_search_tab_initialized = True
        elif wrapper == self.budget_wrapper and not self.is_budget_tab_initialized:
            from .budget_tab import create_budget_tab, calculate_budget
            create_budget_tab(self)
            self.is_budget_tab_initialized = True
        elif wrapper == self.expenses_wrapper and not self.is_expenses_tab_initialized:
            from .expenses_tab import create_expenses_tab, refresh_expenses_list
            create_expenses_tab(self)
            self.is_expenses_tab_initialized = True
        elif wrapper == self.attestation_wrapper and not self.is_attestation_tab_initialized:
            from .attestation_tab import create_attestation_tab
            create_attestation_tab(self)
            self.is_attestation_tab_initialized = True

        wrapper.grid(row=0, column=0, sticky="nsew")
        
        if wrapper == self.expenses_wrapper:
            refresh_expenses_list(self)
        elif wrapper == self.search_wrapper:
            import pandas as pd
            # N'affiche rien par défaut pour éviter de charger des milliers de factures.
            self._display_invoices_in_frame(pd.DataFrame(), "Utilisez les filtres pour lancer une recherche")
        elif wrapper == self.budget_wrapper:
            from .budget_tab import calculate_budget
            calculate_budget(self)

    def _show_menu(self):
        self.new_invoice_wrapper.grid_forget()
        self.search_wrapper.grid_forget()
        self.budget_wrapper.grid_forget()
        self.expenses_wrapper.grid_forget()
        self.attestation_wrapper.grid_forget()
        self.menu_frame.grid(row=0, column=0, sticky="nsew")
        update_dashboard_kpis(self)

    def _update_dashboard_kpis(self):
        update_dashboard_kpis(self)

    def _on_kpi_click(self, kpi_name):
        on_kpi_click(self, kpi_name)

    def _focus_search(self, event=None):
        """Passe à l'onglet de recherche et met le focus sur le champ de saisie."""
        self._show_tool(self.search_wrapper)
        self.search_entry.focus()

    def _apply_filters_and_search(self):
        """Applique tous les filtres de l'onglet recherche et affiche les résultats."""
        import pandas as pd
        from .data_manager import MONTHS_FR

        year = self.search_year_var.get()
        month = self.search_month_var.get()
        prestation = self.search_prestation_var.get()
        status = self.search_status_var.get()
        query = self.search_entry.get().lower().strip()

        self.current_page = 1 # Réinitialise la pagination à la première page

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

    def _open_calendar(self, entry_widget, make_readonly=True):
        """Ouvre une fenêtre Toplevel avec un calendrier pour sélectionner une date."""
        from tkcalendar import Calendar
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
            from .pdf_generator import generate_attestation_pdf
            pdf_path = generate_attestation_pdf(data)
            self.invoice_actions.show_success_dialog(pdf_path)
            self.attestation_patient_name.delete(0, 'end') # Vide le nom pour la prochaine
        except Exception as e:
            messagebox.showerror("Erreur de génération", f"Une erreur est survenue lors de la création du PDF :\n{e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()