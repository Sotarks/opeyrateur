import customtkinter as ctk
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil
from . import config
from . import settings_manager
import json

def create_expenses_tab(app):
    """Crée les widgets pour l'onglet 'Frais'."""
    # Configuration de la grille principale : 2 colonnes (Sidebar Saisie | Contenu Principal)
    app.expenses_tab.grid_columnconfigure(0, weight=0, minsize=320) # Sidebar fixe
    app.expenses_tab.grid_columnconfigure(1, weight=1) # Contenu extensible
    app.expenses_tab.grid_rowconfigure(0, weight=1)

    app.expense_to_edit = None # Variable pour stocker les données originales de la dépense en cours de modification
    app.current_proof_path = None # Variable pour stocker le chemin du fichier sélectionné

    # =================================================================================
    # 1. SIDEBAR DE SAISIE (GAUCHE)
    # =================================================================================
    sidebar = ctk.CTkFrame(app.expenses_tab, corner_radius=0, fg_color=("gray90", "gray16"))
    sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 1)) # Petit espace à droite pour séparer
    sidebar.grid_columnconfigure(0, weight=1)

    # Titre Saisie
    ctk.CTkLabel(sidebar, text="Saisie d'une dépense", font=app.font_large).pack(pady=(20, 15), padx=20, anchor="w")

    # --- Champs du formulaire (Vertical) ---
    
    # Date
    ctk.CTkLabel(sidebar, text="Date", font=app.font_bold).pack(pady=(5, 0), padx=20, anchor="w")
    app.expense_date = ctk.CTkEntry(sidebar, placeholder_text="JJ/MM/AAAA", height=35)
    app.expense_date.pack(pady=(0, 10), padx=20, fill="x")
    app.expense_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
    app.expense_date.configure(state="readonly")
    app.expense_date.bind("<1>", lambda event: app._open_calendar(app.expense_date))

    # Catégorie
    ctk.CTkLabel(sidebar, text="Catégorie", font=app.font_bold).pack(pady=(5, 0), padx=20, anchor="w")
    categories = ["Loyer", "Doctolib / Logiciels", "Supervision", "Mouchoirs / Café", "Papeterie / Tests", 
                  "Électricité / Gaz", "Téléphone / Internet", "Assurance RCP", "Formation", "Repas (seule)", 
                  "Banque", "Ménage", "Assurance Local", "Site Web", "Déplacement", "Cotisations", "Tenue Pro", "Prélèvement Personnel", "Autre"]
    app.expense_cat = ctk.CTkComboBox(sidebar, values=categories, height=35)
    app.expense_cat.pack(pady=(0, 10), padx=20, fill="x")

    # Filtrage dynamique des catégories (Autocomplétion)
    def _filter_categories(event):
        current_text = app.expense_cat.get()
        filtered_values = [cat for cat in categories if current_text.lower() in cat.lower()]
        app.expense_cat.configure(values=filtered_values)

    app.expense_cat._entry.bind("<KeyRelease>", _filter_categories)

    # Description
    ctk.CTkLabel(sidebar, text="Description", font=app.font_bold).pack(pady=(5, 0), padx=20, anchor="w")
    app.expense_desc = ctk.CTkEntry(sidebar, placeholder_text="Ex: Achat fournitures...", height=35)
    app.expense_desc.pack(pady=(0, 10), padx=20, fill="x")

    # Montant
    ctk.CTkLabel(sidebar, text="Montant (€)", font=app.font_bold).pack(pady=(5, 0), padx=20, anchor="w")
    app.expense_amount = ctk.CTkEntry(sidebar, placeholder_text="0.00", height=35, font=ctk.CTkFont(size=16, weight="bold"))
    app.expense_amount.pack(pady=(0, 15), padx=20, fill="x")

    # Zone Justificatif (Card style)
    ctk.CTkLabel(sidebar, text="Justificatif", font=app.font_bold).pack(pady=(5, 0), padx=20, anchor="w")
    
    proof_frame = ctk.CTkFrame(sidebar, fg_color=("white", "gray20"), border_width=1, border_color=("gray70", "gray30"))
    proof_frame.pack(pady=(0, 20), padx=20, fill="x")
    
    app.proof_label = ctk.CTkLabel(proof_frame, text="Aucun fichier", text_color="gray", font=ctk.CTkFont(size=12))
    app.proof_label.pack(pady=(10, 5))
    
    proof_btn_frame = ctk.CTkFrame(proof_frame, fg_color="transparent")
    proof_btn_frame.pack(pady=(0, 10), fill="x", padx=10)
    
    ctk.CTkButton(proof_btn_frame, text="📂 Parcourir", width=80, height=25, command=lambda: _select_proof(app), font=ctk.CTkFont(size=11)).pack(side="left", padx=2, expand=True, fill="x")
    ctk.CTkButton(proof_btn_frame, text="📋 Coller", width=60, height=25, command=lambda: _paste_proof(app), fg_color="#546E7A", hover_color="#455A64", font=ctk.CTkFont(size=11)).pack(side="left", padx=2, expand=True, fill="x")

    # Boutons de validation
    app.add_expense_btn = ctk.CTkButton(sidebar, text="Ajouter la dépense", command=lambda: _add_expense(app), font=app.font_button, height=45)
    app.add_expense_btn.pack(pady=5, padx=20, fill="x")
    
    app.original_btn_color = app.add_expense_btn.cget("fg_color") # Sauvegarde la couleur par défaut

    app.cancel_edit_expense_btn = ctk.CTkButton(sidebar, text="Annuler la modification", command=lambda: _cancel_edit_expense(app), fg_color="gray50", hover_color="#B71C1C", font=app.font_button, height=35)
    # Le bouton annuler est caché par défaut (pack_forget)

    # =================================================================================
    # 2. CONTENU PRINCIPAL (DROITE)
    # =================================================================================
    main_content = ctk.CTkFrame(app.expenses_tab, corner_radius=0, fg_color="transparent")
    main_content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
    main_content.grid_columnconfigure(0, weight=1)
    main_content.grid_rowconfigure(1, weight=1) # Le tableau prend toute la place

    # --- Barre d'outils supérieure (Filtres + Actions) ---
    toolbar_frame = ctk.CTkFrame(main_content, fg_color="transparent")
    toolbar_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    
    # Filtres (Gauche)
    from .data_manager import get_available_years, MONTHS_FR
    filter_container = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
    filter_container.pack(side="left")

    app.expense_view_type = ctk.StringVar(value="Année")
    years = get_available_years()
    if not years: years = [str(datetime.now().year)]
    app.expense_filter_year = ctk.StringVar(value=years[0])
    app.expense_filter_category = ctk.StringVar(value="Toutes")
    current_month_idx = datetime.now().month - 1
    app.expense_filter_month = ctk.StringVar(value=MONTHS_FR[current_month_idx])
    app.expense_filter_start = ctk.StringVar(value=MONTHS_FR[0])
    app.expense_filter_end = ctk.StringVar(value=MONTHS_FR[current_month_idx])

    ctk.CTkLabel(filter_container, text="Filtres :", font=app.font_bold).pack(side="left", padx=(0, 5))
    ctk.CTkOptionMenu(filter_container, variable=app.expense_filter_year, values=years, width=80).pack(side="left", padx=5)
    filter_categories = ["Toutes"] + categories
    ctk.CTkOptionMenu(filter_container, variable=app.expense_filter_category, values=filter_categories, width=140).pack(side="left", padx=5)
    app.expense_view_selector = ctk.CTkSegmentedButton(filter_container, values=["Année", "Mois", "Période"], variable=app.expense_view_type, command=lambda v: _update_filter_visibility(app))
    app.expense_view_selector.pack(side="left", padx=10)
    
    app.expense_month_menu = ctk.CTkOptionMenu(filter_container, variable=app.expense_filter_month, values=MONTHS_FR, width=110)
    app.expense_period_frame = ctk.CTkFrame(filter_container, fg_color="transparent")
    ctk.CTkLabel(app.expense_period_frame, text="de").pack(side="left", padx=2)
    ctk.CTkOptionMenu(app.expense_period_frame, variable=app.expense_filter_start, values=MONTHS_FR, width=100).pack(side="left", padx=2)
    ctk.CTkLabel(app.expense_period_frame, text="à").pack(side="left", padx=2)
    ctk.CTkOptionMenu(app.expense_period_frame, variable=app.expense_filter_end, values=MONTHS_FR, width=100).pack(side="left", padx=2)
    
    ctk.CTkButton(filter_container, text="🔄", width=40, command=lambda: refresh_expenses_list(app), fg_color="#546E7A").pack(side="left", padx=5)
    _update_filter_visibility(app) # Initialisation affichage

    # Actions (Droite)
    actions_container = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
    actions_container.pack(side="right")
    
    # Boutons compacts avec icônes/texte court
    ctk.CTkButton(actions_container, text="📅 Récurrents", width=100, command=lambda: _open_recurring_expenses_window(app), fg_color="#546E7A").pack(side="left", padx=2)
    ctk.CTkButton(actions_container, text="⚡ Générer", width=80, command=lambda: _generate_monthly_expenses(app), fg_color="#E67E22", hover_color="#D35400").pack(side="left", padx=2)
    
    # Menu déroulant pour les exports/imports pour gagner de la place
    def show_export_menu():
        menu = tk.Menu(app, tearoff=0)
        menu.add_command(label="📄 Ouvrir PDF", command=lambda: _view_pdf_report(app))
        menu.add_command(label="📥 Importer CSV Banque", command=lambda: _import_bank_csv(app))
        menu.add_command(label="📊 Télécharger PDF URSSAF", command=lambda: _generate_pdf_report(app))
        menu.add_command(label="⚖️ Export FEC (.fec)", command=lambda: _export_fec_expenses(app))
        menu.add_separator()
        menu.add_command(label="📂 Ouvrir le dossier", command=_open_expenses_folder)
        menu.add_command(label="🗑️ Réinitialiser tout", command=lambda: _reset_expenses(app))
        try:
            x = export_btn.winfo_rootx()
            y = export_btn.winfo_rooty() + export_btn.winfo_height()
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    export_btn = ctk.CTkButton(actions_container, text="Outils & Exports ▼", command=show_export_menu, fg_color="#34495E", width=120)
    export_btn.pack(side="left", padx=5)

    # --- Tableau des frais (Treeview) ---
    columns = ("date", "cat", "desc", "montant", "proof_status", "proof_path", "expense_id")
    app.expenses_tree = ttk.Treeview(main_content, columns=columns, show="headings", selectmode="browse", displaycolumns=("date", "cat", "desc", "montant", "proof_status"))
    
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

    app.expenses_tree.grid(row=1, column=0, sticky="nsew")

    # Scrollbar
    scrollbar = ttk.Scrollbar(main_content, orient="vertical", command=app.expenses_tree.yview)
    app.expenses_tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.grid(row=1, column=1, sticky="ns")

    # --- Menu Contextuel (Clic Droit) ---
    app.expenses_context_menu = tk.Menu(app.expenses_tab, tearoff=0)
    app.expenses_context_menu.add_command(label="Modifier", command=lambda: _prepare_edit_expense(app))
    app.expenses_context_menu.add_command(label="Ouvrir le justificatif", command=lambda: _open_proof(app))
    app.expenses_context_menu.add_command(label="Ajouter un justificatif", command=lambda: _add_proof_to_selected(app))
    app.expenses_context_menu.add_command(label="Supprimer", command=lambda: _confirm_delete_expense(app))
    app.expenses_tree.bind("<Button-3>", lambda event: _show_context_menu(event, app))
    app.expenses_tree.bind("<Double-1>", lambda event: _on_tree_double_click(app, event))

