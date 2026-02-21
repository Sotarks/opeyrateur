import customtkinter as ctk
from datetime import datetime
from .data_manager import load_expenses, MONTHS_FR

def update_dashboard_kpis(app):
    """Calcule et met à jour les indicateurs clés et le graphique du tableau de bord."""
    data = load_dashboard_data(app)
    update_dashboard_views(app, data)

def load_dashboard_data(app):
    """Charge les données nécessaires pour le tableau de bord (exécutable dans un thread)."""
    import pandas as pd
    try:
        now = datetime.now()
        # Optimisation : On ne vide plus le cache ici systématiquement.
        invoices_df = app._load_data_with_cache()
        expenses_df = load_expenses(now.year)

        revenue_month, sessions_month, unpaid_total, expenses_month = 0.0, 0, 0.0, 0.0
        
        # --- Chart Data ---
        chart_labels = []
        chart_values = []

        if not invoices_df.empty:
            invoices_df['Date'] = pd.to_datetime(invoices_df['Date'], format='%d/%m/%Y', errors='coerce')
            paid_invoices_df = invoices_df[invoices_df['Methode_Paiement'] != 'Impayé'].copy()
            
            unpaid_df = invoices_df[invoices_df['Methode_Paiement'] == 'Impayé']
            unpaid_total = unpaid_df['Montant'].sum()

            monthly_invoices = invoices_df[(invoices_df['Date'].dt.year == now.year) & (invoices_df['Date'].dt.month == now.month)]
            sessions_month = len(monthly_invoices)
            
            paid_monthly_invoices = paid_invoices_df[(paid_invoices_df['Date'].dt.year == now.year) & (paid_invoices_df['Date'].dt.month == now.month)]
            revenue_month = paid_monthly_invoices['Montant'].sum()

            # Calculate last 6 months revenue for chart
            for i in range(5, -1, -1):
                target_date = now - pd.DateOffset(months=i)
                month_name = MONTHS_FR[target_date.month - 1][:3]
                chart_labels.append(month_name)
                
                monthly_revenue = paid_invoices_df[
                    (paid_invoices_df['Date'].dt.year == target_date.year) &
                    (paid_invoices_df['Date'].dt.month == target_date.month)
                ]['Montant'].sum()
                chart_values.append(monthly_revenue)

        if not expenses_df.empty:
            expenses_df['Date'] = pd.to_datetime(expenses_df['Date'], format='%d/%m/%Y', errors='coerce')
            monthly_expenses = expenses_df[(expenses_df['Date'].dt.year == now.year) & (expenses_df['Date'].dt.month == now.month)]
            expenses_month = monthly_expenses['Montant'].sum()

        # --- Calcul Salaire "Vrai" (Mensuel) ---
        # Règle : 1/3 Charges, 1/3 Frais, 1/3 Salaire sur le mois en cours
        taxes_paid_month = 0.0
        if not expenses_df.empty:
             taxes_paid_month = monthly_expenses[monthly_expenses['Categorie'] == 'Cotisations']['Montant'].sum()
        
        ops_paid_month = expenses_month - taxes_paid_month

        one_third = revenue_month / 3.0
        prov_taxes = max(0.0, one_third - taxes_paid_month)
        prov_ops = max(0.0, one_third - ops_paid_month)
        cash_flow = revenue_month - expenses_month
        safe_salary = cash_flow - prov_taxes - prov_ops

        # Calcul progression vers objectif (2000€)
        salary_goal = 2000.0
        progress = 0.0
        if salary_goal > 0:
            progress = max(0.0, min(1.0, safe_salary / salary_goal))

        return {
            "revenue_month": revenue_month,
            "sessions_month": sessions_month,
            "unpaid_total": unpaid_total,
            "expenses_month": expenses_month,
            "salary_metrics": {
                "safe_salary": safe_salary,
                "prov_taxes": prov_taxes,
                "prov_ops": prov_ops,
                "progress": progress
            },
            "success": True
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_dashboard_views(app, data):
    """Met à jour les widgets du tableau de bord avec les données calculées."""
    if not data.get("success", False):
        print(f"Erreur dashboard: {data.get('error')}")
        return

    app.kpi_revenue_label.configure(text=f"{data['revenue_month']:,.2f} €".replace(",", " "))
    app.kpi_sessions_label.configure(text=f"{data['sessions_month']}")
    app.kpi_unpaid_label.configure(text=f"{data['unpaid_total']:,.2f} €".replace(",", " "))
    app.kpi_expenses_label.configure(text=f"{data['expenses_month']:,.2f} €".replace(",", " "))
    
    # Gestion de la couleur pour les impayés
    unpaid_val = data['unpaid_total']
    app.kpi_unpaid_label.configure(text_color="#e74c3c" if unpaid_val > 0 else ("#1E1E1E", "#E0E0E0"))

    # Mise à jour du Salaire Estimé
    if hasattr(app, 'kpi_salary_label'):
        salary_data = data.get("salary_metrics", {})
        safe_salary = salary_data.get("safe_salary", 0.0)
        prov_taxes = salary_data.get("prov_taxes", 0.0)
        prov_ops = salary_data.get("prov_ops", 0.0)
        progress = salary_data.get("progress", 0.0)
        
        app.kpi_salary_label.configure(text=f"{safe_salary:,.2f} €".replace(",", " "), text_color="#2ecc71" if safe_salary >= 0 else "#e74c3c")
        app.kpi_salary_details.configure(text=f"À provisionner : Charges {prov_taxes:,.0f}€ | Frais {prov_ops:,.0f}€")

        if hasattr(app, 'salary_progress_bar'):
            app.salary_progress_bar.set(progress)
            # La barre devient verte si l'objectif est atteint, sinon elle reste bleue
            bar_color = "#2ecc71" if progress >= 1.0 else "#3498db"
            app.salary_progress_bar.configure(progress_color=bar_color)

def on_kpi_click(app, kpi_name):
    """Gère le clic sur un indicateur du tableau de bord."""
    now = datetime.now()
    current_year = str(now.year)
    current_month = MONTHS_FR[now.month - 1]

    if kpi_name in ["revenue_month", "sessions_month"]:
        app._show_tool(app.search_wrapper)
        app.search_year_var.set(current_year)
        app._on_search_year_change(current_year) # Enable month menu
        app.search_month_var.set(current_month)
        app.search_status_var.set("Payées" if kpi_name == "revenue_month" else "Tous")
        app._apply_filters_and_search()
    
    elif kpi_name == "unpaid":
        app._show_tool(app.search_wrapper)
        app.search_year_var.set("Toutes")
        app._on_search_year_change("Toutes") # Disable month menu
        app.search_status_var.set("Impayées")
        app._apply_filters_and_search()

    elif kpi_name == "expenses_month":
        app._show_tool(app.expenses_wrapper)
