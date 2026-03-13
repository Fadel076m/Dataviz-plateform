import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from utils.data_loader import DataProcessor
from components.charts import (
    create_severity_frequency_chart,
    create_risk_segmentation_chart,
    create_profitability_map,
    create_bonus_malus_impact
)
from components.analysis import generate_strategic_insights, render_sidebar_insights, render_global_analysis
from components.simulation import render_simulation_controls, render_simulation_results
import os

# ── Data ──────────────────────────────────────────────────
data_path = os.path.join(os.path.dirname(__file__), 'data', 'assurance_data_1000.csv')
processor = DataProcessor(data_path)
df = processor.load_data()

# ── App Init ──────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css"
    ],
    suppress_callback_exceptions=True
)
app.title = "AssurData Pro — Strategic Analytics"

# ── KPI Card Factory ──────────────────────────────────────
def make_kpi(title, value, icon, trend=None, variant="primary"):
    return html.Div([
        html.Div(html.I(className=f"{icon}"), className=f"kpi-icon-wrap kpi-icon-{variant}"),
        html.Div(title, className="kpi-label"),
        html.Div(value, className="kpi-value"),
        html.Div([
            html.I(className="bi bi-arrow-up-right me-1"),
            html.Span(trend)
        ], className="kpi-trend") if trend else None
    ], className="kpi-card h-100")

# ── Chart Card Factory ────────────────────────────────────
def make_chart_card(graph_id, title, chip, description, conclusion, width=12):
    return dbc.Col([
        html.Div([
            html.Div([
                html.H6(title, className="chart-title"),
                html.Span(chip, className="chart-chip")
            ], className="chart-header"),
            html.P(description, className="chart-description"),
            dcc.Graph(id=graph_id, config={'displayModeBar': False}),
            html.Div(conclusion, className="chart-conclusion")
        ], className="chart-card")
    ], width=width, className="mb-0")

# ── Sidebar ───────────────────────────────────────────────
sidebar = html.Div([

    # Logo
    html.Div([
        html.Div(html.I(className="bi bi-shield-lock-fill"), className="logo-icon"),
        html.H2("AssurData")
    ], className="sidebar-logo"),
    html.P("Decision Support System", className="sidebar-subtitle"),

    html.Div(className="sidebar-divider"),

    # Filters
    html.P("Filtres Analytiques", className="sidebar-section-label"),

    html.Div([
        html.Div([
            html.Span([
                html.I(className="bi bi-geo-alt me-1"),
                "Région"
            ], className="filter-label"),
            dcc.Dropdown(
                id='region-filter',
                options=[{'label': r, 'value': r} for r in sorted(df['region'].unique())],
                placeholder="Toutes les régions",
                className="custom-dropdown",
                style={"marginBottom": "14px"}
            )
        ], className="filter-block"),

        html.Div([
            html.Span([
                html.I(className="bi bi-tag me-1"),
                "Type d'Assurance"
            ], className="filter-label"),
            dcc.Dropdown(
                id='type-filter',
                options=[{'label': t, 'value': t} for t in sorted(df['type_assurance'].unique())],
                placeholder="Tous les types",
                className="custom-dropdown"
            )
        ], className="filter-block"),
    ]),

    html.Div(className="sidebar-divider"),

    # Dynamic Insights
    html.Div(id='strategic-insights-container'),

    # Footer
    html.Div([
        html.P("Conçu par Expert Data Analytics"),
        html.P("© 2026 Projet Assurance — M2"),
    ], className="sidebar-footer")

], className="sidebar", style={"position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": "260px"})