def _update_filter_visibility(app):
    """Affiche ou masque les sélecteurs de mois selon le mode choisi."""
    mode = app.expense_view_type.get()
    app.expense_month_menu.pack_forget()
    app.expense_period_frame.pack_forget()
    
    if mode == "Mois":
        app.expense_month_menu.pack(side="left", padx=5)
    elif mode == "Période":
        app.expense_period_frame.pack(side="left", padx=5)

def _select_proof(app):
    """Ouvre une boîte de dialogue pour choisir un fichier."""
    filename = filedialog.askopenfilename(title="Choisir un justificatif", filetypes=[("Images & PDF", "*.png;*.jpg;*.jpeg;*.pdf")])
    if filename:
        app.current_proof_path = filename
        app.proof_label.configure(text=os.path.basename(filename), text_color="black")
    else:
        # Si on annule, on ne change rien (pour éviter de perdre un fichier en mode édition)
        pass

def _paste_proof(app):
    """Tente de récupérer un chemin de fichier depuis le presse-papier."""
    try:
        # Récupère le contenu du presse-papier
        clipboard_content = app.clipboard_get()
        
        # Nettoyage (enlève les guillemets si "Copier en tant que chemin" a été utilisé)
        file_path = clipboard_content.strip().strip('"')
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            # Vérifie l'extension
            _, ext = os.path.splitext(file_path)
            if ext.lower() in ['.pdf', '.png', '.jpg', '.jpeg']:
                app.current_proof_path = file_path
                app.proof_label.configure(text=os.path.basename(file_path), text_color="black")
                app._show_status_message("Fichier collé depuis le presse-papier.")
            else:
                messagebox.showwarning("Format invalide", "Le fichier collé n'est pas une image ou un PDF valide.")
        else:
            messagebox.showinfo("Info", "Aucun fichier valide trouvé dans le presse-papier.\nCopiez un fichier (Ctrl+C) puis réessayez.")
    except Exception:
        messagebox.showinfo("Info", "Impossible de lire le presse-papier.")

