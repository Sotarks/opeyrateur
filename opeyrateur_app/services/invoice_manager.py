import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import threading
from opeyrateur_app.core.data_manager import get_next_sequence_id, save_to_excel, check_duplicate_invoice

class InvoiceManager:
    def __init__(self, app):
        self.app = app
        self.family_member_entries = []
        self._patient_suggestion_job = None # Pour dé-bouncer la recherche
        self.is_saving = False # Flag pour éviter les sauvegardes concurrentes

    def add_family_member(self):
        """Ajoute une ligne de saisie pour un membre de la famille."""
        # Limite à 5 membres supplémentaires (total de 6)
        if len(self.family_member_entries) >= 5:
            return

        member_frame = ctk.CTkFrame(self.app.family_members_container)
        member_frame.pack(fill="x", pady=2, padx=5)
        member_frame.grid_columnconfigure((0, 1), weight=1)

        prenom_entry = ctk.CTkEntry(member_frame, placeholder_text=f"Prénom Membre {len(self.family_member_entries) + 2}")
        prenom_entry.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        nom_entry = ctk.CTkEntry(member_frame, placeholder_text=f"Nom Membre {len(self.family_member_entries) + 2}")
        nom_entry.grid(row=0, column=1, padx=(0, 5), sticky="ew")
        
        entries = (prenom_entry, nom_entry)

        remove_button = ctk.CTkButton(
            member_frame, text="✕", width=30, height=30,
            command=lambda f=member_frame, e=entries: self.remove_family_member(f, e)
        )
        remove_button.grid(row=0, column=2)

        self.family_member_entries.append(entries)

        if len(self.family_member_entries) >= 5:
            self.app.add_member_button.configure(state="disabled")

    def remove_family_member(self, frame_to_destroy, entries_to_remove):
        """Supprime une ligne de saisie de membre de la famille."""
        frame_to_destroy.destroy()
        self.family_member_entries.remove(entries_to_remove)
        self.app.add_member_button.configure(state="normal")

    def toggle_seance_date(self):
        """Active/désactive le champ de date de séance."""
        if self.app.seance_non_lieu_var.get():
            self.app.seance_date.configure(state="normal")
            self.app.seance_date.delete(0, 'end')
            self.app.seance_date.insert(0, "Non-lieu")
            self.app.seance_date.configure(state="readonly")
            self.app.seance_date.unbind("<1>")
        else:
            self.app.seance_date.configure(state="normal")
            self.app.seance_date.delete(0, 'end')
            self.app.seance_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
            self.app.seance_date.configure(state="readonly")
            self.app.seance_date.bind("<1>", lambda event: self.app._open_calendar(self.app.seance_date))

    def toggle_payment_date_field(self, *args):
        """Affiche ou masque le champ de la date de paiement."""
        if self.app.payment_method.get() == "Impayé":
            self.app.payment_date_entry.grid_forget()
            self.app.payment_date_label.grid_forget()
        else:
            self.app.payment_date_label.grid(row=0, column=1, sticky="e", padx=(0, 5))
            self.app.payment_date_entry.grid(row=0, column=2, sticky="ew")

    def update_form(self, prestation_choisie):
        """Met à jour le montant et l'affichage du formulaire selon la prestation."""
        montant = self.app.prestations_prix.get(prestation_choisie)
        self.app.montant.delete(0, 'end')
        if montant is not None:
            self.app.montant.insert(0, f"{montant:.2f}")

        is_child_session = "enfant" in prestation_choisie.lower() or "adolescent" in prestation_choisie.lower()
        is_family_session = "familiale" in prestation_choisie.lower()
        is_couple_session = "couple" in prestation_choisie.lower()
        
        # Masque les cadres optionnels
        for w in [self.app.child_info_frame, self.app.family_frame, self.app.couple_frame, self.app.p1_civility_frame]:
            w.grid_forget()

        if is_child_session:
            self.app.child_info_frame.grid(row=5, column=0, padx=0, pady=10, sticky="ew")
            self.app.p1_civility_frame.grid(row=1, column=0, sticky='w', padx=(10, 5), in_=self.app.client_frame)
        elif is_family_session:
            self.app.family_frame.grid(row=5, column=0, padx=0, pady=10, sticky="ew")
        elif is_couple_session:
            self.app.couple_frame.grid(row=5, column=0, padx=0, pady=10, sticky="ew")

    def _on_patient_search_change(self):
        """Filtre et affiche les suggestions de patients en fonction de la saisie."""
        if self._patient_suggestion_job:
            self.app.after_cancel(self._patient_suggestion_job)
        self._patient_suggestion_job = self.app.after(250, self._perform_patient_search)

    def _perform_patient_search(self):
        """Exécute la recherche de patients et met à jour l'interface."""
        import pandas as pd
        from opeyrateur_app.core.db_manager import search_patients_for_suggestions

        query_prenom = self.app.prenom.get().lower().strip()
        query_nom = self.app.nom.get().lower().strip()

        if len(query_prenom) < 2 and len(query_nom) < 2:
            self.app.patient_suggestion_frame.grid_forget()
            return

        # --- OPTIMISATION : Requête SQL directe en base de données ---
        results = search_patients_for_suggestions(query_prenom=query_prenom, query_nom=query_nom, limit=5)

        for widget in self.app.patient_suggestion_frame.winfo_children():
            widget.destroy()

        if not results:
            self.app.patient_suggestion_frame.grid_forget()
            return

        # Place la boîte de suggestions juste sous le cadre du client
        self.app.patient_suggestion_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 10), in_=self.app.new_invoice_left_panel)
        
        for patient_data in results:
            patient_name = f"{patient_data.get('Prenom', '')} {patient_data.get('Nom', '')}".strip()
            nom_enfant = patient_data.get('Nom_Enfant')
            if nom_enfant and str(nom_enfant).strip() and str(nom_enfant).lower() not in ('nan', '<na>', 'none'):
                patient_name += f" (Enfant: {nom_enfant})"
            
            btn = ctk.CTkButton(
                self.app.patient_suggestion_frame, text=patient_name, anchor="w", fg_color="transparent",
                hover_color=("gray90", "gray30"), command=lambda p=patient_data: self._select_patient(p)
            )
            btn.pack(fill="x", padx=5, pady=2)
            btn.bind("<FocusOut>", lambda e: self._hide_suggestions_on_focus_out())

    def _select_patient(self, patient_data):
        """Remplit le formulaire avec les données du patient sélectionné."""
        import pandas as pd
        self.reset_form(confirm=False)

        self.app.prenom.insert(0, patient_data.get('Prenom', ''))
        self.app.nom.insert(0, patient_data.get('Nom', ''))
        self.app.adresse.insert(0, patient_data.get('Adresse', ''))

        prestation = patient_data.get('Prestation')
        if prestation and prestation in self.app.prestations_prix:
            self.app.prestation.set(prestation)
            self.update_form(prestation)

        if pd.notna(patient_data.get('Nom_Enfant')):
            self.app.enfant_nom.insert(0, patient_data.get('Nom_Enfant', ''))
            self.app.enfant_dob.configure(state="normal")
            self.app.enfant_dob.insert(0, patient_data.get('Naissance_Enfant', ''))
            self.app.enfant_dob.configure(state="readonly")
            if pd.notna(patient_data.get('Prenom2')):
                 self.app.prenom2.insert(0, patient_data.get('Prenom2', ''))
                 self.app.nom2.insert(0, patient_data.get('Nom2', ''))

        self.app.patient_suggestion_frame.grid_forget()
        self.app.payment_method.focus()

    def _hide_suggestions_on_focus_out(self):
        """Masque les suggestions après un court délai pour permettre le clic."""
        def check_focus():
            if not self.app.winfo_exists(): return
            try:
                focused_widget = self.app.focus_get()
                parent = focused_widget
                while parent:
                    if parent == self.app.patient_suggestion_frame: return
                    parent = parent.master if hasattr(parent, 'master') else None
            except Exception:
                pass
            self.app.patient_suggestion_frame.grid_forget()
        self.app.after(150, check_focus)

    def valider(self):
        """Valide le formulaire, sauvegarde les données et génère le PDF."""
        if self.is_saving:
            messagebox.showinfo("Veuillez patienter", "Une facture est déjà en cours de sauvegarde en arrière-plan.")
            return

        # Annuler les recherches/suggestions en cours
        if self._patient_suggestion_job:
            self.app.after_cancel(self._patient_suggestion_job)
            self._patient_suggestion_job = None
        self.app.patient_suggestion_frame.grid_forget()

        try:
            # --- Validation des champs ---
            if not self.app.nom.get() or not self.app.montant.get():
                messagebox.showwarning("Champs requis", "Veuillez remplir les champs Nom et Montant.")
                return
            
            # --- Détermination de la date de référence ---
            seance_date_str = self.app.seance_date.get()
            payment_date_str = self.app.payment_date_entry.get()
            payment_method = self.app.payment_method.get()

            reference_date = datetime.now() # Fallback

            try:
                if seance_date_str and seance_date_str.lower().strip() != 'non-lieu':
                    reference_date = datetime.strptime(seance_date_str, '%d/%m/%Y')
                elif payment_method != "Impayé" and payment_date_str:
                    reference_date = datetime.strptime(payment_date_str, '%d/%m/%Y')
            except ValueError:
                messagebox.showerror("Erreur de date", "Le format de la date est invalide. Utilisez JJ/MM/AAAA.")
                return

            # --- Vérification anti-doublon ---
            check_data = {
                "Date": reference_date.strftime("%d/%m/%Y"),
                "Nom": self.app.nom.get().strip(),
                "Prenom": self.app.prenom.get().strip(),
                "Montant": float(self.app.montant.get())
            }
            
            if check_duplicate_invoice(check_data):
                if not messagebox.askyesno("Doublon détecté", f"Une facture pour {check_data['Prenom']} {check_data['Nom']} d'un montant de {check_data['Montant']} € existe déjà à la date du {check_data['Date']}.\n\nVoulez-vous vraiment créer cette facture ?"):
                    return

            # --- Préparation des données ---
            invoice_year = reference_date.year
            next_seq = get_next_sequence_id(invoice_year)
            sequence_id = f"{next_seq:04d}"
            facture_id = f"{reference_date.strftime('%Y%m%d')}-{sequence_id}"
            
            data = {
                "ID": facture_id,
                "Date": reference_date.strftime("%d/%m/%Y"),
                "Nom": self.app.nom.get().strip().upper(),
                "Prenom": self.app.prenom.get().strip(),
                "Adresse": self.app.adresse.get().strip(),
                "Prestation": self.app.prestation.get(),
                "Date_Seance": self.app.seance_date.get(),
                "Montant": float(self.app.montant.get()),
                "Methode_Paiement": self.app.payment_method.get(),
                "Note": self.app.personal_note.get().strip(),
                "SequenceID": sequence_id
            }

            if data["Methode_Paiement"] != "Impayé":
                if self.app.payment_date_entry.get():
                    data["Date_Paiement"] = self.app.payment_date_entry.get()

            is_child_session = "enfant" in data["Prestation"].lower() or "adolescent" in data["Prestation"].lower()
            is_family_session = "familiale" in data["Prestation"].lower()
            is_couple_session = "couple" in data["Prestation"].lower()

            if is_child_session:
                if not self.app.enfant_nom.get() or not self.app.enfant_dob.get():
                    messagebox.showwarning("Champs requis", "Veuillez renseigner le nom et la date de naissance de l'enfant.")
                    return
                data["Attention_de"] = self.app.attention_var.get()
                data["Nom_Enfant"] = self.app.enfant_nom.get().strip()
                data["Naissance_Enfant"] = self.app.enfant_dob.get().strip()
                
                prenom2 = self.app.prenom2.get().strip()
                nom2 = self.app.nom2.get().strip().upper()
                if prenom2 and nom2:
                    data["Attention_de2"] = self.app.attention_var2.get()
                    data["Prenom2"], data["Nom2"] = prenom2, nom2
            elif is_family_session:
                family_members = []
                if data["Prenom"] and data["Nom"]:
                    family_members.append(f"{data['Prenom']} {data['Nom']}")
                
                for prenom_entry, nom_entry in self.family_member_entries:
                    prenom = prenom_entry.get().strip()
                    nom = nom_entry.get().strip().upper()
                    if prenom or nom:
                        family_members.append(f"{prenom} {nom}".strip())
                data["Membres_Famille"] = family_members
            elif is_couple_session:
                prenom2 = self.app.prenom2_couple.get().strip()
                nom2 = self.app.nom2_couple.get().strip().upper()
                if prenom2 and nom2:
                    data["Prenom2"] = prenom2
                    data["Nom2"] = nom2

            # --- Logique de sauvegarde asynchrone ---
            self.is_saving = True
            self.app.btn.configure(state="disabled", text="Sauvegarde en cours...")
            self.app.update_idletasks()

            # Lancer la sauvegarde et la génération en arrière-plan
            thread = threading.Thread(target=self._save_worker, args=(data,), daemon=True)
            thread.start()

        except ValueError:
            messagebox.showerror("Erreur de format", "Le montant doit être un nombre valide.")
            self._on_save_complete(False, "") # Réactive le bouton en cas d'erreur
        except Exception as e:
            messagebox.showerror("Erreur inattendue", f"Une erreur est survenue : {e}")
            self._on_save_complete(False, "") # Réactive le bouton en cas d'erreur

    def _save_worker(self, data):
        """Worker thread pour la sauvegarde Excel afin de ne pas bloquer l'UI."""
        try:
            from opeyrateur_app.services.pdf_generator import generate_pdf
            pdf_file = generate_pdf(data)
            save_to_excel(data)
            self.app._invalidate_data_cache()
            self.app.after(0, self._on_save_complete, True, "Facture enregistrée dans le registre.", pdf_file, data)
        except Exception as e:
            error_message = f"Erreur lors de la sauvegarde : {e}"
            print(error_message)
            self.app.after(0, self._on_save_complete, False, error_message, None, None)

    def _on_save_complete(self, success, message, pdf_file=None, data=None):
        """Callback exécuté sur le thread principal après la fin de la sauvegarde."""
        self.is_saving = False
        self.app.btn.configure(state="normal", text="VALIDER LA FACTURE")
        if success:
            self.app._show_status_message(message, duration=5000)
            self.app._update_dashboard_kpis() # Met à jour les stats
            self.app.invoice_actions.show_success_dialog(pdf_file, data)
            self.reset_form(confirm=False)
        elif message: # Affiche une erreur seulement si un message a été passé
            messagebox.showerror("Erreur de Sauvegarde", f"La facturation a échoué.\n\n{message}")

    def reset_form(self, confirm=True):
        """Vide tous les champs du formulaire."""
        if confirm and not messagebox.askyesno("Confirmation", "Voulez-vous vraiment vider tout le formulaire ?"):
            return
        else:
            self.app.nom.delete(0, 'end')
            self.app.prenom.delete(0, 'end')
            self.app.adresse.delete(0, 'end')
            self.app.montant.delete(0, 'end')
            self.app.personal_note.delete(0, 'end')
            
            # Reset champs spécifiques
            self.app.enfant_nom.delete(0, 'end')
            self.app.enfant_dob.configure(state="normal")
            self.app.enfant_dob.delete(0, 'end')
            self.app.enfant_dob.configure(state="readonly")
            
            self.app.prenom2.delete(0, 'end')
            self.app.nom2.delete(0, 'end')
            self.app.prenom2_couple.delete(0, 'end')
            self.app.nom2_couple.delete(0, 'end')

            # Vide les membres de la famille
            for widget in self.app.family_members_container.winfo_children():
                widget.destroy()
            self.family_member_entries.clear()
            self.app.add_member_button.configure(state="normal")
            
            # Reset dates
            self.app.payment_date_entry.configure(state="normal")
            self.app.payment_date_entry.delete(0, 'end')
            self.app.payment_date_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
            self.app.payment_date_entry.configure(state="readonly")

            self.app.seance_date.configure(state="normal")
            self.app.seance_date.delete(0, 'end')
            self.app.seance_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
            self.app.seance_date.configure(state="readonly")
            self.app.seance_non_lieu_var.set(False)
            self.toggle_seance_date()
