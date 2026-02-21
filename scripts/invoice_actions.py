import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
import os
import ast
from datetime import datetime
import webbrowser

from . import config
from .data_manager import get_invoice_path, delete_invoice, MONTHS_FR, backup_database

class InvoiceActions:
    def __init__(self, app):
        self.app = app

    def show_invoice_context_menu(self, event, invoice_data):
        """Affiche le menu contextuel pour une facture."""
        menu = tk.Menu(self.app, tearoff=0)
        menu.add_command(label="Visualiser le PDF", command=lambda: self.view_invoice_pdf(invoice_data))
        menu.add_command(label="Modifier la facture", command=lambda: self.open_modify_window(invoice_data))
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
        is_child = "enfant" in invoice_data.get("Prestation", "").lower() or "adolescent" in invoice_data.get("Prestation", "").lower()
        height = 620 if is_child else 520

        win = ctk.CTkToplevel(self.app)
        win.title("Modifier la Facture")
        win.geometry(f"400x{height}")
        win.transient(self.app)
        win.grab_set()

        info_frame = ctk.CTkFrame(win, fg_color="transparent")
        info_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(info_frame, text=f"Facture: {invoice_data['ID']}", font=self.app.font_regular).pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"Patient: {invoice_data.get('Prenom', '')} {invoice_data.get('Nom', '')}", font=self.app.font_regular).pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"Date séance: {invoice_data.get('Date_Seance', 'N/A')}", font=self.app.font_regular).pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"Statut: {invoice_data['Methode_Paiement']}", font=self.app.font_bold).pack(anchor="w", pady=(10,0))

        update_frame = ctk.CTkFrame(win)
        update_frame.pack(pady=10, padx=10, fill="x")

        child_dob_entry = None
        if is_child:
            ctk.CTkLabel(update_frame, text="Date de naissance de l'enfant :").pack(pady=(10, 5))
            child_dob_entry = ctk.CTkEntry(update_frame, placeholder_text="JJ/MM/AAAA")
            child_dob_entry.pack(fill="x", padx=5)
            child_dob_entry.insert(0, invoice_data.get('Naissance_Enfant', ''))
            child_dob_entry.bind("<1>", lambda e: self.app._open_calendar(child_dob_entry, make_readonly=False))

        ctk.CTkLabel(update_frame, text="Nouvelle date de séance :").pack(pady=(10, 5))
        seance_date_entry = ctk.CTkEntry(update_frame, placeholder_text="JJ/MM/AAAA")
        seance_date_entry.pack(fill="x", padx=5)
        seance_date_entry.insert(0, invoice_data.get('Date_Seance', ''))
        seance_date_entry.bind("<1>", lambda e: self.app._open_calendar(seance_date_entry, make_readonly=False))

        ctk.CTkLabel(update_frame, text="Nouveau statut :").pack(pady=(10, 5))
        new_status_var = ctk.CTkOptionMenu(update_frame, values=["Virement", "Espèce", "Chèque"])
        new_status_var.pack(pady=5)
        new_status_var.set("Virement")

        ctk.CTkLabel(update_frame, text="Date de paiement :").pack(pady=(10, 5))
        payment_date_entry = ctk.CTkEntry(update_frame, placeholder_text="JJ/MM/AAAA")
        payment_date_entry.pack(pady=5)
        payment_date_entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
        payment_date_entry.bind("<1>", lambda e: self.app._open_calendar(payment_date_entry))

        regen_pdf_var = ctk.CTkCheckBox(update_frame, text="Régénérer le PDF", font=self.app.font_regular)
        regen_pdf_var.pack(pady=10)
        regen_pdf_var.select()

        def on_update():
            dob = child_dob_entry.get() if child_dob_entry else None
            self._update_invoice_status(invoice_data, new_status_var.get(), payment_date_entry.get(), seance_date_entry.get(), dob, regen_pdf_var.get(), win)

        ctk.CTkButton(win, text="Mettre à jour", font=self.app.font_button, command=on_update).pack(pady=20)

    def _update_invoice_status(self, invoice_data, new_status, new_payment_date, new_seance_date, new_child_dob, regen_pdf, window):
        try:
            import pandas as pd
            invoice_date = datetime.strptime(invoice_data.get('Date'), '%d/%m/%Y')
            year = invoice_date.year
            month_name = MONTHS_FR[invoice_date.month - 1]
            excel_path = os.path.join(config.FACTURES_DIR, str(year), f"factures_{year}.xlsx")

            if not os.path.exists(excel_path): return
            backup_database(year)

            all_sheets = pd.read_excel(excel_path, sheet_name=None, dtype={'ID': str, 'SequenceID': str})
            sheet_df = all_sheets.get(month_name)
            
            idx = sheet_df.index[sheet_df['ID'] == invoice_data['ID']].tolist()[0]
            sheet_df.loc[idx, 'Methode_Paiement'] = new_status
            sheet_df.loc[idx, 'Date_Paiement'] = new_payment_date
            sheet_df.loc[idx, 'Date_Seance'] = new_seance_date
            if new_child_dob: sheet_df.loc[idx, 'Naissance_Enfant'] = new_child_dob
            
            all_sheets[month_name] = sheet_df
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                for sheet_name, df in all_sheets.items(): df.to_excel(writer, sheet_name=sheet_name, index=False)

            if regen_pdf:
                updated_data = sheet_df.loc[idx].to_dict()
                clean_data = {k: v for k, v in updated_data.items() if pd.notna(v)}
                if 'Membres_Famille' in clean_data and isinstance(clean_data.get('Membres_Famille'), str):
                    try: clean_data['Membres_Famille'] = ast.literal_eval(clean_data['Membres_Famille'])
                    except: del clean_data['Membres_Famille']
                from .pdf_generator import generate_pdf
                generate_pdf(clean_data, is_duplicate=True)

            self.app._invalidate_data_cache()
            window.destroy()
            self.app._apply_filters_and_search()
            messagebox.showinfo("Succès", "Facture mise à jour.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur : {e}")

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