def _add_expense(app):
    try:
        from .data_manager import save_expense
        
        # Validation stricte de la catégorie
        category = app.expense_cat.get().strip()
        valid_categories = ["Loyer", "Doctolib / Logiciels", "Supervision", "Mouchoirs / Café", "Papeterie / Tests", 
                      "Électricité / Gaz", "Téléphone / Internet", "Assurance RCP", "Formation", "Repas (seule)", 
                      "Banque", "Ménage", "Assurance Local", "Site Web", "Déplacement", "Cotisations", "Tenue Pro", "Prélèvement Personnel", "Autre"]

        if not category or category not in valid_categories:
            messagebox.showwarning("Catégorie invalide", "Veuillez sélectionner une catégorie valide dans la liste.")
            return

        montant = float(app.expense_amount.get().replace(',', '.'))
        data = {
            "Date": app.expense_date.get(),
            "Categorie": category,
            "Description": app.expense_desc.get(),
            "Montant": montant,
            "ProofPath": app.current_proof_path
        }
        
        if save_expense(data):
            message = "Dépense modifiée avec succès." if app.expense_to_edit else "Dépense ajoutée avec succès."
            app._show_status_message(message)
            refresh_expenses_list(app)
            app._invalidate_data_cache()
            app._update_dashboard_kpis()
            _cancel_edit_expense(app) # Réinitialise le formulaire et les boutons
        else:
            messagebox.showerror("Erreur", "Erreur lors de l'enregistrement.")
            
    except ValueError:
        messagebox.showerror("Erreur", "Montant invalide.")

