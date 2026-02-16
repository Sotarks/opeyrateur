import customtkinter as ctk
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil
import pandas as pd
from .data_manager import save_expense, load_expenses, delete_expense
from . import config
from .pdf_generator import generate_expenses_report

def create_expenses_tab(app):
    """Crée les widgets pour l'onglet 'Frais'."""
    app.expenses_tab.grid_columnconfigure(0, weight=1)
    app.expenses_tab.grid_rowconfigure(1, weight=1)

    app.current_proof_path = None # Variable pour stocker le chemin du fichier sélectionné

    # --- Formulaire d'ajout ---
    form_frame = ctk.CTkFrame(app.expenses_tab, corner_radius=10)
    form_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
    form_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

    ctk.CTkLabel(form_frame, text="Nouvelle Dépense", font=app.font_large).grid(row=0, column=0, columnspan=4, pady=(10, 5), padx=10, sticky="w")

    # Date
    ctk.CTkLabel(form_frame, text="Date").grid(row=1, column=0, padx=5, pady=5)
    app.expense_date = ctk.CTkEntry(form_frame, placeholder_text="JJ/MM/AAAA")
    app.expense_date.grid(row=2, column=0, padx=5, pady=(0, 10), sticky="ew")
    app.expense_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
    app.expense_date.configure(state="readonly")
    app.expense_date.bind("<1>", lambda event: app._open_calendar(app.expense_date))

    # Catégorie
    ctk.CTkLabel(form_frame, text="Catégorie").grid(row=1, column=1, padx=5, pady=5)
    categories = ["Loyer", "Déplacement", "Matériel", "Fournitures", "Cotisations", "Repas", "Autre"]
    app.expense_cat = ctk.CTkOptionMenu(form_frame, values=categories)
    app.expense_cat.grid(row=2, column=1, padx=5, pady=(0, 10), sticky="ew")

    # Description
    ctk.CTkLabel(form_frame, text="Description").grid(row=1, column=2, padx=5, pady=5)
    app.expense_desc = ctk.CTkEntry(form_frame, placeholder_text="Ex: Cabinet")
    app.expense_desc.grid(row=2, column=2, padx=5, pady=(0, 10), sticky="ew")

    # Montant
    ctk.CTkLabel(form_frame, text="Montant (€)").grid(row=1, column=3, padx=5, pady=5)
    app.expense_amount = ctk.CTkEntry(form_frame, placeholder_text="0.00")
    app.expense_amount.grid(row=2, column=3, padx=5, pady=(0, 10), sticky="ew")

    # Justificatif (Ligne suivante)
    ctk.CTkLabel(form_frame, text="Justificatif (Image/PDF) :").grid(row=3, column=0, sticky="e", padx=5, pady=5)
    app.proof_label = ctk.CTkLabel(form_frame, text="Aucun fichier sélectionné", text_color="gray")
    app.proof_label.grid(row=3, column=1, columnspan=2, sticky="w", padx=5, pady=5)
    ctk.CTkButton(form_frame, text="Parcourir...", width=100, command=lambda: _select_proof(app)).grid(row=3, column=3, padx=5, pady=5)

    # Bouton Ajouter
    app.add_expense_btn = ctk.CTkButton(form_frame, text="Ajouter la dépense", command=lambda: _add_expense(app), font=app.font_button)
    app.add_expense_btn.grid(row=4, column=0, columnspan=4, pady=10, padx=20, sticky="ew")
    app.original_btn_color = app.add_expense_btn.cget("fg_color") # Sauvegarde la couleur par défaut

    # --- Liste des frais ---
    list_frame = ctk.CTkFrame(app.expenses_tab, corner_radius=10)
    list_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
    list_frame.grid_columnconfigure(0, weight=1)
    list_frame.grid_rowconfigure(1, weight=1)

    header_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
    header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
    ctk.CTkLabel(header_frame, text="Liste des frais (Année en cours)", font=app.font_large).pack(side="left")

    # Frame for buttons on the right
    button_container = ctk.CTkFrame(header_frame, fg_color="transparent")
    button_container.pack(side="right")

    ctk.CTkButton(button_container, text="Télécharger PDF URSSAF", fg_color="#34D399", hover_color="#10B981", command=lambda: _generate_pdf_report(app), font=app.font_button).pack(side="left", padx=(0, 5))
    ctk.CTkButton(button_container, text="Ouvrir le dossier", command=_open_expenses_folder, font=app.font_button).pack(side="left", padx=(0, 5))
    ctk.CTkButton(button_container, text="Réinitialiser les frais", fg_color="#D32F2F", hover_color="#B71C1C", command=lambda: _reset_expenses(app), font=app.font_button).pack(side="left")

    # Treeview pour afficher les données (style tableau)
    columns = ("date", "cat", "desc", "montant", "proof_status", "proof_path")
    app.expenses_tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse", displaycolumns=("date", "cat", "desc", "montant", "proof_status"))
    
    app.expenses_tree.heading("date", text="Date", command=lambda: _sort_expenses_by(app, "date"))
    app.expenses_tree.heading("cat", text="Catégorie", command=lambda: _sort_expenses_by(app, "cat"))
    app.expenses_tree.heading("desc", text="Description")
    app.expenses_tree.heading("montant", text="Montant", command=lambda: _sort_expenses_by(app, "montant"))
    app.expenses_tree.heading("proof_status", text="Preuve")

    app.expenses_tree.column("date", width=100, anchor="center")
    app.expenses_tree.column("cat", width=150, anchor="w")
    app.expenses_tree.column("desc", width=300, anchor="w")
    app.expenses_tree.column("montant", width=100, anchor="e")
    app.expenses_tree.column("proof_status", width=60, anchor="center")

    app.expenses_tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

    # Scrollbar
    scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=app.expenses_tree.yview)
    app.expenses_tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.grid(row=1, column=1, sticky="ns")

    # --- Menu Contextuel (Clic Droit) ---
    app.expenses_context_menu = tk.Menu(app.expenses_tab, tearoff=0)
    app.expenses_context_menu.add_command(label="Modifier", command=lambda: _prepare_edit_expense(app))
    app.expenses_context_menu.add_command(label="Ouvrir le justificatif", command=lambda: _open_proof(app))
    app.expenses_context_menu.add_command(label="Supprimer", command=lambda: _confirm_delete_expense(app))
    app.expenses_tree.bind("<Button-3>", lambda event: _show_context_menu(event, app))

