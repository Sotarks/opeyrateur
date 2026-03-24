import customtkinter as ctk
from datetime import datetime, timedelta
import calendar
import pandas as pd
from opeyrateur_app.core.data_manager import load_expenses, MONTHS_FR, save_agenda_note, load_agenda_notes, delete_agenda_note
from opeyrateur_app.core import settings_manager

def create_calendar_tab(app):
    """Crée l'interface de l'onglet Agenda."""
    # Configuration : Calendrier (Gauche) | Détails (Droite)
    app.calendar_tab.grid_columnconfigure(0, weight=1)
    app.calendar_tab.grid_columnconfigure(1, weight=0, minsize=350)
    app.calendar_tab.grid_rowconfigure(0, weight=1)

    # --- Variables d'état ---
    app.cal_view_date = datetime.now()
    app.cal_selected_date = datetime.now()
    app.cal_day_map = {} # Pour le Drag & Drop : mapping widget -> date

    # =================================================================================
    # 1. CALENDRIER (GAUCHE)
    # =================================================================================
    cal_container = ctk.CTkFrame(app.calendar_tab, fg_color="transparent")
    cal_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
    cal_container.grid_rowconfigure(1, weight=1)
    cal_container.grid_columnconfigure(0, weight=1)

    # --- En-tête (Mois/Année + Navigation) ---
    header_frame = ctk.CTkFrame(cal_container, fg_color="transparent")
    header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
    
    ctk.CTkButton(header_frame, text="◀", width=40, command=lambda: _change_month(app, -1)).pack(side="left")
    app.cal_month_label = ctk.CTkLabel(header_frame, text="Mois Année", font=("Montserrat", 20, "bold"))
    app.cal_month_label.pack(side="left", padx=20)
    ctk.CTkButton(header_frame, text="▶", width=40, command=lambda: _change_month(app, 1)).pack(side="left")
    
    ctk.CTkButton(header_frame, text="Aujourd'hui", command=lambda: _go_to_today(app), fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(side="right")

    # --- Grille du Calendrier ---
    app.cal_grid_frame = ctk.CTkFrame(cal_container, fg_color=("white", "gray20"), corner_radius=15)
    app.cal_grid_frame.grid(row=1, column=0, sticky="nsew")
    
    # Configuration de la grille 7x7 (Jours semaine + 6 semaines max)
    for i in range(7):
        app.cal_grid_frame.grid_columnconfigure(i, weight=1)
    for i in range(7): # 1 ligne header + 6 lignes jours
        app.cal_grid_frame.grid_rowconfigure(i, weight=1)

    # En-têtes des jours
    days_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    for i, day in enumerate(days_fr):
        ctk.CTkLabel(app.cal_grid_frame, text=day, font=("Montserrat", 12, "bold"), text_color="gray").grid(row=0, column=i, pady=10)

    # =================================================================================
    # 2. BARRE LATÉRALE DÉTAILS (DROITE)
    # =================================================================================
    sidebar = ctk.CTkFrame(app.calendar_tab, corner_radius=0, fg_color=("gray90", "gray16"))
    sidebar.grid(row=0, column=1, sticky="nsew")
    sidebar.grid_rowconfigure(4, weight=1)
    sidebar.grid_columnconfigure(0, weight=1)

    # --- Filtres ---
    filter_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
    filter_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
    
    ctk.CTkLabel(filter_frame, text="Filtres", font=app.font_bold).pack(anchor="w")
    
    app.cal_search_var = ctk.StringVar()
    search_entry = ctk.CTkEntry(filter_frame, placeholder_text="Mot-clé...", textvariable=app.cal_search_var)
    search_entry.pack(fill="x", pady=(5, 5))
    search_entry.bind("<KeyRelease>", lambda e: _refresh_all(app))

    app.cal_type_var = ctk.StringVar(value="Tout")
    type_menu = ctk.CTkOptionMenu(filter_frame, values=["Tout", "Notes", "Factures", "Frais"], variable=app.cal_type_var, command=lambda v: _refresh_all(app))
    type_menu.pack(fill="x", pady=(0, 10))

    # Separator
    ctk.CTkFrame(sidebar, height=2, fg_color=("gray80", "gray30")).grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))

    ctk.CTkLabel(sidebar, text="Détails de la journée", font=app.font_large).grid(row=2, column=0, pady=(0, 2), padx=20, sticky="w")
    app.cal_selected_date_label = ctk.CTkLabel(sidebar, text="Sélectionnez un jour", font=app.font_title, text_color="#3498db")
    app.cal_selected_date_label.grid(row=3, column=0, pady=(0, 10), padx=20, sticky="w")

    app.cal_details_scroll = ctk.CTkScrollableFrame(sidebar, fg_color="transparent", label_text="")
    app.cal_details_scroll.grid(row=4, column=0, sticky="nsew", padx=10, pady=(0, 10))

    # Bouton Ajouter Note (en bas)
    ctk.CTkButton(sidebar, text="+ Ajouter Note / RDV", command=lambda: _open_add_note_dialog(app), font=app.font_button, fg_color="#546E7A").grid(row=5, column=0, padx=20, pady=20, sticky="ew")

    # Initialisation
    _refresh_calendar_view(app)
    _update_details_sidebar(app, datetime.now())

