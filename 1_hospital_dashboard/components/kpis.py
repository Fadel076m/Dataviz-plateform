# kpis.py
import dash_bootstrap_components as dbc
from dash import html
from utils.colors import MEDICAL_COLORS

def kpi_cards(kpis):
    return dbc.Row(
        className="mb-4",
        children=[
            # Patients
            dbc.Col(dbc.Card([
                html.H6("👥 Patients", className="text-white"),
                html.H3(f'{kpis["patients"]:,}', className="text-white"),
                html.Small(f'Total analysé', className="text-light")
            ], className="kpi-card kpi-patients"), md=2, sm=4, xs=6),
            
            # Durée moyenne
            dbc.Col(dbc.Card([
                html.H6("📅 Durée moyenne", className="text-white"),
                html.H3(f'{kpis["avg_stay"]} j', className="text-white"),
                html.Small(f'par patient', className="text-light")
            ], className="kpi-card kpi-duration"), md=2, sm=4, xs=6),
            
            # Durée médiane
            dbc.Col(dbc.Card([
                html.H6("📊 Durée médiane", className="text-white"),
                html.H3(f'{kpis["median_stay"]} j', className="text-white"),
                html.Small(f'valeur centrale', className="text-light")
            ], className="kpi-card kpi-median"), md=2, sm=4, xs=6),
            
            # Coût moyen
            dbc.Col(dbc.Card([
                html.H6("💰 Coût moyen", className="text-white"),
                html.H3(f'{kpis["avg_cost"]:,.0f} €', className="text-white"),
                html.Small(f'par séjour', className="text-light")
            ], className="kpi-card kpi-cost"), md=2, sm=4, xs=6),
            
            # Coût / jour
            dbc.Col(dbc.Card([
                html.H6("📈 Coût / jour", className="text-white"),
                html.H3(f'{kpis["avg_cost_day"]:,.0f} €', className="text-white"),
                html.Small(f'moyenne journalière', className="text-light")
            ], className="kpi-card kpi-cost-day"), md=2, sm=4, xs=6),
            
            # Coût total (nouveau KPI)
            dbc.Col(dbc.Card([
                html.H6("🏥 Coût total", className="text-white"),
                html.H3(f'{kpis["total_cost"]:,.0f} €', className="text-white"),
                html.Small(f'pour tous les patients', className="text-light")
            ], className="kpi-card kpi-total"), md=2, sm=4, xs=6),
        ]
    )