def _select_proof(app):
    """Ouvre une boîte de dialogue pour choisir un fichier."""
    filename = filedialog.askopenfilename(title="Choisir un justificatif", filetypes=[("Images & PDF", "*.png;*.jpg;*.jpeg;*.pdf")])
    if filename:
        app.current_proof_path = filename
        app.proof_label.configure(text=os.path.basename(filename), text_color="black")
    else:
        # Si on annule, on ne change rien (pour éviter de perdre un fichier en mode édition)
        pass

def _add_expense(app):
    try:
        montant = float(app.expense_amount.get().replace(',', '.'))
        data = {
            "Date": app.expense_date.get(),
            "Categorie": app.expense_cat.get(),
            "Description": app.expense_desc.get(),
            "Montant": montant,
            "ProofPath": app.current_proof_path
        }
        
        if save_expense(data):
            app._show_status_message("Dépense ajoutée avec succès.")
            app.expense_desc.delete(0, 'end')
            app.expense_amount.delete(0, 'end')
            refresh_expenses_list(app)
            
            # Réinitialisation du champ preuve
            app.current_proof_path = None
            app.proof_label.configure(text="Aucun fichier sélectionné", text_color="gray")
        else:
            messagebox.showerror("Erreur", "Erreur lors de l'enregistrement.")
            
    except ValueError:
        messagebox.showerror("Erreur", "Montant invalide.")