def _change_month(app, delta):
    """Change le mois affiché."""
    month = app.cal_view_date.month + delta
    year = app.cal_view_date.year
    
    if month > 12:
        month = 1
        year += 1
    elif month < 1:
        month = 12
        year -= 1
        
    app.cal_view_date = app.cal_view_date.replace(year=year, month=month, day=1)
    _refresh_calendar_view(app)

def _go_to_today(app):
    app.cal_view_date = datetime.now()
    app.cal_selected_date = datetime.now()
    _refresh_calendar_view(app)
    _update_details_sidebar(app, app.cal_selected_date)

def _refresh_calendar_view(app):
    """Redessine la grille du calendrier avec les données."""
    # Mise à jour du titre
    app.cal_day_map = {} # Réinitialise le mapping
    month_name = MONTHS_FR[app.cal_view_date.month - 1]
    app.cal_month_label.configure(text=f"{month_name} {app.cal_view_date.year}")

    # Nettoyage de la grille (sauf headers)
    for widget in app.cal_grid_frame.winfo_children():
        info = widget.grid_info()
        if int(info['row']) > 0:
            widget.destroy()

    # Chargement des données
    year = app.cal_view_date.year
    month = app.cal_view_date.month
    
    invoices_df = app._load_data_with_cache(year=year)
    expenses_df = load_expenses(year)
    notes_list = load_agenda_notes(year)
    working_hours = settings_manager.get_working_hours()
    
    # --- Filtrage ---
    invoices_df, expenses_df, notes_list = _filter_data(app, invoices_df, expenses_df, notes_list)

    # Filtrage pour le mois en cours
    if not invoices_df.empty:
        invoices_df['DateObj'] = pd.to_datetime(invoices_df['Date'], format='%d/%m/%Y', errors='coerce')
        invoices_df = invoices_df[invoices_df['DateObj'].dt.month == month]
    
    if not expenses_df.empty:
        expenses_df['DateObj'] = pd.to_datetime(expenses_df['Date'], format='%d/%m/%Y', errors='coerce')
        expenses_df = expenses_df[expenses_df['DateObj'].dt.month == month]

    # Génération du calendrier
    cal = calendar.monthcalendar(year, month)
    
    for r, week in enumerate(cal):
        for c, day in enumerate(week):
            if day == 0: continue
            
            # Cadre du jour
            day_frame = ctk.CTkFrame(app.cal_grid_frame, fg_color=("gray95", "gray25"), corner_radius=8, border_width=1, border_color=("gray85", "gray30"))
            day_frame.grid(row=r+1, column=c, sticky="nsew", padx=2, pady=2)
            app.cal_day_map[day_frame] = datetime(year, month, day) # Enregistre pour le drop
            
            # Numéro du jour
            is_today = (day == datetime.now().day and month == datetime.now().month and year == datetime.now().year)
            is_selected = (day == app.cal_selected_date.day and month == app.cal_selected_date.month and year == app.cal_selected_date.year)
            
            # Vérification jour travaillé (pour griser le fond)
            current_date = datetime(year, month, day)
            day_idx = str(current_date.weekday())
            is_working_day = bool(working_hours.get(day_idx, ""))
            
            bg_color = ("gray95", "gray25") if is_working_day else ("gray85", "gray18")
            day_color = "#3498db" if is_today else ("black", "white") if is_working_day else "gray"
            
            day_frame.configure(fg_color=bg_color)
            if is_selected: day_frame.configure(border_color="#3498db", border_width=2)
            
            ctk.CTkLabel(day_frame, text=str(day), font=("Montserrat", 14, "bold"), text_color=day_color).pack(anchor="nw", padx=5, pady=2)

            # Factures
            day_inv = pd.DataFrame()
            if not invoices_df.empty:
                day_inv = invoices_df[invoices_df['DateObj'].dt.day == day]
            
            if not day_inv.empty:
                count = len(day_inv)
                total = day_inv['Montant'].sum()
                has_unpaid = 'Impayé' in day_inv['Methode_Paiement'].values
                color = "#e74c3c" if has_unpaid else "#2ecc71"
                ctk.CTkLabel(day_frame, text=f"• {count} Fact. ({total:.0f}€)", font=("Montserrat", 10), text_color=color).pack(anchor="w", padx=5)

            # Dépenses
            day_exp = pd.DataFrame()
            if not expenses_df.empty:
                day_exp = expenses_df[expenses_df['DateObj'].dt.day == day]
            
            if not day_exp.empty:
                count = len(day_exp)
                total = day_exp['Montant'].sum()
                ctk.CTkLabel(day_frame, text=f"• {count} Frais ({total:.0f}€)", font=("Montserrat", 10), text_color="#e67e22").pack(anchor="w", padx=5)

            # Notes / RDV
            day_notes = [n for n in notes_list if n['date'] == current_date.strftime("%d/%m/%Y")]
            if day_notes:
                count = len(day_notes)
                ctk.CTkLabel(day_frame, text=f"• {count} Note(s)", font=("Montserrat", 10), text_color="#8e44ad").pack(anchor="w", padx=5)

            # Interaction
            day_frame.bind("<Button-1>", lambda e, d=current_date: _on_day_click(app, d))
            for child in day_frame.winfo_children():
                child.bind("<Button-1>", lambda e, d=current_date: _on_day_click(app, d))

