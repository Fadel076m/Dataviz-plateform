
import dash_bootstrap_components as dbc
from dash import html

def create_kpi_card(title, value, suffix="", color="primary", subtext=None):
    """Crée une carte KPI avec le nouveau style Premium"""
    card_body = [
        html.Div(title, className="badge-gold mb-3 d-inline-block"),
        html.H2(f"{value:,.0f} {suffix}".replace(",", " "), className="kpi-value mb-1"),
    ]
    if subtext:
        card_body.append(html.P(subtext, className="text-muted small mb-0", style={'opacity': '0.7'}))
        
    return dbc.Card(
        dbc.CardBody(card_body),
        className="shadow-sm h-100 fadeIn"
    )

def create_ratio_card(title, value, detail, color="info"):
    """Crée une carte pour un Ratio (%)"""
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.H6(title, className="text-muted mb-0"),
                html.H3(f"{value:.1f}%", className=f"text-{color}")
            ], className="d-flex justify-content-between align_items_center"),
            dbc.Progress(value=min(value, 100), color=color, className="mt-2", style={'height': '5px'}),
            html.Small(detail, className="text-muted mt-1 d-block")
        ]),
        className="shadow-sm mb-3 border-0"
    )
