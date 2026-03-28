import customtkinter as ctk
from datetime import datetime
from tkinter import filedialog, messagebox
import os
from opeyrateur_app.core import config
from opeyrateur_app.core import settings_manager

def create_budget_tab(app):
    """Crée les widgets pour l'onglet 'Budget'."""
    
    # Historique Undo
    app.last_reimbursement_action = getattr(app, 'last_reimbursement_action', None)
    if not hasattr(app, 'reimbursement_undo_bound'):
        app.bind("<Control-z>", lambda e: _undo_reimburse(app), add="+")
        app.bind("<Command-z>", lambda e: _undo_reimburse(app), add="+")
        app.reimbursement_undo_bound = True

    # Configuration : 2 colonnes (Sidebar Contrôles | Contenu Principal)
    app.budget_tab.grid_columnconfigure(0, weight=0, minsize=320) # Sidebar fixe
    app.budget_tab.grid_columnconfigure(1, weight=1) # Contenu extensible
    app.budget_tab.grid_rowconfigure(0, weight=1)
    
    # =================================================================================
    # 1. SIDEBAR (GAUCHE) - Filtres, Stats, Actions
    # =================================================================================
    sidebar = ctk.CTkFrame(app.budget_tab, corner_radius=0, fg_color=("gray90", "gray16"))
    sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 1))
    sidebar.grid_columnconfigure(0, weight=1)
    
    # Titre
    ctk.CTkLabel(sidebar, text="Analyse des Recettes", font=app.font_large).pack(pady=(20, 15), padx=20, anchor="w")

    # --- Section Filtres ---
    filter_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
    filter_frame.pack(fill="x", padx=20, pady=(0, 20))
    
    ctk.CTkLabel(filter_frame, text="Période", font=app.font_bold).pack(anchor="w", pady=(0, 5))
    
    # Type de vue
    app.budget_view_type = ctk.CTkSegmentedButton(filter_frame, values=["Année", "Mois", "Période"], command=lambda v: _update_budget_inputs(app))
    app.budget_view_type.pack(fill="x", pady=(0, 10))
    app.budget_view_type.set("Mois")

    # Conteneur pour les menus déroulants
    app.budget_dropdown_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
    app.budget_dropdown_frame.pack(fill="x")
    app.budget_dropdown_frame.grid_columnconfigure(0, weight=1)

    # Variables
    app.budget_year_var = ctk.StringVar()
    app.budget_month_var = ctk.StringVar()
    app.budget_start_month_var = ctk.StringVar()
    app.budget_end_month_var = ctk.StringVar()
    
    from opeyrateur_app.core.data_manager import get_available_years, MONTHS_FR
    years = get_available_years()
    if not years: years = [str(datetime.now().year)]
    app.budget_year_var.set(years[0])
    current_month_name = MONTHS_FR[datetime.now().month - 1]
    app.budget_month_var.set(current_month_name)
    app.budget_start_month_var.set(current_month_name)
    app.budget_end_month_var.set(current_month_name)

    # Widgets (créés mais placés dynamiquement)
    app.budget_year_menu = ctk.CTkOptionMenu(app.budget_dropdown_frame, variable=app.budget_year_var, values=years)
    app.budget_month_menu = ctk.CTkOptionMenu(app.budget_dropdown_frame, variable=app.budget_month_var, values=MONTHS_FR)
    app.budget_start_month_menu = ctk.CTkOptionMenu(app.budget_dropdown_frame, variable=app.budget_start_month_var, values=MONTHS_FR)
    app.budget_end_month_menu = ctk.CTkOptionMenu(app.budget_dropdown_frame, variable=app.budget_end_month_var, values=MONTHS_FR)
    
    # Bouton Calculer
    ctk.CTkButton(sidebar, text="Actualiser l'analyse", command=lambda: calculate_budget(app), height=40, font=app.font_button, fg_color="#3498db", hover_color="#2980b9").pack(fill="x", padx=20, pady=(0, 20))

    # --- Section Résultats (Cards) ---
    stats_frame = ctk.CTkFrame(sidebar, corner_radius=15, fg_color=("white", "gray20"))
    stats_frame.pack(fill="x", padx=20, pady=(0, 20))
    
    ctk.CTkLabel(stats_frame, text="Résultats de la période", font=app.font_bold, text_color="gray").pack(anchor="w", padx=15, pady=(15, 5))
    
    # Total
    ctk.CTkLabel(stats_frame, text="Chiffre d'Affaires", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=15)
    app.budget_total_label = ctk.CTkLabel(stats_frame, text="0.00 €", font=ctk.CTkFont(size=26, weight="bold"), text_color="#2ecc71")
    app.budget_total_label.pack(anchor="w", padx=15, pady=(0, 10))
    
    # Dépenses
    ctk.CTkLabel(stats_frame, text="Dépenses", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=15)
    app.budget_expenses_label = ctk.CTkLabel(stats_frame, text="0.00 €", font=ctk.CTkFont(size=20, weight="bold"), text_color="#e74c3c")
    app.budget_expenses_label.pack(anchor="w", padx=15, pady=(0, 10))

    # Bénéfice
    ctk.CTkLabel(stats_frame, text="Bénéfice Net", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=15)
    app.budget_net_label = ctk.CTkLabel(stats_frame, text="0.00 €", font=ctk.CTkFont(size=20, weight="bold"), text_color="#3498db")
    app.budget_net_label.pack(anchor="w", padx=15, pady=(0, 10))

    # Count
    ctk.CTkLabel(stats_frame, text="Consultations", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=15)
    app.budget_count_label = ctk.CTkLabel(stats_frame, text="0", font=ctk.CTkFont(size=20, weight="bold"))
    app.budget_count_label.pack(anchor="w", padx=15, pady=(0, 20))

    # --- Section Rémunération (Simulateur) ---
    salary_frame = ctk.CTkFrame(sidebar, corner_radius=15, fg_color=("white", "gray20"))
    salary_frame.pack(fill="x", padx=20, pady=(0, 20))
    
    ctk.CTkLabel(salary_frame, text="Simulateur Rémunération", font=app.font_bold, text_color="gray").pack(anchor="w", padx=15, pady=(15, 5))
    
    # Estimation
    ctk.CTkLabel(salary_frame, text="Salaire Conseillé (Max)", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=15)
    app.budget_safe_salary_label = ctk.CTkLabel(salary_frame, text="0.00 €", font=ctk.CTkFont(size=18, weight="bold"), text_color="#3498db")
    app.budget_safe_salary_label.pack(anchor="w", padx=15, pady=(0, 10))
    
    # Saisie
    ctk.CTkLabel(salary_frame, text="Salaire Versé", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=15)
    app.budget_salary_entry = ctk.CTkEntry(salary_frame, placeholder_text="0.00", height=30)
    app.budget_salary_entry.pack(fill="x", padx=15, pady=(0, 10))
    
    # Jauge visuelle
    app.budget_salary_progress = ctk.CTkProgressBar(salary_frame, height=10, corner_radius=5)
    app.budget_salary_progress.pack(fill="x", padx=15, pady=(0, 10))
    app.budget_salary_progress.set(0)

    # Reste
    ctk.CTkLabel(salary_frame, text="Solde après salaire", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=15)
    app.budget_cash_balance_label = ctk.CTkLabel(salary_frame, text="0.00 €", font=ctk.CTkFont(size=18, weight="bold"), text_color="gray")
    app.budget_cash_balance_label.pack(anchor="w", padx=15, pady=(0, 10))

    # Bouton Enregistrer
    ctk.CTkButton(salary_frame, text="Enregistrer le prélèvement", command=lambda: _save_salary_expense(app), fg_color="transparent", border_width=1, text_color=("gray10", "gray90"), height=30).pack(fill="x", padx=15, pady=(0, 15))

    def _update_salary_balance(event=None):
        try:
            safe = getattr(app, 'current_safe_salary', 0.0)
            paid_str = app.budget_salary_entry.get().replace(',', '.')
            paid = float(paid_str) if paid_str else 0.0
            
            balance = safe - paid
            app.budget_cash_balance_label.configure(text=f"{balance:+.2f} €", text_color="#2ecc71" if balance >= 0 else "#e74c3c")
            
            # Mise à jour de la jauge
            total_out = paid
            if safe > 0:
                ratio = total_out / safe
                app.budget_salary_progress.set(min(ratio, 1.0))
                if ratio > 1.0:
                    app.budget_salary_progress.configure(progress_color="#e74c3c") # Rouge si dépassement
                elif ratio > 0.8:
                    app.budget_salary_progress.configure(progress_color="#f39c12") # Orange si proche
                else:
                    app.budget_salary_progress.configure(progress_color="#2ecc71") # Vert sinon
            else:
                app.budget_salary_progress.set(1.0 if total_out > 0 else 0.0)
                app.budget_salary_progress.configure(progress_color="#e74c3c")
        except ValueError: pass
    
    app.budget_salary_entry.bind("<KeyRelease>", _update_salary_balance)

    # Historique des prélèvements
    history_header = ctk.CTkFrame(salary_frame, fg_color="transparent")
    history_header.pack(fill="x", padx=15, pady=(15, 5))
    
    ctk.CTkLabel(history_header, text="Historique Prélèvements", font=app.font_bold, text_color="gray").pack(side="left")
    ctk.CTkButton(history_header, text="📄 PDF", width=50, height=20, font=ctk.CTkFont(size=10), fg_color="transparent", border_width=1, text_color=("gray10", "gray90"), command=lambda: _export_salary_history_pdf(app)).pack(side="right")

    app.salary_history_frame = ctk.CTkScrollableFrame(salary_frame, height=100, fg_color="transparent", label_text="")
    app.salary_history_frame.pack(fill="x", padx=5, pady=(0, 10))

    # --- Section Actions (Exports) ---
    ctk.CTkLabel(sidebar, text="Exports & Rapports", font=app.font_bold).pack(anchor="w", padx=20, pady=(10, 5))
    
    ctk.CTkButton(sidebar, text="📄 Visualiser PDF", command=lambda: _view_budget_pdf(app), fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(fill="x", padx=20, pady=5)
    ctk.CTkButton(sidebar, text="📊 Générer Excel", command=lambda: _export_budget(app), fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(fill="x", padx=20, pady=5)
    ctk.CTkButton(sidebar, text="⚖️ Export Légal (.fec)", command=lambda: _export_fec(app), fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(fill="x", padx=20, pady=5)

    # =================================================================================
    # 2. MAIN CONTENT (DROITE) - Graphique
    # =================================================================================
    main_content = ctk.CTkScrollableFrame(app.budget_tab, corner_radius=0, fg_color="transparent")
    main_content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
    main_content.grid_columnconfigure(0, weight=1)
    main_content.grid_rowconfigure(3, weight=2) # Le graphique prend plus de place
    main_content.grid_rowconfigure(5, weight=1) # La répartition prend le reste

    # --- Section: Bilan Financier Annuel ---
    ctk.CTkLabel(main_content, text="Bilan Financier Annuel (Année complète)", font=app.font_title, text_color="#8e44ad").grid(row=0, column=0, sticky="w", pady=(0, 15))

    app.annual_balance_frame = ctk.CTkFrame(main_content, corner_radius=15, fg_color=("white", "gray20"))
    app.annual_balance_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
    app.annual_balance_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

    # Bloc CA Annuel
    ca_frame = ctk.CTkFrame(app.annual_balance_frame, fg_color="transparent")
    ca_frame.grid(row=0, column=0, padx=10, pady=15, sticky="ew")
    ctk.CTkLabel(ca_frame, text="CA Brut Annuel", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").pack()
    app.annual_ca_label = ctk.CTkLabel(ca_frame, text="0.00 €", font=ctk.CTkFont(size=20, weight="bold"), text_color="#2ecc71")
    app.annual_ca_label.pack(pady=(5, 0))

    # Bloc Cotisations
    cotis_frame = ctk.CTkFrame(app.annual_balance_frame, fg_color="transparent")
    cotis_frame.grid(row=0, column=1, padx=10, pady=15, sticky="ew")
    ctk.CTkLabel(cotis_frame, text="Cotisations Sociales", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").pack()
    app.annual_cotis_entry = ctk.CTkEntry(cotis_frame, justify="center", width=120)
    app.annual_cotis_entry.pack(pady=(5, 0))
    app.annual_cotis_entry.insert(0, "0.00")

    # Bloc Impôts
    impots_frame = ctk.CTkFrame(app.annual_balance_frame, fg_color="transparent")
    impots_frame.grid(row=0, column=2, padx=10, pady=15, sticky="ew")
    ctk.CTkLabel(impots_frame, text="Impôts", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").pack()
    app.annual_impots_entry = ctk.CTkEntry(impots_frame, justify="center", width=120)
    app.annual_impots_entry.pack(pady=(5, 0))
    app.annual_impots_entry.insert(0, "0.00")

    # Bloc Rémunération
    remu_frame = ctk.CTkFrame(app.annual_balance_frame, fg_color="transparent")
    remu_frame.grid(row=0, column=3, padx=10, pady=15, sticky="ew")
    ctk.CTkLabel(remu_frame, text="Ma Rémunération", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").pack()
    app.annual_remu_label = ctk.CTkLabel(remu_frame, text="0.00 €", font=ctk.CTkFont(size=20, weight="bold"), text_color="#3498db")
    app.annual_remu_label.pack(pady=(5, 0))

    # Bloc Reste
    reste_frame = ctk.CTkFrame(app.annual_balance_frame, fg_color="transparent")
    reste_frame.grid(row=0, column=4, padx=10, pady=15, sticky="ew")
    ctk.CTkLabel(reste_frame, text="Reste / Trésorerie", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").pack()
    app.annual_reste_label = ctk.CTkLabel(reste_frame, text="0.00 €", font=ctk.CTkFont(size=24, weight="bold"), text_color="#e67e22")
    app.annual_reste_label.pack(pady=(5, 0))

    # Binding pour mise à jour
    app.annual_cotis_entry.bind("<KeyRelease>", lambda e: _update_annual_balance_calc(app))
    app.annual_impots_entry.bind("<KeyRelease>", lambda e: _update_annual_balance_calc(app))

    ctk.CTkLabel(main_content, text="Visualisation Graphique", font=app.font_title, text_color="#3498db").grid(row=2, column=0, sticky="w", pady=(0, 15))

    app.chart_frame = ctk.CTkFrame(main_content, corner_radius=15, fg_color=("white", "gray20"))
    app.chart_frame.grid(row=3, column=0, sticky="nsew")

    ctk.CTkLabel(main_content, text="Répartition par Prestation", font=app.font_title, text_color="#3498db").grid(row=4, column=0, sticky="w", pady=(20, 15))

    app.breakdown_frame = ctk.CTkFrame(main_content, corner_radius=15, fg_color=("white", "gray20"))
    app.breakdown_frame.grid(row=5, column=0, sticky="nsew")

    # --- Section: Frais à Rembourser ---
    ctk.CTkLabel(main_content, text="Dépenses à Rembourser (Carte Perso)", font=app.font_title, text_color="#e67e22").grid(row=6, column=0, sticky="w", pady=(20, 15))

    app.reimbursement_frame = ctk.CTkFrame(main_content, corner_radius=15, fg_color=("white", "gray20"))
    app.reimbursement_frame.grid(row=7, column=0, sticky="nsew")
    
    app.reimbursement_header = ctk.CTkFrame(app.reimbursement_frame, fg_color="transparent")
    app.reimbursement_header.pack(fill="x", padx=15, pady=(15, 5))
    
    app.reimbursement_total_label = ctk.CTkLabel(app.reimbursement_header, text="Total à rembourser : 0.00 €", font=ctk.CTkFont(size=14, weight="bold"), text_color="#e67e22")
    app.reimbursement_total_label.pack(side="left")

    ctk.CTkButton(app.reimbursement_header, text="💸 Verser le remboursement", command=lambda: _reimburse_selected(app), fg_color="#27ae60", hover_color="#2ecc71").pack(side="right")

    import tkinter.ttk as ttk
    columns = ("date", "cat", "desc", "montant", "id")
    app.reimbursement_tree = ttk.Treeview(app.reimbursement_frame, columns=columns, show="headings", height=6, selectmode="extended", displaycolumns=("date", "cat", "desc", "montant"))
    app.reimbursement_tree.heading("date", text="Date")
    app.reimbursement_tree.heading("cat", text="Catégorie")
    app.reimbursement_tree.heading("desc", text="Description")
    app.reimbursement_tree.heading("montant", text="Montant")
    
    app.reimbursement_tree.column("date", width=100, anchor="center")
    app.reimbursement_tree.column("cat", width=150, anchor="w")
    app.reimbursement_tree.column("desc", width=250, anchor="w")
    app.reimbursement_tree.column("montant", width=100, anchor="e")
    app.reimbursement_tree.pack(fill="x", padx=15, pady=(0, 15))

    # Initialisation de l'affichage
    _update_budget_inputs(app)

def _update_budget_inputs(app):
    """Affiche ou masque le menu des mois selon la vue choisie."""
    view_type = app.budget_view_type.get()
    
    # Reset layout
    app.budget_year_menu.grid_forget()
    app.budget_month_menu.grid_forget()
    app.budget_start_month_menu.grid_forget()
    app.budget_end_month_menu.grid_forget()
    
    # L'année est toujours visible
    app.budget_year_menu.grid(row=0, column=0, sticky="ew", pady=(0, 5))
    
    if view_type == "Mois":
        app.budget_month_menu.grid(row=1, column=0, sticky="ew", pady=(0, 5))
    elif view_type == "Période":
        app.budget_start_month_menu.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        app.budget_end_month_menu.grid(row=2, column=0, sticky="ew", pady=(0, 5))

def calculate_budget(app):
    """Calcule et affiche les statistiques."""
    import pandas as pd
    from opeyrateur_app.core.data_manager import load_year_data, load_expenses, MONTHS_FR

    year = app.budget_year_var.get()
    view_type = app.budget_view_type.get()
    
    # Charge les données de l'année
    df_year = load_year_data(year)
    df_expenses = load_expenses(year)
    
    # --- FILTRE IMPAYÉS ---
    # On exclut les factures dont le statut est "Impayé"
    if not df_year.empty and 'Methode_Paiement' in df_year.columns:
        df_year = df_year[df_year['Methode_Paiement'] != 'Impayé'].copy()
    
    # Prépare les données pour les statistiques (filtrage mois si nécessaire)
    df_stats = df_year.copy()
    df_exp_stats = df_expenses.copy()
    
    count = 0
    total = 0.0
    total_expenses = 0.0

    if not df_stats.empty:
        # Conversion de la date pour manipulation
        try:
            df_stats['DateObj'] = pd.to_datetime(df_stats['Date'], format='%d/%m/%Y', errors='coerce')
        except Exception:
            pass
    
    if not df_exp_stats.empty:
        try:
            df_exp_stats['DateObj'] = pd.to_datetime(df_exp_stats['Date'], format='%d/%m/%Y', errors='coerce')
        except Exception:
            pass

    try:
        if view_type == "Mois":
            month_name = app.budget_month_var.get()
            month_index = MONTHS_FR.index(month_name) + 1
            if not df_stats.empty:
                df_stats = df_stats[df_stats['DateObj'].dt.month == month_index]
            if not df_exp_stats.empty:
                df_exp_stats = df_exp_stats[df_exp_stats['DateObj'].dt.month == month_index]
                
        elif view_type == "Période":
            start_month_name = app.budget_start_month_var.get()
            end_month_name = app.budget_end_month_var.get()
            start_month_index = MONTHS_FR.index(start_month_name) + 1
            end_month_index = MONTHS_FR.index(end_month_name) + 1
            
            if start_month_index > end_month_index:
                messagebox.showwarning("Période invalide", "Le mois de début ne peut pas être après le mois de fin.")
                return 

            months_in_range = range(start_month_index, end_month_index + 1)
            if not df_stats.empty:
                df_stats = df_stats[df_stats['DateObj'].dt.month.isin(months_in_range)]
            if not df_exp_stats.empty:
                df_exp_stats = df_exp_stats[df_exp_stats['DateObj'].dt.month.isin(months_in_range)]
    except Exception as e:
        print(f"Erreur lors du filtrage: {e}")

    if not df_stats.empty:
        count = len(df_stats)
        if 'Montant' in df_stats.columns:
            total = df_stats['Montant'].sum()
    
    if not df_exp_stats.empty and 'Montant' in df_exp_stats.columns:
        # On exclut les prélèvements personnels du calcul des charges professionnelles
        prof_expenses = df_exp_stats[df_exp_stats['Categorie'] != "Prélèvement Personnel"]
        total_expenses = prof_expenses['Montant'].sum()

    net_profit = total - total_expenses

    app.budget_count_label.configure(text=str(count))
    app.budget_total_label.configure(text=f"{total:.2f} €")
    app.budget_expenses_label.configure(text=f"{total_expenses:.2f} €")
    app.budget_net_label.configure(text=f"{net_profit:.2f} €", text_color="#2ecc71" if net_profit >= 0 else "#e74c3c")
    
    # --- Calcul Salaire Conseillé (Règle des 3 tiers) ---
    cotisations_paid = 0.0
    if not df_exp_stats.empty and 'Categorie' in df_exp_stats.columns:
        cotisations_paid = df_exp_stats[df_exp_stats['Categorie'] == 'Cotisations']['Montant'].sum()
    
    ops_paid = total_expenses - cotisations_paid
    one_third = total / 3.0
    prov_taxes = max(0.0, one_third - cotisations_paid)
    prov_ops = max(0.0, one_third - ops_paid)
    
    safe_salary = (total - total_expenses) - prov_taxes - prov_ops
    app.current_safe_salary = safe_salary
    app.budget_safe_salary_label.configure(text=f"{safe_salary:.2f} €", text_color="#2ecc71" if safe_salary >= 0 else "#e74c3c")
        
    app.budget_salary_entry.event_generate("<KeyRelease>") # Force update du solde

    # Sauvegarde les données actuelles pour l'export
    app.current_budget_df = df_stats

    # --- Mise à jour du Bilan Annuel ---
    total_ca_year = 0.0
    if not df_year.empty and 'Montant' in df_year.columns:
        total_ca_year = df_year['Montant'].sum()
        
    total_remu_year = 0.0
    if not df_expenses.empty and 'Montant' in df_expenses.columns:
        remu_expenses = df_expenses[df_expenses['Categorie'] == 'Prélèvement Personnel']
        total_remu_year = remu_expenses['Montant'].sum()
        
    app.annual_ca_brut = total_ca_year
    app.annual_remu = total_remu_year
    
    app.annual_ca_label.configure(text=f"{total_ca_year:.2f} €")
    app.annual_remu_label.configure(text=f"{total_remu_year:.2f} €")
    
    # Charger les paramètres manuels (Cotisations/Impôts)
    from opeyrateur_app.core.data_manager import load_annual_params
    params = load_annual_params(year)
    app.annual_cotis_entry.delete(0, 'end')
    app.annual_cotis_entry.insert(0, str(params.get('cotisations', 0.0)))
    app.annual_impots_entry.delete(0, 'end')
    app.annual_impots_entry.insert(0, str(params.get('impots', 0.0)))
    
    _update_annual_balance_calc(app, save=False)

    # --- Mise à jour du graphique (Toujours sur l'année pour voir l'évolution) ---
    _update_chart(app, df_year)
    
    # --- Mise à jour de la répartition ---
    _update_breakdown(app, df_stats)
    
    # --- Mise à jour de l'historique des salaires ---
    _update_salary_history(app, df_exp_stats)
    
    # --- Mise à jour des remboursements Perso ---
    _update_reimbursements(app, df_exp_stats)

def _update_breakdown(app, df):
    """Affiche la répartition du CA par prestation."""
    for widget in app.breakdown_frame.winfo_children():
        widget.destroy()
        
    if df.empty or 'Prestation' not in df.columns:
        ctk.CTkLabel(app.breakdown_frame, text="Aucune donnée pour cette période.", text_color="gray").pack(pady=20)
        return
        
    # Groupement par prestation
    breakdown = df.groupby('Prestation')['Montant'].sum().sort_values(ascending=False)
    total_ca = breakdown.sum()
    
    if total_ca == 0: return

    for prestation, montant in breakdown.items():
        percent = (montant / total_ca) * 100
        
        row = ctk.CTkFrame(app.breakdown_frame, fg_color="transparent")
        row.pack(fill="x", pady=5, padx=10)
        
        # Label et Montant
        header = ctk.CTkFrame(row, fg_color="transparent")
        header.pack(fill="x")
        ctk.CTkLabel(header, text=prestation, font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkLabel(header, text=f"{montant:.2f} € ({percent:.1f}%)").pack(side="right")
        
        # Barre de progression
        progress = ctk.CTkProgressBar(row, height=8, corner_radius=4)
        progress.pack(fill="x", pady=(2, 0))
        progress.set(percent / 100)
        # Couleur différente selon l'importance
        if percent > 50: progress.configure(progress_color="#2ecc71")
        elif percent > 20: progress.configure(progress_color="#3498db")
        else: progress.configure(progress_color="#95a5a6")

def _update_salary_history(app, df):
    """Affiche l'historique des prélèvements personnels."""
    for widget in app.salary_history_frame.winfo_children():
        widget.destroy()
        
    if df.empty or 'Categorie' not in df.columns:
        ctk.CTkLabel(app.salary_history_frame, text="-", text_color="gray").pack()
        return

    withdrawals = df[df['Categorie'] == "Prélèvement Personnel"]
    app.current_salary_history_df = withdrawals.copy() # Sauvegarde pour l'export PDF
    
    if withdrawals.empty:
        ctk.CTkLabel(app.salary_history_frame, text="Aucun prélèvement.", text_color="gray", font=ctk.CTkFont(size=11)).pack()
        return
        
    # Tri par date décroissante
    if 'DateObj' in withdrawals.columns:
        withdrawals = withdrawals.sort_values('DateObj', ascending=False)
        
    for _, row in withdrawals.iterrows():
        f = ctk.CTkFrame(app.salary_history_frame, fg_color="transparent")
        f.pack(fill="x", pady=2)
        ctk.CTkLabel(f, text=row['Date'], font=ctk.CTkFont(size=11)).pack(side="left")
        ctk.CTkLabel(f, text=f"{row['Montant']:.2f} €", font=ctk.CTkFont(size=11, weight="bold")).pack(side="right")

def _update_reimbursements(app, df):
    """Affiche les dépenses payées en Carte Perso et non remboursées."""
    for item in app.reimbursement_tree.get_children():
        app.reimbursement_tree.delete(item)
        
    if df.empty or 'Compte_Paiement' not in df.columns:
        app.reimbursement_total_label.configure(text="Total à rembourser : 0.00 €")
        return
        
    # Filtre: Carte Perso ET non remboursé
    if 'Est_Rembourse' not in df.columns:
        df['Est_Rembourse'] = 0
        
    pending = df[(df['Compte_Paiement'] == 'Carte Perso') & (df['Est_Rembourse'] == 0)]
    
    total = 0.0
    for _, row in pending.iterrows():
        try: montant = float(row['Montant'])
        except: montant = 0.0
        total += montant
        app.reimbursement_tree.insert("", "end", values=(row['Date'], row['Categorie'], row['Description'], f"{montant:.2f} €", row.get('ExpenseID', '')))
        
    app.reimbursement_total_label.configure(text=f"Total à rembourser : {total:.2f} €")

def _reimburse_selected(app):
    from tkinter import messagebox
    from opeyrateur_app.core.data_manager import mark_as_reimbursed, save_expense
    from datetime import datetime
    import uuid
    
    selected_items = app.reimbursement_tree.selection()
    if not selected_items:
        messagebox.showwarning("Sélection", "Veuillez sélectionner au moins une dépense à rembourser.")
        return
        
    ids = []
    total_amount = 0.0
    for item in selected_items:
        values = app.reimbursement_tree.item(item, "values")
        if len(values) > 4:
            ids.append(values[4])
            montant_str = values[3].replace(' €', '').replace(',', '.')
            try: total_amount += float(montant_str)
            except: pass
            
    if not ids: return
    
    if not messagebox.askyesno("Confirmation", f"Voulez-vous générer un remboursement tracable de {total_amount:.2f} € pour ces {len(ids)} dépense(s) ?\n\nCette somme sera enregistrée dans votre historique de Prélèvements Personnels afin d'apparaître sur le PDF."):
        return
        
    # 1. Génération de la trace comptable
    generated_id = str(uuid.uuid4())
    data = {
        "ExpenseID": generated_id,
        "Date": datetime.now().strftime("%d/%m/%Y"),
        "Categorie": "Prélèvement Personnel",
        "Description": f"Remboursement de frais avancés ({len(ids)} opération{'s' if len(ids)>1 else ''})",
        "Montant": total_amount,
        "ProofPath": None,
        "Compte_Paiement": "Compte Pro",
        "Est_Rembourse": 0
    }
    
    if save_expense(data):
        # 2. Marquer comme remboursé
        mark_as_reimbursed(ids)
        
        # 3. Stockage pour Ctrl+Z complet
        app.last_reimbursement_action = {
            "reimbursed_ids": ids,
            "generated_id": generated_id
        }
        
        calculate_budget(app)
        messagebox.showinfo("Succès", f"Remboursement de {total_amount:.2f} € validé et tracé !\n\nIl apparaît désormais dans l'historique de vos prélèvements. (Ctrl+Z pour l'annuler)")

def _undo_reimburse(app):
    """Annule la dernière action de remboursement."""
    action = getattr(app, 'last_reimbursement_action', None)
    if action:
        from opeyrateur_app.core.data_manager import unmark_as_reimbursed, delete_expense
        from tkinter import messagebox
        
        # 1. Démarque les dépenses
        unmark_as_reimbursed(action['reimbursed_ids'])
        
        # 2. Supprime la trace de prélèvement
        delete_expense({"ExpenseID": action['generated_id']})
        
        # 3. Vide l'historique undo
        app.last_reimbursement_action = None
        
        calculate_budget(app)
        messagebox.showinfo("Annulation", "Le remboursement a été annulé avec succès et la trace a été effacée de votre historique.")

def _update_chart(app, df):
    """Affiche un graphique de l'évolution du CA sur l'année."""
    import pandas as pd
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from opeyrateur_app.core.data_manager import MONTHS_FR

    # Nettoie le graphique précédent
    for widget in app.chart_frame.winfo_children():
        widget.destroy()

    if df.empty or 'Montant' not in df.columns:
        return

    try:
        # Assure que DateObj existe
        if 'DateObj' not in df.columns:
            df['DateObj'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')

        # Groupe par mois
        monthly_data = df.groupby(df['DateObj'].dt.month)['Montant'].sum()
        
        # Assure d'avoir les 12 mois (même vides)
        monthly_data = monthly_data.reindex(range(1, 13), fill_value=0)

        # Création de la figure
        fig, ax = plt.subplots(figsize=(5, 3), dpi=100)
        months_labels = [m[:3] for m in MONTHS_FR] # Jan, Fév, ...
        ax.bar(months_labels, monthly_data.values, color='#3498db')
        ax.set_title("Évolution du Chiffre d'Affaires (encaissé)")
        ax.set_ylabel("Montant (€)")
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Intégration dans Tkinter
        canvas = FigureCanvasTkAgg(fig, master=app.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    except Exception as e:
        print(f"Erreur graphique: {e}")

def _export_budget(app):
    """Exporte les données affichées vers un fichier Excel."""
    if not hasattr(app, 'current_budget_df') or app.current_budget_df.empty:
        messagebox.showwarning("Export", "Aucune donnée à exporter.")
        return
    
    from opeyrateur_app.core.data_manager import MONTHS_FR

    # Création du dossier 'budget' s'il n'existe pas
    os.makedirs(config.BUDGET_DIR, exist_ok=True)

    # Nommage automatique du fichier
    year = app.budget_year_var.get()
    view_type = app.budget_view_type.get()
    if view_type == "Mois":
        month = app.budget_month_var.get()
        filename = f"Budget_{year}_{month}.xlsx"
    elif view_type == "Période":
        start_month_name = app.budget_start_month_var.get()
        end_month_name = app.budget_end_month_var.get()
        start_month_index = MONTHS_FR.index(start_month_name)
        end_month_index = MONTHS_FR.index(end_month_name)
        if start_month_index > end_month_index:
            messagebox.showwarning("Période invalide", "Le mois de début ne peut pas être après le mois de fin.")
            return

        filename = f"Budget_{year}_{start_month_name[:3]}-{end_month_name[:3]}.xlsx"
    else: # Année
        filename = f"Budget_{year}.xlsx"
    
    full_path = os.path.join(config.BUDGET_DIR, filename)

    try:
        # Supprime la colonne temporaire DateObj si elle existe
        df_to_export = app.current_budget_df.copy()
        if 'DateObj' in df_to_export.columns:
            del df_to_export['DateObj']
        
        df_to_export.to_excel(full_path, index=False)
        messagebox.showinfo("Succès", f"Export réussi dans :\n{full_path}")
        
        # Ouvre le dossier pour faciliter l'accès
        os.startfile(config.BUDGET_DIR)
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible d'exporter : {e}")

def _view_budget_pdf(app):
    """Génère et affiche le PDF du budget pour la vue actuelle."""
    if not hasattr(app, 'current_budget_df') or app.current_budget_df.empty:
        messagebox.showwarning("Visualisation", "Aucune donnée à visualiser.")
        return
    
    from opeyrateur_app.core.data_manager import MONTHS_FR
    from opeyrateur_app.services.pdf_generator import generate_budget_report
    from opeyrateur_app.ui.components.pdf_viewer import PDFViewer

    year = app.budget_year_var.get()
    month = None
    quarter = None
    view_type = app.budget_view_type.get()
    
    download_filename = f"Registre_Recettes_{year}"

    if view_type == "Mois":
        month = app.budget_month_var.get()
        download_filename += f"_{month}"
    elif view_type == "Période":
        start_month_name = app.budget_start_month_var.get()
        end_month_name = app.budget_end_month_var.get()
        start_month_index = MONTHS_FR.index(start_month_name)
        end_month_index = MONTHS_FR.index(end_month_name)
        if start_month_index > end_month_index:
            messagebox.showwarning("Période invalide", "Le mois de début ne peut pas être après le mois de fin.")
            return

        quarter = f"{start_month_name} à {end_month_name}" # For PDF title
        download_filename += f"_{start_month_name[:3]}-{end_month_name[:3]}"

    download_filename += ".pdf"

    try:
        path = generate_budget_report(year, month, quarter, app.current_budget_df)
        PDFViewer(app, path, download_filename=download_filename)
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de visualiser le PDF : {e}")

def _export_fec(app):
    """Génère un fichier FEC (Fichier des Écritures Comptables) pour l'année sélectionnée."""
    import pandas as pd
    from opeyrateur_app.core.data_manager import load_year_data
    
    year = app.budget_year_var.get()
    df = load_year_data(year)
    
    if df.empty:
        messagebox.showwarning("Export FEC", f"Aucune donnée trouvée pour l'année {year}.")
        return

    # Récupération du SIREN pour le nommage du fichier
    pdf_info = settings_manager.get_pdf_info()
    siret = pdf_info.get('siret', '').replace(' ', '')
    siren = siret[:9] if len(siret) >= 9 else "000000000"
    
    try:
        lines = []
        # En-tête officiel FEC (18 champs)
        header = [
            "JournalCode", "JournalLib", "EcritureNum", "EcritureDate", 
            "CompteNum", "CompteLib", "CompteAuxNum", "CompteAuxLib", 
            "PieceRef", "PieceDate", "EcritureLib", "Debit", "Credit", 
            "EcritureLet", "DateLet", "ValidDate", "Montantdevise", "Idevise"
        ]
        lines.append("|".join(header))
        
        # Tri par date puis par ID pour la chronologie
        if 'Date' in df.columns:
            df['DateObj'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
            df = df.sort_values(by=['DateObj', 'ID'])
        
        ecriture_counter = 0
        for _, row in df.iterrows():
            try:
                ecriture_counter += 1
                date_str = row['Date']
                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                fec_date = date_obj.strftime("%Y%m%d")
                ref_piece = str(row['ID'])
                ecriture_num = str(ecriture_counter)
                
                # Fonction de nettoyage
                def clean_txt(t):
                    return str(t).replace('|', ' ').replace('\n', ' ').replace('\r', '').strip() if t else ""

                # Formatage montant (virgule comme séparateur décimal)
                raw_montant = row.get('Montant', 0.0)
                if isinstance(raw_montant, str):
                    raw_montant = raw_montant.replace(',', '.')
                montant_float = float(raw_montant) if pd.notnull(raw_montant) else 0.0
                
                montant_str = f"{montant_float:.2f}".replace('.', ',')
                zero_str = "0,00"
                
                nom_patient = f"{clean_txt(row.get('Prenom', ''))} {clean_txt(row.get('Nom', ''))}".strip()
                libelle = f"Facture {ref_piece} - {nom_patient}"
                libelle = libelle[:200]
                
                # Préparation des lignes (Débit et Crédit)
                line_client = ["VT", "Ventes", ecriture_num, fec_date, "411000", "Clients", "", "", ref_piece, fec_date, libelle, montant_str, zero_str, "", "", fec_date, "", ""]
                line_prod = ["VT", "Ventes", ecriture_num, fec_date, "706000", "Prestations de services", "", "", ref_piece, fec_date, libelle, zero_str, montant_str, "", "", fec_date, "", ""]
                
                # Ajout groupé pour garantir l'équilibre
                lines.append("|".join(line_client))
                lines.append("|".join(line_prod))
                
            except Exception:
                continue
        
        # --- Validation du fichier FEC ---
        from opeyrateur_app.utils.utils import validate_fec_content, FECPreviewWindow
        is_valid, errors = validate_fec_content(lines)
        
        if not is_valid:
            error_msg = "\n".join(errors[:10])
            if len(errors) > 10: error_msg += "\n..."
            if not messagebox.askyesno("Validation FEC échouée", f"Le fichier contient des erreurs :\n{error_msg}\n\nVoulez-vous quand même l'enregistrer ?"):
                return

        # --- Prévisualisation et Enregistrement ---
        def save_action():
            filename = f"{siren}FEC{datetime.now().strftime('%Y%m%d')}.txt"
            filepath = filedialog.asksaveasfilename(
                defaultextension=".txt", initialfile=filename, title="Enregistrer le fichier FEC (Format Légal)", filetypes=[("Fichier FEC", "*.txt"), ("Tous les fichiers", "*.*")]
            )
            if not filepath: return

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))
                
            messagebox.showinfo("Succès", f"Fichier FEC généré avec succès :\n{filepath}")
            
        FECPreviewWindow(app, lines, save_action)
        
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de générer le fichier FEC :\n{e}")

def _save_salary_expense(app):
    """Enregistre le salaire saisi comme une dépense."""
    from opeyrateur_app.core.data_manager import save_expense
    try:
        amount_str = app.budget_salary_entry.get().replace(',', '.')
        if not amount_str: return
        amount = float(amount_str)
        
        if amount <= 0:
            messagebox.showwarning("Montant invalide", "Le montant doit être positif.")
            return

        if not messagebox.askyesno("Confirmation", f"Voulez-vous enregistrer un prélèvement personnel de {amount:.2f} € ?\nCela créera une dépense dans la catégorie 'Prélèvement Personnel'."):
            return

        data = {
            "Date": datetime.now().strftime("%d/%m/%Y"),
            "Categorie": "Prélèvement Personnel",
            "Description": "Salaire / Rémunération",
            "Montant": amount,
            "ProofPath": None
        }
        
        if save_expense(data):
            messagebox.showinfo("Succès", "Prélèvement enregistré.")
            calculate_budget(app) # Rafraîchit les calculs
    except ValueError:
        messagebox.showerror("Erreur", "Montant invalide.")

def _export_salary_history_pdf(app):
    """Génère un PDF avec l'historique des prélèvements personnels."""
    if not hasattr(app, 'current_salary_history_df') or app.current_salary_history_df.empty:
        messagebox.showwarning("Export", "Aucun prélèvement à exporter pour cette période.")
        return

    from opeyrateur_app.services.pdf_generator import generate_expenses_report
    from opeyrateur_app.ui.components.pdf_viewer import PDFViewer
    
    year = app.budget_year_var.get()
    title = f"Relevé des Prélèvements Personnels - {year}"
    
    # On réutilise le générateur de rapport de frais qui est adapté
    path = generate_expenses_report(title, app.current_salary_history_df, year)
    
    try:
        PDFViewer(app, path, download_filename=os.path.basename(path))
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de visualiser le PDF : {e}")

def _update_annual_balance_calc(app, save=True):
    """Met à jour le reste à vivre (Trésorerie) du Bilan Annuel."""
    from opeyrateur_app.core.data_manager import save_annual_params
    try:
        c_str = app.annual_cotis_entry.get().replace(',', '.')
        i_str = app.annual_impots_entry.get().replace(',', '.')
        cotis = float(c_str) if c_str else 0.0
        impots = float(i_str) if i_str else 0.0
        
        ca_brut = getattr(app, 'annual_ca_brut', 0.0)
        remu = getattr(app, 'annual_remu', 0.0)
        
        reste = ca_brut - cotis - impots - remu
        
        app.annual_reste_label.configure(text=f"{reste:.2f} €", text_color="#2ecc71" if reste >= 0 else "#e74c3c")
        
        if save:
            year = app.budget_year_var.get()
            save_annual_params(year, {"cotisations": cotis, "impots": impots})
    except ValueError:
        pass