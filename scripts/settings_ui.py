import customtkinter as ctk
from tkinter import messagebox
import os
import threading
import queue
import time
import random
from datetime import datetime
import ast

from . import config
from . import settings_manager
from . import pin_manager
from .dashboard import update_dashboard_kpis

class SettingsUI:
    def __init__(self, app):
        self.app = app
        self.regeneration_queue = queue.Queue()

    def open_settings_window(self):
        """Ouvre la fenêtre des réglages."""
        settings_window = ctk.CTkToplevel(self.app)
        settings_window.title("Réglages")
        settings_window.geometry("1000x700")
        settings_window.transient(self.app)
        settings_window.grab_set()

        # Configuration de la grille : Sidebar (fixe) + Contenu (extensible)
        settings_window.grid_columnconfigure(0, weight=0, minsize=250)
        settings_window.grid_columnconfigure(1, weight=1)
        settings_window.grid_rowconfigure(0, weight=1)

        # =================================================================================
        # 1. SIDEBAR DE NAVIGATION (GAUCHE)
        # =================================================================================
        sidebar = ctk.CTkFrame(settings_window, corner_radius=0, fg_color=("gray90", "gray16"))
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(6, weight=1) # Spacer

        ctk.CTkLabel(sidebar, text="Paramètres", font=ctk.CTkFont(family="Montserrat", size=24, weight="bold")).pack(pady=(30, 20), padx=20, anchor="w")
        
        self.nav_buttons = {}
        
        def select_category(category_name):
            # Met à jour l'apparence des boutons
            for name, btn in self.nav_buttons.items():
                if name == category_name:
                    btn.configure(fg_color=("gray75", "gray25"))
                else:
                    btn.configure(fg_color="transparent")
            
            # Affiche le contenu correspondant
            self._show_settings_content(category_name, content_area, settings_window)

        categories = [
            ("Personnalisation", "🎨"),
            ("Gestion des Données", "💾"),
            ("Maintenance", "🛠️"),
            ("Debug / Tests", "🐞"),
            ("Zone de Danger", "☢️")
        ]

        for name, icon in categories:
            btn = ctk.CTkButton(sidebar, text=f"{icon}  {name}", anchor="w", fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray80", "gray25"), height=45, font=self.app.font_button, command=lambda n=name: select_category(n))
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[name] = btn

        # Bouton Fermer en bas
        ctk.CTkButton(sidebar, text="Fermer", command=settings_window.destroy, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"), font=self.app.font_button, height=40).pack(side="bottom", fill="x", padx=20, pady=20)

        # =================================================================================
        # 2. CONTENU PRINCIPAL (DROITE)
        # =================================================================================
        content_area = ctk.CTkFrame(settings_window, corner_radius=0, fg_color="transparent")
        content_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        content_area.grid_columnconfigure(0, weight=1)
        content_area.grid_rowconfigure(0, weight=1)
        
        # Affiche la première catégorie par défaut
        select_category("Personnalisation")

    def _show_settings_content(self, category, parent, window):
        # Vide le contenu précédent
        for widget in parent.winfo_children():
            widget.destroy()
            
        # Crée un cadre défilant pour le contenu
        scroll_frame = ctk.CTkScrollableFrame(parent, corner_radius=15, fg_color=("white", "gray20"))
        scroll_frame.grid(row=0, column=0, sticky="nsew")
        scroll_frame.grid_columnconfigure(0, weight=1)

        # Titre de la section
        ctk.CTkLabel(scroll_frame, text=category, font=ctk.CTkFont(family="Montserrat", size=24, weight="bold"), text_color="#3498db").pack(anchor="w", padx=20, pady=(20, 10))

        if category == "Personnalisation":
            self._build_personalization_settings(scroll_frame)
        elif category == "Gestion des Données":
            self._build_data_settings(scroll_frame)
        elif category == "Maintenance":
            self._build_maintenance_settings(scroll_frame)
        elif category == "Debug / Tests":
            self._build_debug_settings(scroll_frame, window)
        elif category == "Zone de Danger":
            self._build_danger_settings(scroll_frame)

    def _build_personalization_settings(self, parent):
        ctk.CTkButton(parent, text="Modifier les informations des PDF", font=self.app.font_button, command=self._open_pdf_settings_window, height=40).pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(parent, text="Changer le code PIN", font=self.app.font_button, command=self._open_change_pin_window, height=40).pack(fill="x", padx=20, pady=5)
        
        # Zoom UI
        zoom_frame = ctk.CTkFrame(parent, fg_color="transparent")
        zoom_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(zoom_frame, text="Zoom de l'interface :", font=self.app.font_button).pack(side="left", padx=10)
        
        current_zoom = settings_manager.get_ui_zoom()
        zoom_values = ["80%", "90%", "100%", "110%", "120%", "150%"]
        zoom_map = {"80%": 0.8, "90%": 0.9, "100%": 1.0, "110%": 1.1, "120%": 1.2, "150%": 1.5}
        
        current_zoom_str = "100%"
        for k, v in zoom_map.items():
            if abs(v - current_zoom) < 0.01:
                current_zoom_str = k
                break
                
        zoom_menu = ctk.CTkOptionMenu(zoom_frame, values=zoom_values, command=lambda v: self._change_zoom(zoom_map[v]))
        zoom_menu.set(current_zoom_str)
        zoom_menu.pack(side="right", padx=10)

    def _build_data_settings(self, parent):
        ctk.CTkButton(parent, text="Ouvrir le dossier de l'application", font=self.app.font_button, command=self._open_app_directory, height=40).pack(fill="x", padx=20, pady=5)

    def _build_maintenance_settings(self, parent):
        ctk.CTkLabel(parent, text="Outils de correction en cas de problème d'affichage ou de données.", font=self.app.font_regular, text_color="gray").pack(anchor="w", padx=20, pady=(0, 10))
        
        btn_grid = ctk.CTkFrame(parent, fg_color="transparent")
        btn_grid.pack(fill="x", padx=20)
        ctk.CTkButton(btn_grid, text="Régénérer PDF Factures", font=self.app.font_button, command=self._regenerate_all_invoice_pdfs, height=40).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(btn_grid, text="Régénérer Excel Factures", font=self.app.font_button, command=self._regenerate_all_invoices_excel, height=40).pack(side="left", fill="x", expand=True, padx=(5, 0))

    def _build_debug_settings(self, parent, window):
        debug_ctrl = ctk.CTkFrame(parent, fg_color="transparent")
        debug_ctrl.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkLabel(debug_ctrl, text="Nombre d'éléments à générer :", font=self.app.font_regular).pack(side="left")
        debug_count_entry = ctk.CTkEntry(debug_ctrl, width=60)
        debug_count_entry.pack(side="left", padx=10)
        debug_count_entry.insert(0, "5")
        
        debug_btns = ctk.CTkFrame(parent, fg_color="transparent")
        debug_btns.pack(fill="x", padx=20)
        ctk.CTkButton(debug_btns, text="Générer Factures Test", font=self.app.font_button, command=lambda: self._generate_random_invoices(debug_count_entry, settings_window), height=40).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(debug_btns, text="Générer Frais Test", font=self.app.font_button, command=lambda: self._generate_random_expenses(debug_count_entry, settings_window), height=40).pack(side="left", fill="x", expand=True, padx=(5, 0))

    def _build_danger_settings(self, parent):
        ctk.CTkLabel(parent, text="Attention : Ces actions sont irréversibles.", font=self.app.font_bold, text_color="#e74c3c").pack(anchor="w", padx=20, pady=(0, 10))
        
        danger_style = {"fg_color": ("#ffebee", "#3e2723"), "text_color": "#e74c3c", "hover_color": ("#ffcdd2", "#5d4037"), "height": 40, "font": self.app.font_button}
        
        ctk.CTkButton(parent, text="Supprimer TOUTES les données", command=self._delete_all_data, **danger_style).pack(fill="x", padx=20, pady=5)
        
        danger_grid = ctk.CTkFrame(parent, fg_color="transparent")
        danger_grid.pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(danger_grid, text="Supprimer Factures", command=self._delete_invoices, **danger_style).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(danger_grid, text="Supprimer Frais", command=self._delete_expenses, **danger_style).pack(side="left", fill="x", expand=True, padx=5)
        
        ctk.CTkButton(parent, text="Supprimer Budgets", command=self._delete_budgets, **danger_style).pack(fill="x", padx=20, pady=5)

    def _change_zoom(self, new_zoom):
        settings_manager.save_ui_zoom(new_zoom)
        messagebox.showinfo("Redémarrage requis", "Le changement de zoom sera pris en compte au prochain démarrage de l'application.")

    def _open_app_directory(self):
        try:
            os.startfile(config.BASE_DIR)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le dossier de l'application:\n{e}")

    def _open_pdf_settings_window(self):
        pdf_info = settings_manager.get_pdf_info()
        pdf_settings_window = ctk.CTkToplevel(self.app)
        pdf_settings_window.title("Réglages des informations PDF")
        pdf_settings_window.geometry("700x750")
        pdf_settings_window.transient(self.app)
        pdf_settings_window.grab_set()

        scrollable_frame = ctk.CTkScrollableFrame(pdf_settings_window, label_text="Informations pour les documents PDF")
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        entries = {}
        # ... (Code de création des champs identique à l'original, simplifié ici pour la brièveté) ...
        # Pour simplifier la réponse, je reprends la logique de création des champs de manière générique ou directe
        fields = [
            ("Informations Société", [
                ("company_name", "Nom de la société"),
                ("address_line1", "Adresse (ligne 1)"),
                ("address_line2", "Adresse (ligne 2 - CP Ville)"),
                ("siret", "N° Siret"),
                ("rpps", "N° RPPS")
            ]),
            ("Informations Signature & Contact", [
                ("practitioner_name", "Nom complet (pour signature)"),
                ("practitioner_title", "Titre / Profession"),
                ("phone_number", "Numéro de téléphone"),
                ("email", "Email (optionnel)")
            ]),
            ("Informations Attestation", [
                ("attestation_city", "Ville pour 'Fait à...'")
            ])
        ]

        for section, items in fields:
            ctk.CTkLabel(scrollable_frame, text=section, font=self.app.font_large).pack(pady=(10, 5), anchor="w")
            for key, label in items:
                ctk.CTkLabel(scrollable_frame, text=f"{label} :").pack(anchor="w", padx=10)
                entry = ctk.CTkEntry(scrollable_frame)
                entry.pack(fill="x", padx=10, pady=(0, 5))
                entry.insert(0, pdf_info.get(key, ''))
                entries[key] = entry

        # Champ spécial pour le message
        ctk.CTkLabel(scrollable_frame, text="Modèle du message de l'attestation :").pack(anchor="w", padx=10)
        entries['attestation_message'] = ctk.CTkTextbox(scrollable_frame, height=100)
        entries['attestation_message'].pack(fill="x", expand=True, padx=10, pady=(0, 15))
        entries['attestation_message'].insert("1.0", pdf_info.get('attestation_message', ''))

        button_frame = ctk.CTkFrame(pdf_settings_window, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(button_frame, text="Enregistrer", command=lambda: self._save_pdf_settings(entries, pdf_settings_window), font=self.app.font_button).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(button_frame, text="Annuler", command=pdf_settings_window.destroy, fg_color="gray50", font=self.app.font_button).pack(side="left", fill="x", expand=True, padx=(5, 0))

    def _save_pdf_settings(self, entries, window):
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
        pin_window = ctk.CTkToplevel(self.app)
        pin_window.title("Changer le code PIN")
        pin_window.geometry("400x350")
        pin_window.transient(self.app)
        pin_window.grab_set()

        ctk.CTkLabel(pin_window, text="Changer votre code PIN", font=self.app.font_large).pack(pady=(20, 15))
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
        
        ctk.CTkButton(pin_window, text="Enregistrer", command=lambda: self._change_pin(entries, pin_window), font=self.app.font_button).pack(pady=10)

    def _change_pin(self, entries, window):
        success, message = pin_manager.change_pin(entries['current'].get(), entries['new'].get(), entries['confirm'].get())
        if success:
            messagebox.showinfo("Succès", message, parent=window)
            window.destroy()
        else:
            messagebox.showerror("Erreur", message, parent=window)

    def _delete_directory(self, dir_path, dir_name):
        if messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer définitivement le dossier '{dir_name}' et tout son contenu ?"):
            import shutil
            try:
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path)
                self.app._show_status_message(f"Dossier '{dir_name}' supprimé avec succès.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de supprimer le dossier '{dir_name}':\n{e}")

    def _delete_all_data(self):
        if messagebox.askyesno("Confirmation FINALE", "ATTENTION : Vous êtes sur le point de supprimer TOUTES les données.\n\nCette action est IRREVERSIBLE.\n\nContinuer ?"):
            import shutil
            dirs_to_delete = { "factures": config.FACTURES_DIR, "frais": config.FRAIS_DIR, "budget": config.BUDGET_DIR, "backups": config.BACKUPS_DIR }
            for name, path in dirs_to_delete.items():
                try:
                    if os.path.exists(path): shutil.rmtree(path)
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible de supprimer le dossier '{name}':\n{e}")
            self.app._show_status_message("Toutes les données ont été supprimées.")

    def _delete_invoices(self): self._delete_directory(config.FACTURES_DIR, "factures")
    def _delete_expenses(self): self._delete_directory(config.FRAIS_DIR, "frais")
    def _delete_budgets(self): self._delete_directory(config.BUDGET_DIR, "budget")

    def _generate_random_invoices(self, count_entry, window):
        try:
            count = int(count_entry.get())
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer un nombre valide.")
            return
        if count <= 0: return

        if not messagebox.askyesno("Confirmation", f"Voulez-vous générer {count} factures de test ?"):
            return

        window.destroy()
        self.app._show_status_message("Génération des factures en cours...")
        self.app.update_idletasks()

        from .data_manager import save_to_excel, get_yearly_invoice_count
        from .pdf_generator import generate_pdf
        
        current_year = datetime.now().year
        prestations = list(self.app.prestations_prix.keys())
        payment_methods = ["Virement", "Espèce", "Chèque", "Impayé"]

        for i in range(count):
            start_date = datetime(current_year, 1, 1).timestamp()
            end_date = datetime.now().timestamp()
            random_ts = start_date + (end_date - start_date) * random.random()
            date_obj = datetime.fromtimestamp(random_ts)
            date_str = date_obj.strftime("%d/%m/%Y")
            
            cnt = get_yearly_invoice_count(date_obj.year)
            sequence_id = f"{cnt + 1:04d}"
            facture_id = f"{date_obj.strftime('%Y%m%d')}-{sequence_id}"

            prestation = random.choice(prestations)
            montant = self.app.prestations_prix.get(prestation, 0.0)
            payment_method = random.choice(payment_methods)
            date_paiement = date_str if payment_method != "Impayé" else ""
            
            data = {
                "ID": facture_id, "Date": date_str, "Nom": f"Test {i+1}", "Prenom": f"Patient {i+1}",
                "Adresse": "Adresse Test", "Prestation": prestation, "Date_Seance": date_str,
                "Montant": montant, "Methode_Paiement": payment_method, "Date_Paiement": date_paiement,
                "Note": "Facture de test générée aléatoirement", "SequenceID": sequence_id
            }
            save_to_excel(data)
            generate_pdf(data)
            if i % 2 == 0: self.app.update_idletasks()

        self.app._invalidate_data_cache()
        update_dashboard_kpis(self.app)
        messagebox.showinfo("Succès", f"{count} factures ont été générées.")

    def _generate_random_expenses(self, count_entry, window):
        try:
            count = int(count_entry.get())
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer un nombre valide.")
            return
        if count <= 0: return

        if not messagebox.askyesno("Confirmation", f"Voulez-vous générer {count} frais de test ?"):
            return

        window.destroy()
        self.app._show_status_message("Génération des frais en cours...")
        self.app.update_idletasks()

        from .data_manager import save_expense
        current_year = datetime.now().year
        categories = ["Loyer", "Déplacement", "Matériel", "Fournitures", "Cotisations", "Repas", "Autre"]
        descriptions = ["Achat fournitures", "Loyer cabinet", "Repas midi", "Essence", "Assurance", "Abonnement logiciel", "Papeterie"]

        for i in range(count):
            start_date = datetime(current_year, 1, 1).timestamp()
            end_date = datetime.now().timestamp()
            random_ts = start_date + (end_date - start_date) * random.random()
            date_obj = datetime.fromtimestamp(random_ts)
            date_str = date_obj.strftime("%d/%m/%Y")
            
            data = {
                "Date": date_str, "Categorie": random.choice(categories),
                "Description": f"{random.choice(descriptions)} {i+1}",
                "Montant": round(random.uniform(10.0, 200.0), 2), "ProofPath": None
            }
            save_expense(data)
            if i % 5 == 0: self.app.update_idletasks()

        update_dashboard_kpis(self.app)
        if self.app.is_expenses_tab_initialized:
             from .expenses_tab import refresh_expenses_list
             refresh_expenses_list(self.app)
        messagebox.showinfo("Succès", f"{count} frais ont été générés.")

    def _regenerate_all_invoices_excel(self):
        if not messagebox.askyesno("Confirmation", "Cette opération va lire toutes vos factures et recréer les fichiers Excel.\nContinuer ?"):
            return
        from .data_manager import load_all_data, get_available_years, backup_database, save_to_excel
        import pandas as pd
        self.app._show_status_message("Regénération Excel en cours...")
        self.app.update_idletasks()

        try:
            all_invoices_df = load_all_data()
            if all_invoices_df.empty:
                messagebox.showinfo("Information", "Aucune facture à traiter.")
                return
            available_years = get_available_years()
            for year in available_years: backup_database(year)
            
            for year in available_years:
                excel_path = os.path.join(config.FACTURES_DIR, str(year), f"factures_{year}.xlsx")
                if os.path.exists(excel_path): os.remove(excel_path)

            all_invoices_df = all_invoices_df.where(pd.notnull(all_invoices_df), None)
            invoices_to_save = all_invoices_df.to_dict('records')
            for invoice_data in invoices_to_save: save_to_excel(invoice_data)

            messagebox.showinfo("Succès", "Regénération Excel terminée.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur durant la regénération :\n{e}")

    def _regenerate_all_invoice_pdfs(self):
        if not messagebox.askyesno("Confirmation", "Cette opération va remplacer tous les PDF de factures.\nContinuer ?"):
            return

        all_invoices_df = self.app._load_data_with_cache()
        if all_invoices_df.empty:
            messagebox.showinfo("Information", "Aucune facture à régénérer.")
            return

        invoices_to_process = all_invoices_df.to_dict('records')
        total_invoices = len(invoices_to_process)

        progress_window = ctk.CTkToplevel(self.app)
        progress_window.title("Régénération en cours")
        progress_window.geometry("450x200")
        progress_window.transient(self.app)
        progress_window.grab_set()
        progress_window.protocol("WM_DELETE_WINDOW", lambda: None)

        ctk.CTkLabel(progress_window, text="Régénération des PDF...", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(20, 10))
        progress_bar = ctk.CTkProgressBar(progress_window, width=400)
        progress_bar.pack(pady=10, padx=20)
        progress_bar.set(0)
        progress_label = ctk.CTkLabel(progress_window, text=f"Facture 0 / {total_invoices}")
        progress_label.pack()
        time_label = ctk.CTkLabel(progress_window, text="Calcul du temps...")
        time_label.pack(pady=5)

        thread = threading.Thread(target=self._regenerate_pdfs_worker, args=(invoices_to_process,), daemon=True)
        thread.start()
        self._update_regeneration_progress(progress_window, progress_bar, progress_label, time_label, total_invoices, time.time())

    def _regenerate_pdfs_worker(self, invoices_to_process):
        try:
            import pandas as pd
            from .pdf_generator import generate_pdf
            for i, invoice_data in enumerate(invoices_to_process):
                clean_data = {k: v for k, v in invoice_data.items() if pd.notna(v)}
                if 'Membres_Famille' in clean_data and isinstance(clean_data.get('Membres_Famille'), str):
                    try: clean_data['Membres_Famille'] = ast.literal_eval(clean_data['Membres_Famille'])
                    except: del clean_data['Membres_Famille']
                generate_pdf(clean_data, is_duplicate=False)
                self.regeneration_queue.put(('progress', i + 1))
            self.regeneration_queue.put(('done', len(invoices_to_process)))
        except Exception as e:
            self.regeneration_queue.put(('error', str(e)))

    def _update_regeneration_progress(self, window, bar, p_label, t_label, total, start_time):
        if not window.winfo_exists(): return
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
                    t_label.configure(text=f"Temps restant : {int(mins)} min {int(secs)} sec")
                self.app.after(100, self._update_regeneration_progress, window, bar, p_label, t_label, total, start_time)
            elif message_type == 'done':
                window.destroy()
                messagebox.showinfo("Succès", f"{data} factures régénérées.")
            elif message_type == 'error':
                window.destroy()
                messagebox.showerror("Erreur", f"Erreur : {data}")
        except queue.Empty:
            if window.winfo_exists():
                self.app.after(100, self._update_regeneration_progress, window, bar, p_label, t_label, total, start_time)