def _on_day_click(app, date):
    app.cal_selected_date = date
    _refresh_calendar_view(app) # Pour mettre à jour la bordure de sélection
    _update_details_sidebar(app, date)

def _update_details_sidebar(app, date):
    """Affiche les détails pour la date sélectionnée."""
    app.cal_selected_date_label.configure(text=date.strftime("%d %B %Y"))
    
    for widget in app.cal_details_scroll.winfo_children():
        widget.destroy()

    year = date.year
    date_str = date.strftime("%d/%m/%Y")
    
    # Chargement des données
    invoices_df = app._load_data_with_cache(year=year)
    expenses_df = load_expenses(year)
    notes_list = load_agenda_notes(year)
    working_hours = settings_manager.get_working_hours()
    
    # --- Filtrage ---
    invoices_df, expenses_df, notes_list = _filter_data(app, invoices_df, expenses_df, notes_list)

    # --- Factures ---
    day_inv = pd.DataFrame()
    if not invoices_df.empty:
        day_inv = invoices_df[invoices_df['Date'] == date_str]

    if not day_inv.empty:
        ctk.CTkLabel(app.cal_details_scroll, text="RECETTES", font=("Montserrat", 12, "bold"), text_color="#2ecc71").pack(anchor="w", pady=(10, 5))
        for _, row in day_inv.iterrows():
            f = ctk.CTkFrame(app.cal_details_scroll, fg_color=("white", "gray25"), cursor="hand2")
            f.pack(fill="x", pady=2)
            
            name = f"{row.get('Prenom', '')} {row.get('Nom', '')}"
            status = row.get('Methode_Paiement', '')
            color = "#e74c3c" if status == "Impayé" else "gray"
            
            ctk.CTkLabel(f, text=name, font=("Montserrat", 12, "bold")).pack(anchor="w", padx=5, pady=(5, 0))
            ctk.CTkLabel(f, text=f"{row['Prestation']} - {row['Montant']}€", font=("Montserrat", 11)).pack(anchor="w", padx=5)
            ctk.CTkLabel(f, text=status, font=("Montserrat", 10), text_color=color).pack(anchor="w", padx=5, pady=(0, 5))

            # Rendre cliquable pour ouvrir le PDF
            f.bind("<Button-1>", lambda e, d=row.to_dict(): app.invoice_actions.view_invoice_pdf(d))
            for child in f.winfo_children():
                child.bind("<Button-1>", lambda e, d=row.to_dict(): app.invoice_actions.view_invoice_pdf(d))

    # --- Dépenses ---
    day_exp = pd.DataFrame()
    if not expenses_df.empty:
        day_exp = expenses_df[expenses_df['Date'] == date_str]

    if not day_exp.empty:
        ctk.CTkLabel(app.cal_details_scroll, text="DÉPENSES", font=("Montserrat", 12, "bold"), text_color="#e67e22").pack(anchor="w", pady=(15, 5))
        for _, row in day_exp.iterrows():
            f = ctk.CTkFrame(app.cal_details_scroll, fg_color=("white", "gray25"))
            f.pack(fill="x", pady=2)
            
            ctk.CTkLabel(f, text=row['Categorie'], font=("Montserrat", 12, "bold")).pack(anchor="w", padx=5, pady=(5, 0))
            ctk.CTkLabel(f, text=f"{row['Description']}", font=("Montserrat", 11)).pack(anchor="w", padx=5)
            ctk.CTkLabel(f, text=f"-{row['Montant']}€", font=("Montserrat", 11, "bold"), text_color="#e67e22").pack(anchor="w", padx=5, pady=(0, 5))

    # --- Planning Journalier (Timeline) ---
    ctk.CTkLabel(app.cal_details_scroll, text="PLANNING", font=("Montserrat", 12, "bold"), text_color="#3498db").pack(anchor="w", pady=(15, 5))
    
    # Récupération des horaires du jour
    day_idx = str(date.weekday())
    hours_str = working_hours.get(day_idx, "")
    
    work_start, work_end = 0, 0
    if hours_str and "-" in hours_str:
        try:
            s, e = hours_str.split("-")
            work_start = int(s.split(":")[0])
            work_end = int(e.split(":")[0])
        except: pass

    day_notes = [n for n in notes_list if n['date'] == date_str]
    
    # Affichage des créneaux de 8h à 20h
    for hour in range(8, 21):
        # Détermine si l'heure est travaillée
        is_working_hour = False
        if work_start > 0: # Si jour travaillé
            if work_start <= hour < work_end:
                is_working_hour = True
        
        # Couleur de fond : gris foncé si non travaillé, blanc/gris clair si travaillé
        bg_color = ("white", "gray25") if is_working_hour else ("gray90", "gray14")
        
        slot_frame = ctk.CTkFrame(app.cal_details_scroll, fg_color=bg_color, corner_radius=0, border_width=0)
        slot_frame.pack(fill="x", pady=1)
        
        # Label Heure
        time_label = ctk.CTkLabel(slot_frame, text=f"{hour:02d}:00", font=("Montserrat", 10), width=40, text_color="gray")
        time_label.pack(side="left", padx=(5, 0), anchor="n", pady=5)
        
        # Contenu du créneau
        content_frame = ctk.CTkFrame(slot_frame, fg_color="transparent")
        content_frame.pack(side="left", fill="both", expand=True)
        
        # Recherche des notes pour cette heure
        notes_in_slot = []
        for note in day_notes:
            note_time = note.get('time', '')
            if note_time and note_time.startswith(f"{hour:02d}"):
                notes_in_slot.append(note)
        
        if notes_in_slot:
            for note in notes_in_slot:
                note_bg = ("#E3F2FD", "#2c3e50") # Bleu très clair / Bleu foncé
                nf = ctk.CTkFrame(content_frame, fg_color=note_bg, corner_radius=6)
                nf.pack(fill="x", pady=2, padx=5)
                
                # Drag Handle
                handle = ctk.CTkLabel(nf, text="::", font=("Arial", 12), text_color="gray", cursor="fleur")
                handle.pack(side="left", padx=5)
                handle.bind("<Button-1>", lambda e, n=note: _start_drag(e, app, n))
                handle.bind("<B1-Motion>", lambda e: _on_drag(e, app))
                handle.bind("<ButtonRelease-1>", lambda e: _end_drag(e, app))

                ctk.CTkLabel(nf, text=f"{note.get('time')} {note.get('title')}", font=("Montserrat", 11, "bold")).pack(side="left", padx=5)
                ctk.CTkButton(nf, text="✕", width=20, height=20, fg_color="transparent", text_color="red", 
                              command=lambda nid=note['id'], y=year: _delete_note(app, nid, y)).pack(side="right", padx=5)
        else:
            # Espace vide pour maintenir la hauteur du créneau
            ctk.CTkFrame(content_frame, height=25, fg_color="transparent").pack()

