import customtkinter as ctk
from datetime import datetime
import pandas as pd
from .data_manager import load_expenses, MONTHS_FR

def update_dashboard_kpis(app):
    """Calcule et met à jour les indicateurs clés et le graphique du tableau de bord."""
    try:
        now = datetime.now()
        app._invalidate_data_cache()
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

        # Update KPI Labels
        app.kpi_revenue_label.configure(text=f"{revenue_month:,.2f} €".replace(",", " "))
        app.kpi_sessions_label.configure(text=f"{sessions_month}")
        app.kpi_unpaid_label.configure(text=f"{unpaid_total:,.2f} €".replace(",", " "))
        app.kpi_expenses_label.configure(text=f"{expenses_month:,.2f} €".replace(",", " "))
        app.kpi_unpaid_label.configure(text_color="#e74c3c" if unpaid_total > 0 else ("#1E1E1E", "#E0E0E0"))
    except Exception as e:
        print(f"Erreur lors de la mise à jour du tableau de bord : {e}")

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