def refresh_expenses_list(app):
    # Vide le tableau
    for item in app.expenses_tree.get_children():
        app.expenses_tree.delete(item)
        
    # Charge les données de l'année en cours
    current_year = datetime.now().year
    df = load_expenses(current_year)

    # Crée le label pour l'état vide une seule fois s'il n'existe pas
    if not hasattr(app, 'expenses_empty_label'):
        app.expenses_empty_label = ctk.CTkLabel(app.expenses_tree.master, text="💸\nAucune dépense enregistrée pour cette année.", font=ctk.CTkFont(size=16), text_color="gray")

    if df.empty:
        # Affiche le message si la liste est vide
        app.expenses_empty_label.place(in_=app.expenses_tree, relx=0.5, rely=0.5, anchor="center")
    else:
        # Masque le message et remplit la liste s'il y a des données
        app.expenses_empty_label.place_forget()
        for _, row in df.iterrows():
            proof_path = row["ProofPath"] if pd.notna(row["ProofPath"]) else ""
            proof_status = "📎" if proof_path else ""
            app.expenses_tree.insert("", "end", values=(row["Date"], row["Categorie"], row["Description"], f"{row['Montant']:.2f} €", proof_status, proof_path))

def _generate_pdf_report(app):
    current_year = datetime.now().year
    df = load_expenses(current_year)
    if df.empty:
        messagebox.showwarning("Attention", "Aucune dépense à exporter pour cette année.")
        return
        
    path = generate_expenses_report(current_year, df)
    
    # Ouvre le PDF ou le dossier
    try:
        os.startfile(path)
    except Exception as e:
        messagebox.showinfo("Succès", f"Rapport généré : {path}")

def _show_context_menu(event, app):
    """Affiche le menu contextuel sur la ligne sélectionnée."""
    try:
        item = app.expenses_tree.identify_row(event.y)
        if item:
            app.expenses_tree.selection_set(item)
            app.expenses_context_menu.tk_popup(event.x_root, event.y_root)
    finally:
        app.expenses_context_menu.grab_release()

def _open_proof(app):
    """Ouvre le fichier justificatif associé à la dépense."""
    selected_item = app.expenses_tree.selection()
    if not selected_item: return
    
    item_values = app.expenses_tree.item(selected_item, "values")
    proof_path = item_values[5] # Index 5 = proof_path
    
    if proof_path and os.path.exists(proof_path):
        os.startfile(proof_path)
    else:
        messagebox.showinfo("Info", "Aucun justificatif pour cette dépense.")

def _confirm_delete_expense(app):
    """Supprime la dépense sélectionnée."""
    selected_item = app.expenses_tree.selection()
    if not selected_item:
        return
    
    item_values = app.expenses_tree.item(selected_item, "values")
    # values: date, cat, desc, montant_str
    
    montant_str = item_values[3].replace(' €', '').replace(',', '.')
    try:
        montant = float(montant_str)
    except:
        montant = 0.0
        
    data = {
        "Date": item_values[0],
        "Categorie": item_values[1],
        "Description": item_values[2],
        "Montant": montant
    }
    
    if messagebox.askyesno("Confirmation", "Voulez-vous vraiment supprimer cette dépense ?"):
        if delete_expense(data):
            refresh_expenses_list(app)
            app._show_status_message("Dépense supprimée.")
        else:
            messagebox.showerror("Erreur", "Impossible de supprimer la dépense.")