# ── Main Content ──────────────────────────────────────────
content = html.Div([

    # Page Header
    html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.I(className="bi bi-bar-chart-line me-2"),
                    "Analytique • Portefeuille Assurance"
                ], className="header-badge"),
                html.H1("Performance & Risk Portfolio", className="page-title"),
                html.P(
                    "Analyse multidimensionnelle pour pilotage stratégique du portefeuille client",
                    className="page-subtitle"
                )
            ], width=12)
        ])
    ], className="page-header"),

    # ── KPI Row ───────────────────────────────────────────
    dbc.Row([
        dbc.Col(html.Div(id='kpi-total-primes',  className="h-100"), width=4),
        dbc.Col(html.Div(id='kpi-total-sinistres', className="h-100"), width=4),
        dbc.Col(html.Div(id='kpi-loss-ratio',     className="h-100"), width=4),
    ], className="g-4 mb-4 row-gap"),

    # ── Charts Row 1 ──────────────────────────────────────
    dbc.Row([
        make_chart_card(
            graph_id='chart-severity-freq',
            title="Fréquence vs Sévérité",
            chip="Scatter Analysis",
            description="Corrélation entre le nombre moyen de sinistres et leur coût moyen, par type de contrat.",
            conclusion="Les contrats Santé affichent une fréquence élevée mais une sévérité maîtrisée.",
            width=7
        ),
        make_chart_card(
            graph_id='chart-risk-segment',
            title="Segmentation du Risque",
            chip="Risk Profiling",
            description="Score de risque moyen calculé sur la sinistralité historique et le profil assuré, par tranche d'âge.",
            conclusion="Les 18–25 ans présentent un score de risque 20% supérieur à la moyenne.",
            width=5
        ),
    ], className="g-4 mb-4 row-gap"),

    # ── Charts Row 2 ──────────────────────────────────────
    dbc.Row([
        make_chart_card(
            graph_id='chart-profit-region',
            title="Performance Géographique",
            chip="Regional KPIs",
            description="Équilibre financier (Primes encaissées – Sinistres versés) ventilé par zone administrative.",
            conclusion="Dakar génère 60% de la rentabilité brute, compensant les zones à sinistralité atypique.",
            width=12
        ),
    ], className="g-4 mb-4 row-gap"),

    # ── Charts Row 3 ──────────────────────────────────────
    dbc.Row([
        make_chart_card(
            graph_id='chart-bonus-impact',
            title="Diagnostic Bonus / Malus",
            chip="Predictive Signal",
            description="Analyse de la pertinence du coefficient bonus-malus comme prédicteur de la sinistralité future.",
            conclusion="Corrélation > 0.7 : le malus isole correctement les profils à haute fréquence.",
            width=12
        ),
    ], className="g-4 mb-4 row-gap"),

    # ── Global Intelligent Analysis ────────────────────────
    html.Div(id='global-analysis-container'),

    # ── Simulation & What-if Analysis ─────────────────────
    html.Div([
        render_simulation_controls(),
        html.Div(id='simulation-results-container')
    ], id='simulation-section'),

], className="main-content")

app.layout = html.Div([sidebar, content])

# ── Callbacks ─────────────────────────────────────────────
@app.callback(
    [Output('kpi-total-primes', 'children'),
     Output('kpi-total-sinistres', 'children'),
     Output('kpi-loss-ratio', 'children'),
     Output('chart-severity-freq', 'figure'),
     Output('chart-risk-segment', 'figure'),
     Output('chart-profit-region', 'figure'),
     Output('chart-bonus-impact', 'figure'),
     Output('strategic-insights-container', 'children'),
     Output('global-analysis-container', 'children')],
    [Input('region-filter', 'value'),
     Input('type-filter', 'value')]
)
def update_dashboard(region, type_assur):
    dff = df.copy()
    if region:
        dff = dff[dff['region'] == region]
    if type_assur:
        dff = dff[dff['type_assurance'] == type_assur]

    prime_sum    = dff['montant_prime'].sum()
    sinistre_sum = dff['montant_sinistres'].sum()
    l_ratio      = (sinistre_sum / prime_sum * 100) if prime_sum > 0 else 0

    ratio_variant = "success" if l_ratio < 60 else ("warning" if l_ratio < 70 else "danger")

    kpi_p  = make_kpi("Primes Totales",    f"{prime_sum:,.0f} €",    "bi bi-cash-stack",         trend="+2.1%", variant="primary")
    kpi_s  = make_kpi("Charge Sinistres",  f"{sinistre_sum:,.0f} €", "bi bi-lightning-charge",   trend="Stable", variant="danger")
    kpi_lr = make_kpi("Loss Ratio (S/P)",  f"{l_ratio:.1f}%",        "bi bi-activity",            trend=f"Cible: 70%", variant=ratio_variant)

    fig1 = create_severity_frequency_chart(dff)
    fig2 = create_risk_segmentation_chart(dff)
    fig3 = create_profitability_map(dff)
    fig4 = create_bonus_malus_impact(dff)

    insights_data    = generate_strategic_insights(dff)
    insights_sidebar = render_sidebar_insights(insights_data)
    global_analysis  = render_global_analysis(dff)

    return kpi_p, kpi_s, kpi_lr, fig1, fig2, fig3, fig4, insights_sidebar, global_analysis

# ── Simulation Callback ───────────────────────────────────
@app.callback(
    Output('simulation-results-container', 'children'),
    [Input('region-filter', 'value'),
     Input('type-filter', 'value'),
     Input('sim-premium-mod', 'value'),
     Input('sim-claim-mod', 'value')]
)
def update_simulation(region, type_assur, premium_mod, claim_mod):
    dff = df.copy()
    if region:
        dff = dff[dff['region'] == region]
    if type_assur:
        dff = dff[dff['type_assurance'] == type_assur]
    
    return render_simulation_results(dff, premium_mod, claim_mod)

if __name__ == '__main__':
    app.run(debug=False, port=8050)
