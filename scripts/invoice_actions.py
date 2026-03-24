import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
import os
import ast
from datetime import datetime
import webbrowser
import threading

from . import config
from .data_manager import get_invoice_path, delete_invoice, MONTHS_FR, backup_database, save_to_excel, mark_invoices_as_sent

class InvoiceActions:
    def __init__(self, app):
        self.app = app

    def show_invoice_context_menu(self, event, invoice_data):
        """Affiche le menu contextuel pour une facture."""
        menu = tk.Menu(self.app, tearoff=0)
        menu.add_command(label="Visualiser le PDF", command=lambda: self.view_invoice_pdf(invoice_data))
        menu.add_command(label="Modifier la facture", command=lambda: self.open_modify_window(invoice_data))
        menu.add_command(label="Envoyer par Email", command=lambda: self._prompt_send_email(invoice_data=invoice_data))
        menu.add_command(label="Ouvrir le dossier", command=lambda: self.open_invoice_folder(invoice_data))
        menu.add_command(label="Ouvrir le PDF (externe)", command=lambda: self.open_invoice_pdf_externally(invoice_data))
        menu.add_separator()
        menu.add_command(label="Supprimer la facture", command=lambda: self._confirm_delete_invoice(invoice_data))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _confirm_delete_invoice(self, invoice_data):
        if messagebox.askyesno("Confirmation", f"Voulez-vous vraiment supprimer la facture {invoice_data['ID']} ?"):
            if delete_invoice(invoice_data):
                self.app._invalidate_data_cache()
                self.app._show_status_message("Facture supprimée.")
                self.app._apply_filters_and_search()
            else:
                messagebox.showerror("Erreur", "Impossible de supprimer la facture.")

    def open_modify_window(self, invoice_data):
        """Ouvre une fenêtre pour modifier le statut d'une facture."""
        win = ctk.CTkToplevel(self.app)
        win.title("Modifier la Facture")
        win.geometry("500x650")
        win.resizable(True, True)
        win.transient(self.app)
        win.grab_set()

        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(0, weight=1)

        scroll_frame = ctk.CTkScrollableFrame(win, label_text=f"Modification de la facture #{invoice_data.get('ID', '')}", label_font=self.app.font_large)
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scroll_frame.grid_columnconfigure(0, weight=1)

        # --- Carte 1: Informations Patient ---
        patient_card = ctk.CTkFrame(scroll_frame)
        patient_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        patient_card.grid_columnconfigure((0, 1), weight=1)
        
        ctk.CTkLabel(patient_card, text="Patient", font=self.app.font_bold).grid(row=0, column=0, columnspan=2, padx=15, pady=(10, 5), sticky="w")
        
        ctk.CTkLabel(patient_card, text="Prénom :").grid(row=1, column=0, padx=15, pady=(0, 5), sticky="w")
        prenom_entry = ctk.CTkEntry(patient_card)
        prenom_entry.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="ew")
        prenom_entry.insert(0, invoice_data.get('Prenom', ''))

        ctk.CTkLabel(patient_card, text="Nom :").grid(row=1, column=1, padx=15, pady=(0, 5), sticky="w")
        nom_entry = ctk.CTkEntry(patient_card)
        nom_entry.grid(row=2, column=1, padx=15, pady=(0, 15), sticky="ew")
        nom_entry.insert(0, invoice_data.get('Nom', ''))

        # --- Carte 2: Identification & Dates ---
        dates_card = ctk.CTkFrame(scroll_frame)
        dates_card.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        dates_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(dates_card, text="Identification & Dates", font=self.app.font_bold).grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")

        ctk.CTkLabel(dates_card, text="ID Facture :").grid(row=1, column=0, padx=15, pady=(0, 5), sticky="w")
        id_entry = ctk.CTkEntry(dates_card)
        id_entry.grid(row=2, column=0, padx=15, pady=(0, 10), sticky="ew")
        id_entry.insert(0, invoice_data['ID'])

        ctk.CTkLabel(dates_card, text="Date de facturation :").grid(row=3, column=0, padx=15, pady=(0, 5), sticky="w")
        creation_date_entry = ctk.CTkEntry(dates_card)
        creation_date_entry.grid(row=4, column=0, padx=15, pady=(0, 10), sticky="ew")
        creation_date_entry.insert(0, invoice_data.get('Date', ''))
        creation_date_entry.bind("<1>", lambda e: self.app._open_calendar(creation_date_entry, make_readonly=False))

        ctk.CTkLabel(dates_card, text="Date de séance :").grid(row=5, column=0, padx=15, pady=(0, 5), sticky="w")
        seance_date_entry = ctk.CTkEntry(dates_card)
        seance_date_entry.grid(row=6, column=0, padx=15, pady=(0, 15), sticky="ew")
        seance_date_entry.insert(0, invoice_data.get('Date_Seance', ''))
        seance_date_entry.bind("<1>", lambda e: self.app._open_calendar(seance_date_entry, make_readonly=False))

        # --- Carte 3: Informations Enfant (si applicable) ---
        is_child = "enfant" in invoice_data.get("Prestation", "").lower() or "adolescent" in invoice_data.get("Prestation", "").lower()
        child_dob_entry = None
        child_name_entry = None
        if is_child:
            child_card = ctk.CTkFrame(scroll_frame)
            child_card.grid(row=2, column=0, sticky="ew", pady=(0, 10))
            child_card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(child_card, text="Informations Enfant", font=self.app.font_bold).grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")
            
            ctk.CTkLabel(child_card, text="Nom de l'enfant :").grid(row=1, column=0, padx=15, pady=(0, 5), sticky="w")
            child_name_entry = ctk.CTkEntry(child_card)
            child_name_entry.grid(row=2, column=0, padx=15, pady=(0, 10), sticky="ew")
            child_name_val = str(invoice_data.get('Nom_Enfant', ''))
            if child_name_val.lower() == 'nan': child_name_val = ''
            child_name_entry.insert(0, child_name_val)

            ctk.CTkLabel(child_card, text="Date de naissance de l'enfant :").grid(row=3, column=0, padx=15, pady=(0, 5), sticky="w")
            child_dob_entry = ctk.CTkEntry(child_card)
            child_dob_entry.grid(row=4, column=0, padx=15, pady=(0, 15), sticky="ew")
            child_dob_entry.insert(0, invoice_data.get('Naissance_Enfant', ''))
            child_dob_entry.bind("<1>", lambda e: self.app._open_calendar(child_dob_entry, make_readonly=False))

        # --- Carte 4: Statut du Paiement ---
        payment_card = ctk.CTkFrame(scroll_frame)
        payment_card.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        payment_card.grid_columnconfigure((0, 1), weight=1)
        
        ctk.CTkLabel(payment_card, text="Statut du Paiement", font=self.app.font_bold).grid(row=0, column=0, columnspan=2, padx=15, pady=(10, 5), sticky="w")
        ctk.CTkLabel(payment_card, text=f"Statut actuel : {invoice_data['Methode_Paiement']}", font=self.app.font_regular).grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 10), sticky="w")

        payment_date_label = ctk.CTkLabel(payment_card, text="Date de paiement :")
        payment_date_entry = ctk.CTkEntry(payment_card)
        
        def toggle_payment_date(status):
            if status == "Impayé":
                payment_date_label.grid_remove()
                payment_date_entry.grid_remove()
            else:
                payment_date_label.grid(row=2, column=1, padx=15, pady=(0, 5), sticky="w")
                payment_date_entry.grid(row=3, column=1, padx=15, pady=(0, 15), sticky="ew")

        ctk.CTkLabel(payment_card, text="Nouveau statut :").grid(row=2, column=0, padx=15, pady=(0, 5), sticky="w")
        new_status_var = ctk.CTkOptionMenu(payment_card, values=["Virement", "Espèce", "Chèque", "Impayé"], command=toggle_payment_date)
        new_status_var.grid(row=3, column=0, padx=15, pady=(0, 15), sticky="ew")
        new_status_var.set(invoice_data.get('Methode_Paiement', 'Virement'))

        payment_date_to_show = invoice_data.get('Date_Paiement') or datetime.now().strftime("%d/%m/%Y")
        payment_date_entry.insert(0, payment_date_to_show)
        payment_date_entry.bind("<1>", lambda e: self.app._open_calendar(payment_date_entry))
        toggle_payment_date(new_status_var.get())

        # --- Option de régénération ---
        regen_pdf_var = ctk.CTkCheckBox(scroll_frame, text="Régénérer le PDF (recommandé si des informations ont changé)", font=self.app.font_regular)
        regen_pdf_var.grid(row=4, column=0, padx=15, pady=10, sticky="w")
        regen_pdf_var.select()

        def on_update(open_after=False):
            dob = child_dob_entry.get() if child_dob_entry else None
            child_name = child_name_entry.get().strip() if child_name_entry else None
            new_nom = nom_entry.get().strip()
            new_prenom = prenom_entry.get().strip()
            new_id = id_entry.get().strip()
            new_creation_date = creation_date_entry.get().strip()
            
            status = new_status_var.get()
            payment_date = payment_date_entry.get() if status != 'Impayé' else ''
            
            self._update_invoice_status(invoice_data, status, payment_date, seance_date_entry.get(), dob, regen_pdf_var.get(), win, new_nom, new_prenom, new_id, new_creation_date, open_pdf_after=open_after, new_child_name=child_name)

        # --- Boutons d'action en bas ---
        btn_frame = ctk.CTkFrame(win)
        btn_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        btn_frame.grid_columnconfigure((0, 1), weight=1)
        
        ctk.CTkButton(btn_frame, text="Sauvegarder et Fermer", font=self.app.font_button, command=lambda: on_update(False), height=40).grid(row=0, column=0, padx=(0, 5), sticky="ew")
        ctk.CTkButton(btn_frame, text="Sauvegarder et Ouvrir", font=self.app.font_button, command=lambda: on_update(True), height=40).grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def _update_invoice_status(self, invoice_data, new_status, new_payment_date, new_seance_date, new_child_dob, regen_pdf, window, new_nom=None, new_prenom=None, new_id=None, new_creation_date=None, open_pdf_after=False, new_child_name=None):
        try:
            import pandas as pd
            
            # Gestion du changement de date de création (nécessite suppression/recréation pour gérer les fichiers Excel annuels)
            old_date = invoice_data.get('Date')
            if new_creation_date and new_creation_date != old_date:
                new_data = invoice_data.copy()
                new_data.update({
                    'Date': new_creation_date,
                    'Methode_Paiement': new_status,
                    'Date_Paiement': new_payment_date,
                    'Date_Seance': new_seance_date,
                    'Nom': new_nom if new_nom else invoice_data.get('Nom'),
                    'Prenom': new_prenom if new_prenom else invoice_data.get('Prenom'),
                })
                if new_child_dob: new_data['Naissance_Enfant'] = new_child_dob
                if new_child_name: new_data['Nom_Enfant'] = new_child_name
                
                # --- Mise à jour intelligente de l'ID ---
                new_date_obj = datetime.strptime(new_creation_date, '%d/%m/%Y')
                new_date_prefix = new_date_obj.strftime('%Y%m%d')
                current_id_input = new_id if new_id else invoice_data.get('ID')

                # Si l'ID actuel ne correspond pas à la nouvelle date, on le régénère
                if not current_id_input.startswith(new_date_prefix):
                    # Gestion du SequenceID
                    old_date_obj = datetime.strptime(old_date, '%d/%m/%Y')
                    
                    if old_date_obj.year != new_date_obj.year:
                        # Changement d'année : nouvelle séquence obligatoire
                        from .data_manager import get_next_sequence_id
                        seq_int = get_next_sequence_id(new_date_obj.year)
                        seq_str = f"{seq_int:04d}"
                    else:
                        # Même année : on conserve la séquence existante
                        seq_val = invoice_data.get('SequenceID')
                        if not seq_val or str(seq_val) == 'nan':
                            seq_val = current_id_input.split('-')[-1] if '-' in current_id_input else "0001"
                        try:
                            seq_str = f"{int(float(seq_val)):04d}"
                        except:
                            seq_str = str(seq_val)

                    new_data['ID'] = f"{new_date_prefix}-{seq_str}"
                    new_data['SequenceID'] = seq_str
                else:
                    # L'utilisateur a mis à jour l'ID manuellement ou il correspond déjà
                    new_data['ID'] = current_id_input
                    if '-' in current_id_input:
                         new_data['SequenceID'] = current_id_input.split('-')[-1]

                if delete_invoice(invoice_data):
                    save_to_excel(new_data)
                    
                    if regen_pdf:
                        self._regenerate_pdf_and_cleanup(new_data, invoice_data)

                    self.app._invalidate_data_cache()
                    window.destroy()
                    self.app._apply_filters_and_search()
                    if open_pdf_after:
                        self.view_invoice_pdf(new_data)
                    else:
                        messagebox.showinfo("Succès", "Facture mise à jour (Date modifiée).")
                    return
                else:
                    messagebox.showerror("Erreur", "Impossible de supprimer l'ancienne facture pour la mise à jour.")
                    return

            # Mise à jour classique (même date de création)
            updated_data = invoice_data.copy()
            updated_data['Methode_Paiement'] = new_status
            updated_data['Date_Paiement'] = new_payment_date
            updated_data['Date_Seance'] = new_seance_date
            if new_child_dob: updated_data['Naissance_Enfant'] = new_child_dob
            if new_child_name: updated_data['Nom_Enfant'] = new_child_name
            if new_nom: updated_data['Nom'] = new_nom
            if new_prenom: updated_data['Prenom'] = new_prenom
            
            if new_id and new_id != invoice_data['ID']:
                updated_data['ID'] = new_id
                # Mise à jour intelligente du SequenceID si le format est standard (YYYYMMDD-XXXX)
                if '-' in new_id:
                    parts = new_id.split('-')
                    if len(parts) >= 2 and parts[-1].isdigit():
                        updated_data['SequenceID'] = parts[-1]
                
                # Si l'ID a changé, on supprime l'ancienne
                delete_invoice(invoice_data)

            save_to_excel(updated_data)

            if regen_pdf:
                self._regenerate_pdf_and_cleanup(updated_data, invoice_data)

            self.app._invalidate_data_cache()
            window.destroy()
            self.app._apply_filters_and_search()
            
            if open_pdf_after:
                self.view_invoice_pdf(updated_data)
            else:
                messagebox.showinfo("Succès", "Facture mise à jour.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur : {e}")

    def _regenerate_pdf_and_cleanup(self, new_data, old_data):
        """Génère le nouveau PDF et supprime l'ancien si le chemin a changé."""
        import pandas as pd
        clean_data = {}
        for k, v in new_data.items():
            if isinstance(v, (list, tuple, dict)):
                if v:
                    clean_data[k] = v
            else:
                try:
                    if pd.notna(v):
                        val_str = str(v).strip()
                        if val_str.lower() not in ('nan', '<na>', 'nat', ''):
                            clean_data[k] = v
                except Exception:
                    if v:
                        clean_data[k] = v
                        
        if 'Membres_Famille' in clean_data and isinstance(clean_data.get('Membres_Famille'), str):
            try: clean_data['Membres_Famille'] = ast.literal_eval(clean_data['Membres_Famille'])
            except: del clean_data['Membres_Famille']
            
        from .pdf_generator import generate_pdf
        new_path = generate_pdf(clean_data, is_duplicate=False)
        
        old_path = get_invoice_path(old_data)
        if os.path.abspath(old_path) != os.path.abspath(new_path) and os.path.exists(old_path):
            try: os.remove(old_path)
            except Exception as e: print(f"Erreur suppression ancien PDF: {e}")

    def send_grouped_email(self, selected_vars):
        """Prépare l'envoi groupé pour les factures sélectionnées."""
        selected_invoices = []
        for inv_id, (var, data) in selected_vars.items():
            if var.get():
                selected_invoices.append(data)
        
        if not selected_invoices:
            messagebox.showinfo("Info", "Veuillez sélectionner au moins une facture.")
            return
            
        self._prompt_send_email(invoice_data_list=selected_invoices)

    def _prompt_send_email(self, invoice_data=None, pdf_path=None, email_subject=None, invoice_data_list=None):
        """Ouvre une boîte de dialogue pour envoyer la facture par email."""
        pdf_paths = []
        target_invoices = []

        if invoice_data_list:
            target_invoices = invoice_data_list
            for inv in invoice_data_list:
                path = get_invoice_path(inv)
                if path and os.path.exists(path):
                    pdf_paths.append(path)
        elif invoice_data:
            target_invoices = [invoice_data]
            path = pdf_path if pdf_path else get_invoice_path(invoice_data)
            if path and os.path.exists(path): pdf_paths.append(path)
        
        if not pdf_paths:
            messagebox.showerror("Erreur", "Aucun fichier PDF valide trouvé.")
            return

        # Dialog to ask for email
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Envoyer par Email")
        dialog.geometry("500x450")
        dialog.transient(self.app)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Adresse email du destinataire :").pack(pady=(20, 5))
        email_entry = ctk.CTkEntry(dialog, width=400)
        email_entry.pack(pady=5)
        email_entry.focus()
        
        ctk.CTkLabel(dialog, text="Message :").pack(pady=(10, 5))
        body_entry = ctk.CTkTextbox(dialog, width=400, height=150)
        body_entry.pack(pady=5)
        
        # Détermine le sujet et le corps par défaut
        if len(pdf_paths) > 1:
            default_subject = f"Vos documents ({len(pdf_paths)})"
            default_body = "Bonjour,\n\nVeuillez trouver ci-joint vos documents.\n\nCordialement,\nAlaïs Peyrat"
        else:
            filename = os.path.basename(pdf_paths[0])
            is_attestation = "ATTESTATION" in filename.upper()
            
            if is_attestation:
                default_subject = f"Attestation - {filename}"
                default_body = "Bonjour,\n\nVeuillez trouver ci-joint votre attestation.\n\nCordialement,\nAlaïs Peyrat"
            else:
                default_subject = f"Facture - {filename}"
                default_body = "Bonjour,\n\nVeuillez trouver ci-joint votre facture.\n\nCordialement,\nAlaïs Peyrat"

        if email_subject: default_subject = email_subject

        body_entry.insert("1.0", default_body)
        
        def send():
            recipient = email_entry.get().strip()
            body_text = body_entry.get("1.0", "end-1c")
            if not recipient: return
            
            dialog.destroy()
            self.app._show_status_message("Envoi de l'email en cours...")
            
            import scripts.email_manager as email_manager
            subject = default_subject
            
            def _send_thread():
                success, msg = email_manager.send_email_with_attachments(recipient, subject, body_text, pdf_paths)
                
                def on_complete():
                    if success:
                        mark_invoices_as_sent(target_invoices)
                        self.app._invalidate_data_cache()
                        self.app._apply_filters_and_search() # Rafraîchir pour voir la date d'envoi
                        messagebox.showinfo("Email", msg)
                    else:
                        messagebox.showerror("Erreur Email", msg)
                
                self.app.after(0, on_complete)
                
            threading.Thread(target=_send_thread, daemon=True).start()

        ctk.CTkButton(dialog, text="Envoyer", command=send).pack(pady=20)

    def show_success_dialog(self, pdf_path, invoice_data=None):
        """Affiche une boîte de dialogue de succès."""
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Succès")
        dialog.geometry("400x500")
        dialog.transient(self.app)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Facture générée avec succès !", font=self.app.font_large).pack(pady=(20, 15))
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=5, padx=50, fill="both", expand=True)

        def open_pdf():
            dialog.destroy()
            from .pdf_viewer import PDFViewer
            PDFViewer(self.app, pdf_path)

        ctk.CTkButton(btn_frame, text="📂  Ouvrir l'emplacement", command=lambda: os.startfile(os.path.dirname(pdf_path)), fg_color="#34D399", hover_color="#10B981", height=40, font=self.app.font_button).pack(pady=8, fill="x")
        ctk.CTkButton(btn_frame, text="📄  Visualiser le PDF", command=open_pdf, height=40, font=self.app.font_button).pack(pady=8, fill="x")
        ctk.CTkButton(btn_frame, text="🖨️  Imprimer", command=lambda: os.startfile(pdf_path, "print"), fg_color="transparent", border_width=1, text_color=("#1E1E1E", "#E0E0E0"), height=40, font=self.app.font_button).pack(pady=8, fill="x")
        ctk.CTkButton(btn_frame, text="✉️  Envoyer par Email", command=lambda: self._prompt_send_email(pdf_path=pdf_path), fg_color="#3498db", hover_color="#2980b9", height=40, font=self.app.font_button).pack(pady=8, fill="x")
        ctk.CTkButton(btn_frame, text="📅  Ouvrir Doctolib", command=lambda: webbrowser.open("https://pro.doctolib.fr/patient_messaging"), fg_color="transparent", border_width=1, text_color=("#1E1E1E", "#E0E0E0"), height=40, font=self.app.font_button).pack(pady=8, fill="x")
        
        if invoice_data:
            ctk.CTkButton(btn_frame, text="❌  Annuler la facture", command=lambda: self._cancel_last_invoice(dialog, invoice_data), fg_color="#e74c3c", hover_color="#c0392b", height=40, font=self.app.font_button).pack(pady=8, fill="x")

        ctk.CTkButton(dialog, text="Fermer", command=dialog.destroy, fg_color="gray50", height=40, font=self.app.font_button).pack(pady=(10, 20), padx=50, fill="x")

    def _cancel_last_invoice(self, dialog, invoice_data):
        """Annule (supprime) la facture qui vient d'être créée."""
        if messagebox.askyesno("Annulation", f"Voulez-vous vraiment annuler et supprimer la facture {invoice_data['ID']} ?\n\nLe fichier PDF et l'entrée Excel seront supprimés."):
            if delete_invoice(invoice_data):
                # Suppression du PDF
                pdf_path = get_invoice_path(invoice_data)
                if os.path.exists(pdf_path):
                    try: os.remove(pdf_path)
                    except Exception as e: print(f"Erreur suppression PDF: {e}")

                self.app._invalidate_data_cache()
                dialog.destroy()
                messagebox.showinfo("Succès", "La facture a été annulée.")
                
                if hasattr(self.app, '_update_dashboard_kpis'):
                    self.app._update_dashboard_kpis()
            else:
                messagebox.showerror("Erreur", "Impossible de supprimer la facture du registre.")

    def view_invoice_pdf(self, invoice_data):
        """Ouvre le visualiseur de PDF interne."""
        pdf_path = get_invoice_path(invoice_data)
        if not os.path.exists(pdf_path):
            messagebox.showwarning("Fichier introuvable", f"Le fichier PDF n'a pas été trouvé:\n{pdf_path}")
            return
        from .pdf_viewer import PDFViewer
        PDFViewer(self.app, pdf_path)

    def open_invoice_folder(self, invoice_data):
        """Ouvre le dossier contenant le PDF de la facture."""
        folder_path = get_invoice_path(invoice_data, get_folder=True)
        if not os.path.isdir(folder_path):
            messagebox.showwarning("Dossier introuvable", f"Le dossier de la facture n'a pas été trouvé:\n{folder_path}")
            return
        try:
            os.startfile(folder_path)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le dossier:\n{e}")

    def open_invoice_pdf_externally(self, invoice_data):
        """Ouvre le fichier PDF de la facture avec le lecteur par défaut."""
        pdf_path = get_invoice_path(invoice_data)
        if not os.path.exists(pdf_path):
            messagebox.showwarning("Fichier introuvable", f"Le fichier PDF n'a pas été trouvé:\n{pdf_path}")
            return
        try:
            os.startfile(pdf_path)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le PDF:\n{e}")
