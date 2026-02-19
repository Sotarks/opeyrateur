import customtkinter as ctk
from datetime import datetime
from tkinter import filedialog, messagebox
import os
from . import config
from . import settings_manager

def create_budget_tab(app):
    """Crée les widgets pour l'onglet 'Budget'."""
    app.budget_tab.grid_columnconfigure(0, weight=1)
    
    # --- Cadre principal pour les contrôles ---
    controls_frame = ctk.CTkFrame(app.budget_tab, corner_radius=10)
    controls_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
    controls_frame.grid_columnconfigure((0, 1), weight=1)

    # --- Colonne de gauche pour les filtres ---
    filter_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
    filter_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    filter_frame.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(filter_frame, text="Période", font=app.font_large).pack(anchor="w", pady=(0, 5))

    # Type de vue (Année ou Mois)
    app.budget_view_type = ctk.CTkSegmentedButton(filter_frame, values=["Année", "Mois", "Période"], command=lambda v: _update_budget_inputs(app))
    app.budget_view_type.pack(fill="x", pady=5)
    app.budget_view_type.set("Mois")

    # Frame pour les menus déroulants
    dropdown_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
    dropdown_frame.pack(fill="x", pady=5)
    dropdown_frame.grid_columnconfigure((0, 1), weight=1)
    dropdown_frame.grid_rowconfigure((0, 1), weight=0)

    # Dropdowns pour Année et Mois
    app.budget_year_var = ctk.StringVar()
    app.budget_month_var = ctk.StringVar()
    app.budget_start_month_var = ctk.StringVar()
    app.budget_end_month_var = ctk.StringVar()
    
    from .data_manager import get_available_years, MONTHS_FR
    years = get_available_years()
    if not years:
        years = [str(datetime.now().year)]
    app.budget_year_var.set(years[0])
    current_month_name = MONTHS_FR[datetime.now().month - 1]
    app.budget_month_var.set(current_month_name)
    app.budget_start_month_var.set(current_month_name)
    app.budget_end_month_var.set(current_month_name)

    app.budget_year_menu = ctk.CTkOptionMenu(dropdown_frame, variable=app.budget_year_var, values=years)
    # Le placement grid sera géré par _update_budget_inputs

    app.budget_month_menu = ctk.CTkOptionMenu(dropdown_frame, variable=app.budget_month_var, values=MONTHS_FR)
    # Le placement grid sera géré par _update_budget_inputs
    
    app.budget_start_month_menu = ctk.CTkOptionMenu(dropdown_frame, variable=app.budget_start_month_var, values=MONTHS_FR)
    app.budget_end_month_menu = ctk.CTkOptionMenu(dropdown_frame, variable=app.budget_end_month_var, values=MONTHS_FR)

    # --- Colonne de droite pour les actions ---
    actions_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
    actions_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
    actions_frame.grid_columnconfigure(0, weight=1)
    actions_frame.grid_rowconfigure((0, 1, 2), weight=0)

    ctk.CTkButton(actions_frame, text="Calculer", command=lambda: calculate_budget(app), font=app.font_button, height=40).pack(fill="x", pady=5)
    ctk.CTkButton(actions_frame, text="Visualiser PDF (Vue actuelle)", command=lambda: _view_budget_pdf(app), font=app.font_button, height=40).pack(fill="x", pady=5)
    ctk.CTkButton(actions_frame, text="Générer Excel", command=lambda: _export_budget(app), fg_color="#34D399", hover_color="#10B981", font=app.font_button, height=40).pack(fill="x", pady=5)
    ctk.CTkButton(actions_frame, text="Export Légal (.fec)", command=lambda: _export_fec(app), fg_color="#546E7A", hover_color="#455A64", font=app.font_button, height=40).pack(fill="x", pady=5)

    # --- Frame Résultats ---
    results_frame = ctk.CTkFrame(app.budget_tab, corner_radius=10)
    results_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
    results_frame.grid_columnconfigure((0, 1), weight=1)

    ctk.CTkLabel(results_frame, text="Résultats", font=app.font_large).grid(row=0, column=0, columnspan=2, pady=(10, 15), padx=10, sticky="w")

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
    app.budget_month_menu.grid_forget()
    app.budget_start_month_menu.grid_forget()
    app.budget_end_month_menu.grid_forget()
    if view_type == "Année":
        app.budget_year_menu.grid(row=0, column=0, columnspan=2, padx=0, pady=0, sticky="ew")
    elif view_type == "Mois":
        app.budget_year_menu.grid(row=0, column=0, columnspan=1, padx=(0, 5), pady=0, sticky="ew")
        app.budget_month_menu.grid(row=0, column=1, padx=(5, 0), pady=0, sticky="ew")
    elif view_type == "Période":
        app.budget_year_menu.grid(row=0, column=0, columnspan=2, padx=0, pady=(0, 5), sticky="ew")
        app.budget_start_month_menu.grid(row=1, column=0, padx=(0, 5), pady=0, sticky="ew")
        app.budget_end_month_menu.grid(row=1, column=1, padx=(5, 0), pady=0, sticky="ew")