def _open_add_note_dialog(app):
    """Ouvre une fenêtre pour ajouter une note."""
    dialog = ctk.CTkToplevel(app)
    dialog.title("Ajouter Note / RDV")
    dialog.geometry("400x350")
    dialog.transient(app)
    dialog.grab_set()
    
    ctk.CTkLabel(dialog, text=f"Ajouter pour le {app.cal_selected_date.strftime('%d/%m/%Y')}", font=app.font_bold).pack(pady=10)
    
    ctk.CTkLabel(dialog, text="Titre / Objet :").pack(anchor="w", padx=20)
    title_entry = ctk.CTkEntry(dialog)
    title_entry.pack(fill="x", padx=20, pady=(0, 10))
    
    ctk.CTkLabel(dialog, text="Heure (optionnel) :").pack(anchor="w", padx=20)
    time_entry = ctk.CTkEntry(dialog, placeholder_text="HH:MM")
    time_entry.pack(fill="x", padx=20, pady=(0, 10))
    
    ctk.CTkLabel(dialog, text="Description :").pack(anchor="w", padx=20)
    desc_entry = ctk.CTkTextbox(dialog, height=80)
    desc_entry.pack(fill="x", padx=20, pady=(0, 20))
    
    def save():
        if not title_entry.get(): return
        data = {
            "date": app.cal_selected_date.strftime("%d/%m/%Y"),
            "title": title_entry.get(),
            "time": time_entry.get(),
            "description": desc_entry.get("1.0", "end-1c")
        }
        save_agenda_note(data)
        dialog.destroy()
        _refresh_calendar_view(app)
        _update_details_sidebar(app, app.cal_selected_date)
        
    ctk.CTkButton(dialog, text="Enregistrer", command=save).pack(pady=10)

