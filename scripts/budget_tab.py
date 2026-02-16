import customtkinter as ctk
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog, messagebox
import os
from . import config
from .data_manager import get_available_years, load_year_data, MONTHS_FR
from .pdf_generator import generate_budget_report

def create_budget_tab(app):
    """Crée les widgets pour l'onglet 'Budget'."""
    app.budget_tab.grid_columnconfigure(0, weight=1)
    
    # --- Frame de sélection ---
    selection_frame = ctk.CTkFrame(app.budget_tab, corner_radius=10)
    selection_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
    selection_frame.grid_columnconfigure((0, 1), weight=1)

    ctk.CTkLabel(selection_frame, text="Période", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(10, 5))

    # Type de vue (Année ou Mois)
    app.budget_view_type = ctk.CTkSegmentedButton(selection_frame, values=["Année", "Mois"], command=lambda v: _update_budget_inputs(app))
    app.budget_view_type.grid(row=1, column=0, columnspan=2, pady=5)
    app.budget_view_type.set("Mois")

    # Dropdowns pour Année et Mois
    app.budget_year_var = ctk.StringVar()
    app.budget_month_var = ctk.StringVar()
    
    years = get_available_years()
    if not years:
        years = [str(datetime.now().year)]
    app.budget_year_var.set(years[0])
    app.budget_month_var.set(MONTHS_FR[datetime.now().month - 1])

    app.budget_year_menu = ctk.CTkOptionMenu(selection_frame, variable=app.budget_year_var, values=years)
    # Le placement grid sera géré par _update_budget_inputs

    app.budget_month_menu = ctk.CTkOptionMenu(selection_frame, variable=app.budget_month_var, values=MONTHS_FR)
    # Le placement grid sera géré par _update_budget_inputs

    # Bouton Calculer
    ctk.CTkButton(selection_frame, text="Calculer", command=lambda: calculate_budget(app)).grid(row=3, column=0, columnspan=2, pady=(10, 5), padx=20, sticky="ew")

    # Boutons Exporter
    ctk.CTkButton(selection_frame, text="Générer Excel", command=lambda: _export_budget(app), fg_color="green").grid(row=4, column=0, padx=(20, 5), pady=(5, 10), sticky="ew")
    ctk.CTkButton(selection_frame, text="Générer PDF (Vue actuelle)", command=lambda: _export_budget_pdf(app), fg_color="#c0392b").grid(row=4, column=1, padx=(5, 20), pady=(5, 10), sticky="ew")
    ctk.CTkButton(selection_frame, text="Générer PDF (Registre annuel)", command=lambda: _export_annual_report(app), fg_color="#c0392b").grid(row=5, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")

    # --- Frame Résultats ---
    results_frame = ctk.CTkFrame(app.budget_tab, corner_radius=10)
    results_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
    results_frame.grid_columnconfigure((0, 1), weight=1)

    ctk.CTkLabel(results_frame, text="Résultats", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(10, 15))

    ctk.CTkLabel(results_frame, text="Nombre de consultations :").grid(row=1, column=0, sticky="e", padx=10, pady=5)
    app.budget_count_label = ctk.CTkLabel(results_frame, text="0", font=ctk.CTkFont(size=14, weight="bold"))
    app.budget_count_label.grid(row=1, column=1, sticky="w", padx=10, pady=5)

    ctk.CTkLabel(results_frame, text="Total Brut :").grid(row=2, column=0, sticky="e", padx=10, pady=5)
    app.budget_total_label = ctk.CTkLabel(results_frame, text="0.00 €", font=ctk.CTkFont(size=14, weight="bold"), text_color="#2ecc71")
    app.budget_total_label.grid(row=2, column=1, sticky="w", padx=10, pady=5)

    # --- Frame Graphique ---
    app.chart_frame = ctk.CTkFrame(app.budget_tab, corner_radius=10)
    app.chart_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
    app.budget_tab.grid_rowconfigure(2, weight=1)

    # Initialisation de l'affichage
    _update_budget_inputs(app)

def _update_budget_inputs(app):
    """Affiche ou masque le menu des mois selon la vue choisie."""
    view_type = app.budget_view_type.get()
    if view_type == "Année":
        app.budget_month_menu.grid_forget()
        app.budget_year_menu.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
    else:
        app.budget_year_menu.grid(row=2, column=0, columnspan=1, padx=5, pady=10, sticky="ew")
        app.budget_month_menu.grid(row=2, column=1, padx=5, pady=10, sticky="ew")

def calculate_budget(app):
    """Calcule et affiche les statistiques."""
    year = app.budget_year_var.get()
    view_type = app.budget_view_type.get()
    
    # Charge les données de l'année
    df_year = load_year_data(year)
    
    # --- FILTRE IMPAYÉS ---
    # On exclut les factures dont le statut est "Impayé"
    if not df_year.empty and 'Methode_Paiement' in df_year.columns:
        df_year = df_year[df_year['Methode_Paiement'] != 'Impayé'].copy()
    
    # Prépare les données pour les statistiques (filtrage mois si nécessaire)
    df_stats = df_year.copy()
    
    count = 0
    total = 0.0

    if not df_stats.empty:
        # Conversion de la date pour manipulation
        try:
            df_stats['DateObj'] = pd.to_datetime(df_stats['Date'], format='%d/%m/%Y', errors='coerce')
        except Exception:
            pass

        if view_type == "Mois":
            month_name = app.budget_month_var.get()
            try:
                # Filtre par le mois sélectionné
                month_index = MONTHS_FR.index(month_name) + 1
                df_stats = df_stats[df_stats['DateObj'].dt.month == month_index]
            except Exception as e:
                print(f"Erreur lors du filtrage par date: {e}")
                df_stats = pd.DataFrame()

        count = len(df_stats)
        if 'Montant' in df_stats.columns:
            total = df_stats['Montant'].sum()

    app.budget_count_label.configure(text=str(count))
    app.budget_total_label.configure(text=f"{total:.2f} €")
    
    # Sauvegarde les données actuelles pour l'export
    app.current_budget_df = df_stats

    # --- Mise à jour du graphique (Toujours sur l'année pour voir l'évolution) ---
    _update_chart(app, df_year)

def _update_chart(app, df):
    """Affiche un graphique de l'évolution du CA sur l'année."""
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

    # Création du dossier 'budget' s'il n'existe pas
    os.makedirs(config.BUDGET_DIR, exist_ok=True)

    # Nommage automatique du fichier
    year = app.budget_year_var.get()
    if app.budget_view_type.get() == "Mois":
        month = app.budget_month_var.get()
        filename = f"Budget_{year}_{month}.xlsx"
    else:
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

def _export_budget_pdf(app):
    """Exporte les données affichées vers un fichier PDF."""
    if not hasattr(app, 'current_budget_df') or app.current_budget_df.empty:
        messagebox.showwarning("Export", "Aucune donnée à exporter.")
        return

    year = app.budget_year_var.get()
    month = None
    if app.budget_view_type.get() == "Mois":
        month = app.budget_month_var.get()

    try:
        path = generate_budget_report(year, month, app.current_budget_df)
        messagebox.showinfo("Succès", f"Export PDF réussi :\n{path}")
        os.startfile(os.path.dirname(path))
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible d'exporter en PDF : {e}")

def _export_annual_report(app):
    """Génère et exporte le registre des recettes pour toute l'année sélectionnée."""
    year = app.budget_year_var.get()
    
    # Charge les données de l'année entière
    df_year = load_year_data(year)
    
    # Filtre les impayés
    if not df_year.empty and 'Methode_Paiement' in df_year.columns:
        df_year = df_year[df_year['Methode_Paiement'] != 'Impayé'].copy()
    
    if df_year.empty:
        messagebox.showwarning("Export", f"Aucune facture payée trouvée pour l'année {year}.")
        return

    try:
        path = generate_budget_report(year, None, df_year)
        messagebox.showinfo("Succès", f"Registre annuel généré :\n{path}")
        os.startfile(os.path.dirname(path))
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de générer le registre : {e}")