def _prepare_edit_expense(app):
    """Remplit le formulaire avec les données sélectionnées pour modification."""
    selected_item = app.expenses_tree.selection()
    if not selected_item:
        return
        
    item_values = app.expenses_tree.item(selected_item, "values")
    
    # Remplir le formulaire
    app.expense_date.configure(state="normal")
    app.expense_date.delete(0, 'end')
    app.expense_date.insert(0, item_values[0])
    app.expense_date.configure(state="readonly")
    
    app.expense_cat.set(item_values[1])
    
    app.expense_desc.delete(0, 'end')
    app.expense_desc.insert(0, item_values[2])
    
    montant_str = item_values[3].replace(' €', '').replace(',', '.')
    app.expense_amount.delete(0, 'end')
    app.expense_amount.insert(0, montant_str)
    
    # Gestion du justificatif
    proof_path = item_values[5] # Index 5 = proof_path
    app.current_proof_path = proof_path if proof_path else None
    
    label_text = os.path.basename(proof_path) if proof_path else "Aucun fichier sélectionné"
    app.proof_label.configure(text=label_text, text_color="black" if proof_path else "gray")

    # Sauvegarde les données originales pour suppression ultérieure
    app.expense_to_edit = {
        "Date": item_values[0],
        "Categorie": item_values[1],
        "Description": item_values[2],
        "Montant": float(montant_str)
    }
    
    # Change le bouton en mode "Modifier"
    app.add_expense_btn.configure(text="Modifier la dépense", fg_color="#e67e22", command=lambda: _update_expense(app))

def _update_expense(app):
    """Supprime l'ancienne dépense et ajoute la nouvelle."""
    # On tente d'ajouter la nouvelle dépense (la validation se fait dans _add_expense)
    # Si on est ici, c'est qu'on veut modifier. On supprime l'ancienne d'abord.
    if hasattr(app, 'expense_to_edit'):
        delete_expense(app.expense_to_edit)
        del app.expense_to_edit
    
    _add_expense(app)
    
    # Réinitialise le bouton
    app.add_expense_btn.configure(text="Ajouter la dépense", fg_color=app.original_btn_color, command=lambda: _add_expense(app))
    
    # Réinitialise le champ preuve si on annule ou finit (géré par _add_expense, mais au cas où)
    if not hasattr(app, 'expense_to_edit'):
        app.current_proof_path = None
        app.proof_label.configure(text="Aucun fichier sélectionné", text_color="gray")

def _sort_expenses_by(app, col):
    """Trie le Treeview des dépenses par colonne."""
    # Récupère toutes les lignes du Treeview
    rows = [(app.expenses_tree.set(item, col), item) for item in app.expenses_tree.get_children('')]

    # Détermine l'ordre de tri
    current_col, is_reversed = app.expense_sort_state
    reverse = is_reversed if col == current_col else False

    # Logique de tri spécifique par colonne
    if col == 'montant':
        # Convertit le montant en float pour le tri numérique
        rows.sort(key=lambda x: float(x[0].replace(' €', '').replace(',', '.')), reverse=reverse)
    elif col == 'date':
        # Convertit la date pour le tri chronologique
        rows.sort(key=lambda x: datetime.strptime(x[0], '%d/%m/%Y'), reverse=reverse)
    else:
        # Tri alphabétique standard
        rows.sort(key=lambda x: x[0].lower(), reverse=reverse)

    # Réinsère les lignes dans le Treeview dans le nouvel ordre
    for index, (val, item) in enumerate(rows):
        app.expenses_tree.move(item, '', index)

    # Met à jour l'état de tri pour le prochain clic
    app.expense_sort_state = (col, not reverse)

def _open_expenses_folder():
    """Ouvre le dossier contenant les frais générés."""
    os.makedirs(config.FRAIS_DIR, exist_ok=True)
    try:
        os.startfile(config.FRAIS_DIR)
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible d'ouvrir le dossier des frais:\n{e}")

def _reset_expenses(app):
    """Supprime tous les fichiers générés dans le dossier frais et rafraîchit la liste."""
    if messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer tous les frais et justificatifs enregistrés ?\nCette action est irréversible."):
        try:
            if os.path.exists(config.FRAIS_DIR):
                shutil.rmtree(config.FRAIS_DIR)
            # Recrée le dossier vide
            os.makedirs(config.FRAIS_DIR, exist_ok=True)
            messagebox.showinfo("Succès", "Le dossier des frais a été réinitialisé.")
            # Rafraîchit la liste dans l'interface
            refresh_expenses_list(app)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de réinitialiser le dossier des frais:\n{e}")