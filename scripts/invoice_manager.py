import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from .data_manager import get_yearly_invoice_count, save_to_excel
from .pdf_generator import generate_pdf

class InvoiceManager:
    def __init__(self, app):
        self.app = app
        self.family_member_entries = []

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
            self.app.payment_date_label.grid(row=0, column=1, sticky="w")
            self.app.payment_date_entry.grid(row=1, column=1, pady=5, sticky="ew", padx=(5, 0))

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
        self.app.child_info_frame.grid_forget()
        self.app.family_frame.grid_forget()
        self.app.couple_frame.grid_forget()
        self.app.p1_civility_frame.grid_forget()

        if is_child_session:
            self.app.child_info_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
            self.app.p1_civility_frame.grid(row=1, column=0, sticky='w', padx=(10, 5))
            self.app.prenom.configure(placeholder_text="Prénom Parent 1")
            self.app.nom.configure(placeholder_text="Nom Parent 1")
        elif is_family_session:
            self.app.family_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
            self.app.prenom.configure(placeholder_text="Prénom Membre 1")
            self.app.nom.configure(placeholder_text="Nom Membre 1")
        elif is_couple_session:
            self.app.couple_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
            self.app.prenom.configure(placeholder_text="Prénom Partenaire 1")
            self.app.nom.configure(placeholder_text="Nom Partenaire 1")
        else:
            # Cas par défaut
            self.app.prenom.configure(placeholder_text="Prénom Patient")
            self.app.nom.configure(placeholder_text="Nom Patient")

    def valider(self):
        """Valide le formulaire, sauvegarde les données et génère le PDF."""
        try:
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

            invoice_year = reference_date.year
            invoice_count_this_year = get_yearly_invoice_count(invoice_year)
            sequence_id = f"{invoice_count_this_year + 1:04d}"
            facture_id = f"{reference_date.strftime('%Y%m%d')}-{sequence_id}"
            
            data = {
                "ID": facture_id,
                "Date": reference_date.strftime("%d/%m/%Y"),
                "Nom": self.app.nom.get().strip(),
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
                nom2 = self.app.nom2.get().strip()
                if prenom2 and nom2:
                    data["Attention_de2"] = self.app.attention_var2.get()
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
                prenom2 = self.app.prenom2_couple.get().strip()
                nom2 = self.app.nom2_couple.get().strip()
                if prenom2 and nom2:
                    data["Prenom2"] = prenom2
                    data["Nom2"] = nom2

            self.app._invalidate_data_cache()
            save_to_excel(data)
            pdf_file = generate_pdf(data)
            self.app.invoice_actions.show_success_dialog(pdf_file)
            
            # Reset form
            self.app.nom.delete(0, 'end')
            self.app.prenom.delete(0, 'end')
            self.app.adresse.delete(0, 'end')
            if is_child_session:
                self.app.enfant_nom.delete(0, 'end')
                self.app.enfant_dob.delete(0, 'end')
                self.app.prenom2.delete(0, 'end')
                self.app.nom2.delete(0, 'end')
            elif is_family_session:
                for widget in self.app.family_members_container.winfo_children():
                    widget.destroy()
                self.family_member_entries.clear()
                self.app.add_member_button.configure(state="normal")
            elif is_couple_session:
                self.app.prenom2_couple.delete(0, 'end')
                self.app.nom2_couple.delete(0, 'end')
            
            self.app.personal_note.delete(0, 'end')
        except ValueError:
            messagebox.showerror("Erreur de format", "Le montant doit être un nombre valide.")
        except Exception as e:
            messagebox.showerror("Erreur inattendue", f"Une erreur est survenue : {e}")