def refresh_expenses_list(app):
    import pandas as pd
    from .data_manager import load_expenses, MONTHS_FR

    # Vide le tableau
    for item in app.expenses_tree.get_children():
        app.expenses_tree.delete(item)
        
    # Récupération des filtres
    try:
        year = int(app.expense_filter_year.get())
    except:
        year = datetime.now().year
        
    view_type = app.expense_view_type.get()
    category_filter = app.expense_filter_category.get()
    
    # Charge les données de l'année sélectionnée
    df = load_expenses(year)
    
    # Filtrage
    if not df.empty:
        # Conversion date pour filtrage
        df['DateObj'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
        
        if category_filter != "Toutes":
            df = df[df['Categorie'] == category_filter]
        
        if view_type == "Mois":
            month_name = app.expense_filter_month.get()
            month_idx = MONTHS_FR.index(month_name) + 1
            df = df[df['DateObj'].dt.month == month_idx]
            
        elif view_type == "Période":
            start_name = app.expense_filter_start.get()
            end_name = app.expense_filter_end.get()
            start_idx = MONTHS_FR.index(start_name) + 1
            end_idx = MONTHS_FR.index(end_name) + 1
            
            if start_idx <= end_idx:
                df = df[(df['DateObj'].dt.month >= start_idx) & (df['DateObj'].dt.month <= end_idx)]
            else:
                messagebox.showwarning("Filtre", "Le mois de début doit être avant le mois de fin.")
                return

    # Sauvegarde du DF filtré pour les exports
    app.current_expenses_filtered_df = df.copy()
    app.current_expenses_filter_info = f"{view_type} {year}" # Pour le titre PDF

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
            expense_id = row.get("ExpenseID", "")
            app.expenses_tree.insert("", "end", values=(row["Date"], row["Categorie"], row["Description"], f"{row['Montant']:.2f} €", proof_status, proof_path, expense_id))

def _generate_pdf_report(app):
    from .data_manager import load_expenses
    from .pdf_generator import generate_expenses_report
    
    # Utilise les données filtrées
    if not hasattr(app, 'current_expenses_filtered_df') or app.current_expenses_filtered_df.empty:
        messagebox.showwarning("Attention", "Aucune dépense affichée à exporter.")
        return
        
    df = app.current_expenses_filtered_df
    
    # Construction du titre
    year = app.expense_filter_year.get()
    title = f"Registre des Dépenses - {year}"
    if app.expense_view_type.get() == "Mois":
        title += f" - {app.expense_filter_month.get()}"
    elif app.expense_view_type.get() == "Période":
        title += f" ({app.expense_filter_start.get()} - {app.expense_filter_end.get()})"
        
    if app.expense_filter_category.get() != "Toutes":
        title += f" - {app.expense_filter_category.get()}"
        
    path = generate_expenses_report(title, df, year)
    
    # Ouvre le PDF ou le dossier
    try:
        os.startfile(path)
    except Exception as e:
        messagebox.showinfo("Succès", f"Rapport généré : {path}")

def _view_pdf_report(app):
    from .data_manager import load_expenses
    from .pdf_generator import generate_expenses_report
    from .pdf_viewer import PDFViewer
    
    # Utilise les données filtrées
    if not hasattr(app, 'current_expenses_filtered_df') or app.current_expenses_filtered_df.empty:
        messagebox.showwarning("Attention", "Aucune dépense affichée à visualiser.")
        return
        
    df = app.current_expenses_filtered_df
    
    # Construction du titre
    year = app.expense_filter_year.get()
    title = f"Registre des Dépenses - {year}"
    if app.expense_view_type.get() == "Mois":
        title += f" - {app.expense_filter_month.get()}"
    elif app.expense_view_type.get() == "Période":
        title += f" ({app.expense_filter_start.get()} - {app.expense_filter_end.get()})"
        
    if app.expense_filter_category.get() != "Toutes":
        title += f" - {app.expense_filter_category.get()}"
        
    path = generate_expenses_report(title, df, year)
    
    try:
        PDFViewer(app, path, download_filename=os.path.basename(path))
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de visualiser le PDF : {e}")

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
    proof_path = item_values[5] if len(item_values) > 5 else None
    
    if proof_path and os.path.exists(proof_path):
        # Si c'est un PDF, on utilise le visualiseur interne
        if proof_path.lower().endswith(".pdf"):
            from .pdf_viewer import PDFViewer
            PDFViewer(app, proof_path)
        else:
            # Sinon (image), on ouvre avec le système
            os.startfile(proof_path)
    else:
        messagebox.showinfo("Info", "Aucun justificatif pour cette dépense.")

def _on_tree_double_click(app, event):
    """Gère le double-clic sur une ligne : ouvre le justificatif s'il existe, sinon édite."""
    _open_proof(app)

def _add_proof_to_selected(app):
    """Ajoute ou remplace un justificatif pour la dépense sélectionnée."""
    selected_item = app.expenses_tree.selection()
    if not selected_item:
        return
    
    item_values = app.expenses_tree.item(selected_item, "values")
    # item_values: date, cat, desc, montant, proof_status, proof_path, expense_id
    
    filename = filedialog.askopenfilename(title="Choisir un justificatif", filetypes=[("Images & PDF", "*.png;*.jpg;*.jpeg;*.pdf")])
    if not filename:
        return

    montant_str = item_values[3].replace(' €', '').replace(',', '.')
    try:
        montant = float(montant_str)
    except:
        montant = 0.0

    data = {
        "Date": item_values[0],
        "Categorie": item_values[1],
        "Description": item_values[2],
        "Montant": montant,
        "ExpenseID": item_values[6],
        "ProofPath": filename
    }

    from .data_manager import delete_expense, save_expense
    # On supprime l'ancienne version pour la remplacer proprement (gestion des fichiers)
    delete_expense(data)
    if save_expense(data):
        app._show_status_message("Justificatif ajouté.")
        refresh_expenses_list(app)
    else:
        messagebox.showerror("Erreur", "Impossible de mettre à jour la dépense.")

def _confirm_delete_expense(app):
    """Supprime la dépense sélectionnée."""
    from .data_manager import delete_expense

    selected_item = app.expenses_tree.selection()
    if not selected_item:
        return
    
    item_values = app.expenses_tree.item(selected_item, "values")
    montant_str = item_values[3].replace(' €', '').replace(',', '.') if len(item_values) > 3 else "0.0"
    try:
        montant = float(montant_str)
    except:
        montant = 0.0

    data = {
        "Date": item_values[0] if len(item_values) > 0 else "",
        "Categorie": item_values[1] if len(item_values) > 1 else "",
        "Description": item_values[2] if len(item_values) > 2 else "",
        "Montant": montant,
        "ExpenseID": item_values[6] if len(item_values) > 6 else None
    }
    
    if messagebox.askyesno("Confirmation", "Voulez-vous vraiment supprimer cette dépense ?"):
        if delete_expense(data): # On passe tout le dict pour la compatibilité
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
    montant_str = item_values[3].replace(' €', '').replace(',', '.') if len(item_values) > 3 else "0.0"
    
    # Remplir le formulaire
    app.expense_date.configure(state="normal")
    app.expense_date.delete(0, 'end')
    app.expense_date.insert(0, item_values[0])
    app.expense_date.configure(state="readonly")
    
    app.expense_cat.set(item_values[1])
    
    app.expense_desc.delete(0, 'end')
    app.expense_desc.insert(0, item_values[2])
    
    app.expense_amount.delete(0, 'end')
    app.expense_amount.insert(0, montant_str)
    
    # Gestion du justificatif
    proof_path = item_values[5] if len(item_values) > 5 else None
    app.current_proof_path = proof_path if proof_path else None
    
    label_text = os.path.basename(proof_path) if proof_path else "Aucun fichier sélectionné"
    app.proof_label.configure(text=label_text, text_color="black" if proof_path else "gray")

    # Sauvegarde les données originales pour suppression ultérieure
    app.expense_to_edit = {
        "Date": item_values[0] if len(item_values) > 0 else "",
        "Categorie": item_values[1] if len(item_values) > 1 else "",
        "Description": item_values[2] if len(item_values) > 2 else "",
        "Montant": float(montant_str),
        "ExpenseID": item_values[6] if len(item_values) > 6 else None
    }
    
    # Change le bouton en mode "Modifier"
    app.add_expense_btn.configure(text="Modifier la dépense", fg_color="#e67e22", command=lambda: _update_expense(app))
    app.cancel_edit_expense_btn.pack(pady=(0, 5), padx=20, fill="x")

def _update_expense(app):
    """Supprime l'ancienne dépense et ajoute la nouvelle."""
    from .data_manager import delete_expense
    if app.expense_to_edit:
        delete_expense(app.expense_to_edit)
    
    _add_expense(app)
    
def _cancel_edit_expense(app):
    """Annule le mode édition et réinitialise le formulaire."""
    app.expense_to_edit = None
    app.current_proof_path = None

    # Réinitialise les champs du formulaire
    app.expense_desc.delete(0, 'end')
    app.expense_amount.delete(0, 'end')
    app.expense_date.configure(state="normal")
    app.expense_date.delete(0, 'end')
    app.expense_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
    app.expense_date.configure(state="readonly")
    app.proof_label.configure(text="Aucun fichier sélectionné", text_color="gray")

    # Réinitialise les boutons
    app.add_expense_btn.configure(text="Ajouter la dépense", fg_color=app.original_btn_color, command=lambda: _add_expense(app))
    app.cancel_edit_expense_btn.pack_forget()

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

def _open_recurring_expenses_window(app):
    """Ouvre une fenêtre pour gérer les frais récurrents."""
    win = ctk.CTkToplevel(app)
    win.title("Gérer les frais récurrents")
    win.geometry("700x600")
    win.transient(app)
    win.grab_set()

    # --- Liste des frais ---
    list_frame = ctk.CTkScrollableFrame(win, label_text="Liste des frais automatiques")
    list_frame.pack(fill="both", expand=True, padx=10, pady=10)

    recurring_data = settings_manager.get_recurring_expenses()
    edit_state = {"index": None}

    def refresh_list():
        for widget in list_frame.winfo_children():
            widget.destroy()
        
        for i, item in enumerate(recurring_data):
            f = ctk.CTkFrame(list_frame)
            f.pack(fill="x", pady=2)
            
            proof_icon = "📎" if item.get("ProofPath") else ""
            text = f"{item['Categorie']} | {item['Description']} | {item['Montant']} € {proof_icon}"
            ctk.CTkLabel(f, text=text, anchor="w").pack(side="left", padx=10, fill="x", expand=True)
            
            ctk.CTkButton(f, text="Supprimer", width=80, fg_color="#D32F2F", hover_color="#B71C1C", 
                          command=lambda idx=i: delete_item(idx)).pack(side="right", padx=5, pady=5)
            ctk.CTkButton(f, text="Modifier", width=80, fg_color="#546E7A", hover_color="#455A64", 
                          command=lambda idx=i: prepare_edit(idx)).pack(side="right", padx=5, pady=5)

    def delete_item(index):
        if edit_state["index"] == index:
            cancel_edit()
        elif edit_state["index"] is not None and edit_state["index"] > index:
            edit_state["index"] -= 1
        del recurring_data[index]
        settings_manager.save_recurring_expenses(recurring_data)
        refresh_list()

    refresh_list()

    # --- Formulaire d'ajout ---
    add_frame = ctk.CTkFrame(win)
    add_frame.pack(fill="x", padx=10, pady=10)
    
    ctk.CTkLabel(add_frame, text="Ajouter un nouveau frais récurrent", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=4, pady=5)

    categories = ["Loyer", "Doctolib / Logiciels", "Supervision", "Mouchoirs / Café", "Papeterie / Tests", 
                  "Électricité / Gaz", "Téléphone / Internet", "Assurance RCP", "Formation", "Repas (seule)", 
                  "Banque", "Ménage", "Assurance Local", "Site Web", "Déplacement", "Cotisations", "Tenue Pro", "Prélèvement Personnel", "Autre"]
    cat_var = ctk.CTkComboBox(add_frame, values=categories)
    cat_var.grid(row=1, column=0, padx=5, pady=5)

    # Filtrage dynamique pour les récurrents
    def _filter_recurring_categories(event):
        current_text = cat_var.get()
        filtered_values = [cat for cat in categories if current_text.lower() in cat.lower()]
        cat_var.configure(values=filtered_values)

    cat_var._entry.bind("<KeyRelease>", _filter_recurring_categories)
    
    desc_entry = ctk.CTkEntry(add_frame, placeholder_text="Description")
    desc_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
    
    amount_entry = ctk.CTkEntry(add_frame, placeholder_text="Montant", width=80)
    amount_entry.grid(row=1, column=2, padx=5, pady=5)

    proof_path_var = ctk.StringVar(value="")
    proof_label = ctk.CTkLabel(add_frame, text="Aucun justificatif", text_color="gray", width=150)
    proof_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=5)

    def select_proof():
        f = filedialog.askopenfilename(title="Justificatif par défaut", filetypes=[("Images & PDF", "*.png;*.jpg;*.jpeg;*.pdf")])
        if f:
            proof_path_var.set(f)
            proof_label.configure(text=os.path.basename(f), text_color="black")

    ctk.CTkButton(add_frame, text="Joindre Justificatif", command=select_proof, width=120).grid(row=2, column=2, padx=5, pady=5)

    def cancel_edit():
        edit_state["index"] = None
        desc_entry.delete(0, 'end')
        amount_entry.delete(0, 'end')
        proof_path_var.set("")
        proof_label.configure(text="Aucun justificatif", text_color="gray")
        add_btn.configure(text="Ajouter", fg_color="#34D399", hover_color="#10B981")
        cancel_btn.grid_forget()

    def prepare_edit(index):
        item = recurring_data[index]
        edit_state["index"] = index
        
        cat_var.set(item['Categorie'])
        desc_entry.delete(0, 'end')
        desc_entry.insert(0, item['Description'])
        amount_entry.delete(0, 'end')
        amount_entry.insert(0, str(item['Montant']))
        
        proof_path = item.get('ProofPath', "")
        proof_path_var.set(proof_path)
        if proof_path:
            proof_label.configure(text=os.path.basename(proof_path), text_color="black")
        else:
            proof_label.configure(text="Aucun justificatif", text_color="gray")
            
        add_btn.configure(text="Enregistrer", fg_color="#E67E22", hover_color="#D35400")
        cancel_btn.grid(row=1, column=4, rowspan=2, padx=5, pady=5, sticky="ns")

    def save_item():
        try:
            montant = float(amount_entry.get().replace(',', '.'))
            desc = desc_entry.get()
            if not desc: return
            
            item_data = {
                "Categorie": cat_var.get(),
                "Description": desc,
                "Montant": montant,
                "ProofPath": proof_path_var.get()
            }
            
            if edit_state["index"] is not None:
                recurring_data[edit_state["index"]] = item_data
                cancel_edit()
            else:
                recurring_data.append(item_data)
                # Reset form
                desc_entry.delete(0, 'end')
                amount_entry.delete(0, 'end')
                proof_path_var.set("")
                proof_label.configure(text="Aucun justificatif", text_color="gray")
            
            settings_manager.save_recurring_expenses(recurring_data)
            refresh_list()
        except ValueError:
            messagebox.showerror("Erreur", "Montant invalide", parent=win)

    add_btn = ctk.CTkButton(add_frame, text="Ajouter", command=save_item, fg_color="#34D399", hover_color="#10B981")
    add_btn.grid(row=1, column=3, rowspan=2, padx=5, pady=5, sticky="ns")
    
    cancel_btn = ctk.CTkButton(add_frame, text="Annuler", command=cancel_edit, fg_color="gray50", hover_color="gray30")
    
    add_frame.grid_columnconfigure(1, weight=1)