def _delete_note(app, note_id, year):
    if delete_agenda_note(note_id, year):
        _refresh_calendar_view(app)
        _update_details_sidebar(app, app.cal_selected_date)

# --- Fonctions Drag & Drop ---
def _start_drag(event, app, note_data):
    """Commence le glisser-déposer."""
    app.drag_item = note_data
    # Création d'une fenêtre fantôme qui suit la souris
    app.drag_window = ctk.CTkToplevel(app)
    app.drag_window.overrideredirect(True)
    app.drag_window.attributes('-alpha', 0.7)
    app.drag_window.attributes('-topmost', True)
    
    l = ctk.CTkLabel(app.drag_window, text=note_data.get('title', 'Note'), fg_color="#3498db", text_color="white", corner_radius=5, padx=10, pady=5)
    l.pack()
    
    app.drag_window.geometry(f"+{event.x_root + 15}+{event.y_root + 15}")

def _on_drag(event, app):
    """Met à jour la position de la fenêtre fantôme."""
    if hasattr(app, 'drag_window') and app.drag_window:
        app.drag_window.geometry(f"+{event.x_root + 15}+{event.y_root + 15}")

def _end_drag(event, app):
    """Termine le glisser-déposer et déplace la note si lâchée sur un jour."""
    if hasattr(app, 'drag_window') and app.drag_window:
        app.drag_window.destroy()
        app.drag_window = None
    
    if not hasattr(app, 'drag_item') or not app.drag_item: return

    # Trouve le widget sous la souris
    x, y = event.x_root, event.y_root
    target_widget = app.winfo_containing(x, y)
    
    # Remonte la hiérarchie pour trouver si on est sur un jour du calendrier
    current_w = target_widget
    target_date = None
    
    while current_w:
        # Vérifie si le widget actuel (ou son canvas interne pour CTkFrame) est une clé de notre map
        for day_frame, date in app.cal_day_map.items():
            if current_w == day_frame or (hasattr(day_frame, '_canvas') and current_w == day_frame._canvas):
                target_date = date
                break
        if target_date: break
        if hasattr(current_w, 'master'): current_w = current_w.master
        else: break
            
    if target_date:
        new_date_str = target_date.strftime("%d/%m/%Y")
        if new_date_str != app.drag_item['date']:
            app.drag_item['date'] = new_date_str
            save_agenda_note(app.drag_item)
            _refresh_calendar_view(app)
            # Rafraîchit la sidebar (la note va disparaître de la vue actuelle si changée de jour)
            _update_details_sidebar(app, app.cal_selected_date)
            
    app.drag_item = None