def calculate_budget(app):
    """Calcule et affiche les statistiques."""
    import pandas as pd
    from .data_manager import load_year_data, MONTHS_FR

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
        elif view_type == "Période":
            start_month_name = app.budget_start_month_var.get()
            end_month_name = app.budget_end_month_var.get()
            try:
                start_month_index = MONTHS_FR.index(start_month_name) + 1
                end_month_index = MONTHS_FR.index(end_month_name) + 1
                
                if start_month_index > end_month_index:
                    messagebox.showwarning("Période invalide", "Le mois de début ne peut pas être après le mois de fin.")
                    return 

                months_in_range = range(start_month_index, end_month_index + 1)
                df_stats = df_stats[df_stats['DateObj'].dt.month.isin(months_in_range)]
            except Exception as e:
                print(f"Erreur lors du filtrage par période: {e}")

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
    import pandas as pd
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from .data_manager import MONTHS_FR

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
    
    from .data_manager import MONTHS_FR

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
    
    from .data_manager import MONTHS_FR
    from .pdf_generator import generate_budget_report
    from .pdf_viewer import PDFViewer

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
    from .data_manager import load_year_data
    
    year = app.budget_year_var.get()
    df = load_year_data(year)
    
    if df.empty:
        messagebox.showwarning("Export FEC", f"Aucune donnée trouvée pour l'année {year}.")
        return

    # Récupération du SIREN pour le nommage du fichier
    pdf_info = settings_manager.get_pdf_info()
    siret = pdf_info.get('siret', '').replace(' ', '')
    siren = siret[:9] if len(siret) >= 9 else "000000000"
    
    # Nom du fichier selon norme : SirenFECYYYYMMDD.txt
    filename = f"{siren}FEC{datetime.now().strftime('%Y%m%d')}.txt"
    
    filepath = filedialog.asksaveasfilename(
        defaultextension=".txt",
        initialfile=filename,
        title="Enregistrer le fichier FEC (Format Légal)",
        filetypes=[("Fichier FEC", "*.txt"), ("Tous les fichiers", "*.*")]
    )
    
    if not filepath:
        return

    try:
        lines = []
        # En-tête officiel FEC (18 champs)
        header = [
            "JournalCode", "JournalLib", "EcritureNum", "EcritureDate", 
            "CompteNum", "CompteLib", "CompteAuxNum", "CompteAuxLib", 
            "PieceRef", "PieceDate", "EcritureLib", "Debit", "Credit", 
            "EcritureLet", "DateLet", "ValidDate", "Montantdevise", "Idevise"
        ]
        lines.append("\t".join(header))
        
        # Tri par date puis par ID pour la chronologie
        if 'Date' in df.columns:
            df['DateObj'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
            df = df.sort_values(by=['DateObj', 'ID'])
        
        for _, row in df.iterrows():
            try:
                date_str = row['Date']
                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                fec_date = date_obj.strftime("%Y%m%d")
                ref_piece = str(row['ID'])
                
                # Formatage montant (virgule comme séparateur décimal)
                montant_float = float(row['Montant']) if pd.notnull(row['Montant']) else 0.0
                montant_str = f"{montant_float:.2f}".replace('.', ',')
                zero_str = "0,00"
                
                nom_patient = f"{row.get('Prenom', '')} {row.get('Nom', '')}".strip()
                libelle = f"Facture {ref_piece} - {nom_patient}"
                
                # Écriture 1 : Client (Debit 411)
                line_client = ["VT", "Ventes", ref_piece, fec_date, "411000", "Clients", "", "", ref_piece, fec_date, libelle, montant_str, zero_str, "", "", fec_date, "", ""]
                lines.append("\t".join(line_client))
                
                # Écriture 2 : Produit (Credit 706)
                line_prod = ["VT", "Ventes", ref_piece, fec_date, "706000", "Prestations de services", "", "", ref_piece, fec_date, libelle, zero_str, montant_str, "", "", fec_date, "", ""]
                lines.append("\t".join(line_prod))
                
            except Exception:
                continue
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
            
        messagebox.showinfo("Succès", f"Fichier FEC généré avec succès :\n{filepath}")
        
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de générer le fichier FEC :\n{e}")