import customtkinter as ctk
import tkinter as tk
import fitz  # PyMuPDF
from PIL import Image, ImageTk
from tkinter import messagebox, filedialog
import os
import shutil

class PDFViewer(ctk.CTkToplevel):
    """
    Une fenêtre Toplevel pour afficher un fichier PDF avec des contrôles de base.
    Nécessite PyMuPDF (fitz) et Pillow.
    """
    def __init__(self, parent, pdf_path, download_filename=None):
        super().__init__(parent)
        self.title(f"Visualiseur PDF - {os.path.basename(pdf_path)}")
        self.geometry("800x1000")
        self.transient(parent)
        self.grab_set()

        self.pdf_path = pdf_path
        self.download_filename = download_filename
        self.pdf_document = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom_level = 1.0
        self.pil_image = None
        self.tk_image = None

        # --- Layout ---
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Controls Frame ---
        controls_frame = ctk.CTkFrame(self, height=50)
        controls_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        # --- Left side ---
        self.prev_button = ctk.CTkButton(controls_frame, text="⬅ Précédent", command=self.prev_page, state="disabled")
        self.prev_button.pack(side="left", padx=5)

        self.page_label = ctk.CTkLabel(controls_frame, text="Page 0 / 0")
        self.page_label.pack(side="left", padx=5)

        self.next_button = ctk.CTkButton(controls_frame, text="Suivant ➡", command=self.next_page, state="disabled")
        self.next_button.pack(side="left", padx=5)

        # --- Right side (packed in reverse order of appearance) ---
        self.open_folder_button = ctk.CTkButton(controls_frame, text="Ouvrir le dossier", command=self._open_containing_folder)
        self.open_folder_button.pack(side="right", padx=(20, 5))

        if self.download_filename:
            self.download_button = ctk.CTkButton(controls_frame, text="Télécharger", command=self._download_pdf)
            self.download_button.pack(side="right", padx=(5, 5))

        ctk.CTkButton(controls_frame, text="+", width=30, command=self.zoom_in).pack(side="right", padx=5)
        self.zoom_label = ctk.CTkLabel(controls_frame, text="100%")
        self.zoom_label.pack(side="right")
        ctk.CTkButton(controls_frame, text="-", width=30, command=self.zoom_out).pack(side="right", padx=5)

        # --- Canvas for PDF page ---
        self.canvas = tk.Canvas(self, bg="gray50")
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))

        try:
            self.pdf_document = fitz.open(pdf_path)
            self.total_pages = len(self.pdf_document)
            self.render_page()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier PDF:\n{e}", parent=self)
            self.destroy()
        
        self.protocol("WM_DELETE_WINDOW", self.close)

    def render_page(self):
        if not self.pdf_document: return

        page = self.pdf_document.load_page(self.current_page)
        mat = fitz.Matrix(self.zoom_level, self.zoom_level)
        pix = page.get_pixmap(matrix=mat)
        
        self.pil_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.tk_image = ImageTk.PhotoImage(self.pil_image)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        self.update_controls()

    def update_controls(self):
        self.page_label.configure(text=f"Page {self.current_page + 1} / {self.total_pages}")
        self.prev_button.configure(state="normal" if self.current_page > 0 else "disabled")
        self.next_button.configure(state="normal" if self.current_page < self.total_pages - 1 else "disabled")
        self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.render_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.render_page()

    def zoom_in(self):
        self.zoom_level = min(self.zoom_level + 0.1, 3.0)
        self.render_page()

    def zoom_out(self):
        self.zoom_level = max(self.zoom_level - 0.1, 0.2)
        self.render_page()

    def close(self):
        if self.pdf_document:
            self.pdf_document.close()
        self.destroy()

    def _download_pdf(self):
        """Ouvre une boîte de dialogue pour enregistrer le PDF actuel."""
        if not self.download_filename:
            return

        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Fichiers PDF", "*.pdf"), ("Tous les fichiers", "*.*")],
                initialfile=self.download_filename,
                title="Enregistrer le rapport PDF"
            )

            if not filepath:
                return # User cancelled

            shutil.copy2(self.pdf_path, filepath)
            messagebox.showinfo("Succès", f"Le fichier a été téléchargé avec succès vers :\n{filepath}", parent=self)
        except Exception as e:
            messagebox.showerror("Erreur de téléchargement", f"Une erreur est survenue :\n{e}", parent=self)

    def _open_containing_folder(self):
        """Ouvre le dossier contenant le PDF actuel."""
        try:
            folder_path = os.path.dirname(self.pdf_path)
            os.startfile(folder_path)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le dossier:\n{e}", parent=self)