def _refresh_all(app):
    _refresh_calendar_view(app)
    _update_details_sidebar(app, app.cal_selected_date)

def _filter_data(app, invoices_df, expenses_df, notes_list):
    if not hasattr(app, 'cal_search_var') or not hasattr(app, 'cal_type_var'):
        return invoices_df, expenses_df, notes_list
        
    search_text = app.cal_search_var.get().lower().strip()
    filter_type = app.cal_type_var.get()

    # Filter by Type
    if filter_type == "Notes":
        invoices_df = pd.DataFrame()
        expenses_df = pd.DataFrame()
    elif filter_type == "Factures":
        expenses_df = pd.DataFrame()
        notes_list = []
    elif filter_type == "Frais":
        invoices_df = pd.DataFrame()
        notes_list = []

    # Filter by Text
    if search_text:
        if not invoices_df.empty:
            mask = invoices_df.apply(lambda row: search_text in str(row.get('Nom', '')).lower() or 
                                                 search_text in str(row.get('Prenom', '')).lower() or 
                                                 search_text in str(row.get('Prestation', '')).lower(), axis=1)
            invoices_df = invoices_df[mask]
        
        if not expenses_df.empty:
            mask = expenses_df.apply(lambda row: search_text in str(row.get('Categorie', '')).lower() or 
                                                 search_text in str(row.get('Description', '')).lower(), axis=1)
            expenses_df = expenses_df[mask]
            
        if notes_list:
            notes_list = [n for n in notes_list if search_text in str(n.get('title', '')).lower() or 
                                                   search_text in str(n.get('description', '')).lower()]

    return invoices_df, expenses_df, notes_list