def _generate_monthly_expenses(app):
    """Génère les frais pour le mois en cours basés sur la configuration."""
    recurring_data = settings_manager.get_recurring_expenses()
    if not recurring_data:
        messagebox.showinfo("Info", "Aucun frais récurrent configuré.")
        return

    if not messagebox.askyesno("Confirmation", f"Voulez-vous générer {len(recurring_data)} frais pour aujourd'hui ?"):
        return

    from .data_manager import save_expense
    count = 0
    today_str = datetime.now().strftime("%d/%m/%Y")

    for item in recurring_data:
        # On crée une copie pour ne pas modifier la config
        data = item.copy()
        data['Date'] = today_str
        # save_expense va gérer la copie du justificatif si ProofPath est valide
        if save_expense(data):
            count += 1
    
    refresh_expenses_list(app)
    app._show_status_message(f"{count} frais générés avec succès.")

def _export_fec_expenses(app):
    """Génère un fichier FEC (Fichier des Écritures Comptables) pour les frais de l'année en cours."""
    import pandas as pd
    from .data_manager import ACCOUNT_MAP
    
    # Utilise les données filtrées
    if not hasattr(app, 'current_expenses_filtered_df') or app.current_expenses_filtered_df.empty:
        messagebox.showwarning("Export FEC", "Aucune dépense affichée à exporter.")
        return
        
    df = app.current_expenses_filtered_df

    # Récupération du SIREN pour le nommage du fichier
    pdf_info = settings_manager.get_pdf_info()
    siret = pdf_info.get('siret', '').replace(' ', '')
    siren = siret[:9] if len(siret) >= 9 else "000000000"
    
    try:
        lines = []
        header = [
            "JournalCode", "JournalLib", "EcritureNum", "EcritureDate", 
            "CompteNum", "CompteLib", "CompteAuxNum", "CompteAuxLib", 
            "PieceRef", "PieceDate", "EcritureLib", "Debit", "Credit", 
            "EcritureLet", "DateLet", "ValidDate", "Montantdevise", "Idevise"
        ]
        lines.append("|".join(header))
        
        if 'Date' in df.columns:
            df['DateObj'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
            df = df.sort_values(by=['DateObj'])

        ecriture_counter = 0
        for i, row in df.iterrows():
            try:
                ecriture_counter += 1
                date_str = row['Date']
                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                fec_date = date_obj.strftime("%Y%m%d")
                ref_piece = str(row.get('ExpenseID', f"EXP{i+1}"))
                if not ref_piece or ref_piece == "nan": ref_piece = f"EXP{i+1}"
                ecriture_num = str(ecriture_counter)

                # Fonction de nettoyage pour éviter de casser le CSV (pipe) ou de tronquer (newline)
                def clean_txt(t):
                    return str(t).replace('|', ' ').replace('\n', ' ').replace('\r', '').strip() if t else ""
                
                raw_montant = row.get('Montant', 0.0)
                if isinstance(raw_montant, str):
                    raw_montant = raw_montant.replace(',', '.')
                montant_float = float(raw_montant) if pd.notnull(raw_montant) else 0.0
                
                montant_str = f"{montant_float:.2f}".replace('.', ',')
                zero_str = "0,00"
                
                libelle = f"{clean_txt(row.get('Categorie', ''))} - {clean_txt(row.get('Description', ''))}"
                # Limite la taille du libellé pour éviter les problèmes de buffer
                libelle = libelle[:200]
                
                cat = clean_txt(row.get('Categorie', 'Charge'))
                
                # Utilise le CompteNum enregistré s'il existe, sinon utilise le mapping par défaut
                compte_charge = str(row.get('CompteNum')) if pd.notna(row.get('CompteNum')) else ACCOUNT_MAP.get(cat, "628000")
                if compte_charge.endswith('.0'): compte_charge = compte_charge[:-2]
                
                line_charge = "|".join(["AC", "Achats", ecriture_num, fec_date, compte_charge, cat, "", "", ref_piece, fec_date, libelle, montant_str, zero_str, "", "", fec_date, "", ""])
                line_fournisseur = "|".join(["AC", "Achats", ecriture_num, fec_date, "401000", "Fournisseurs divers", "", "", ref_piece, fec_date, libelle, zero_str, montant_str, "", "", fec_date, "", ""])
                
                lines.append(line_charge)
                lines.append(line_fournisseur)
            except Exception: continue
        
        # --- Validation du fichier FEC ---
        from .utils import validate_fec_content, FECPreviewWindow
        is_valid, errors = validate_fec_content(lines)
        
        if not is_valid:
            error_msg = "\n".join(errors[:10])
            if len(errors) > 10: error_msg += "\n..."
            if not messagebox.askyesno("Validation FEC échouée", f"Le fichier contient des erreurs :\n{error_msg}\n\nVoulez-vous quand même l'enregistrer ?"):
                return

        # --- Prévisualisation et Enregistrement ---
        def save_action():
            filename = f"{siren}FEC_Frais_{datetime.now().strftime('%Y%m%d')}.txt"
            filepath = filedialog.asksaveasfilename(
                defaultextension=".txt", initialfile=filename, title="Enregistrer le fichier FEC Frais", filetypes=[("Fichier FEC", "*.txt"), ("Tous les fichiers", "*.*")]
            )
            if not filepath: return

            with open(filepath, 'w', encoding='utf-8') as f: f.write("\n".join(lines))
            messagebox.showinfo("Succès", f"Fichier FEC Frais généré :\n{filepath}")

        FECPreviewWindow(app, lines, save_action)

    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur FEC : {e}")

def _import_bank_csv(app):
    """Ouvre un dialogue pour importer un CSV bancaire."""
    file_path = filedialog.askopenfilename(
        title="Sélectionner le relevé bancaire (CSV)",
        filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")]
    )
    
    if not file_path:
        return
        
    from .data_manager import import_expenses_from_csv
    
    count, error = import_expenses_from_csv(file_path)
    
    if error:
        messagebox.showerror("Erreur d'import", f"Une erreur est survenue : {error}")
    else:
        messagebox.showinfo("Succès", f"{count} dépenses ont été importées et catégorisées.")
        refresh_expenses_list(app)
        app._update_dashboard_kpis()