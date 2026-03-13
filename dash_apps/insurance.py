"""
dash_apps/insurance.py
Wrapper : Dashboard Assurance — url_base_pathname='/insurance/'

Import via importlib.util pour éviter les conflits de noms avec hospital
(tous les deux ont des dossiers utils/ et components/).
"""

import sys
import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_INSURANCE_DIR = _ROOT / "2_assurance_dashboard"


def _load(alias: str, rel_path: str):
    """Import d'un module par chemin absolu avec un alias unique dans sys.modules."""
    if alias in sys.modules:
        return sys.modules[alias]
    full_path = _INSURANCE_DIR / rel_path
    spec = importlib.util.spec_from_file_location(alias, str(full_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Impossible de charger le module {alias} depuis {full_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)
    return mod


def create_insurance_app():
    """
    Instancie le dashboard assurance Dash avec url_base_pathname='/insurance/'.
    Utilise importlib.util pour charger chaque module par chemin absolu.
    """
    import dash
    import dash_bootstrap_components as dbc
    from dash import dcc, html, Input, Output

    # ── Chargement des modules via chemin absolu ─────────────
    dl_mod    = _load("ins.utils.data_loader",       "utils/data_loader.py")
    charts_mod = _load("ins.components.charts",      "components/charts.py")
    analysis_mod = _load("ins.components.analysis",  "components/analysis.py")
    sim_mod   = _load("ins.components.simulation",   "components/simulation.py")

    DataProcessor               = dl_mod.DataProcessor
    create_severity_frequency_chart = charts_mod.create_severity_frequency_chart
    create_risk_segmentation_chart  = charts_mod.create_risk_segmentation_chart
    create_profitability_map        = charts_mod.create_profitability_map
    create_bonus_malus_impact       = charts_mod.create_bonus_malus_impact
    generate_strategic_insights = analysis_mod.generate_strategic_insights
    render_sidebar_insights     = analysis_mod.render_sidebar_insights
    render_global_analysis      = analysis_mod.render_global_analysis
    render_simulation_controls  = sim_mod.render_simulation_controls
    render_simulation_results   = sim_mod.render_simulation_results

    # ── Chargement des données ───────────────────────────────
    data_path = str(_INSURANCE_DIR / "data" / "assurance_data_1000.csv")
    processor = DataProcessor(data_path)
    df = processor.load_data()

    # ── Création de l'app Dash ───────────────────────────────
    app = dash.Dash(
        __name__,
        requests_pathname_prefix="/insurance/",
        routes_pathname_prefix="/",
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,
            "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css",
        ],
        suppress_callback_exceptions=True,
        assets_folder=str(_INSURANCE_DIR / "assets"),
        title="DataViz | Assurance",
        meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    )

    # ── KPI Card Factory ─────────────────────────────────────
    def make_kpi(title, value, icon, trend=None, variant="primary"):
        return html.Div(
            [
                html.Div(html.I(className=f"{icon}"), className=f"kpi-icon-wrap kpi-icon-{variant}"),
                html.Div(title, className="kpi-label"),
                html.Div(value, className="kpi-value"),
                html.Div(
                    [html.I(className="bi bi-arrow-up-right me-1"), html.Span(trend)],
                    className="kpi-trend",
                ) if trend else None,
            ],
            className="kpi-card h-100",
        )

    # ── Barre retour hub ─────────────────────────────────────
    back_bar = html.Div(
        style={
            "display": "flex", "alignItems": "center", "gap": "12px",
            "padding": "10px 20px",
            "background": "rgba(0,0,0,0.4)",
            "borderBottom": "1px solid rgba(108,99,255,0.2)",
            "position": "fixed", "top": "0", "left": "260px",
            "right": "0", "zIndex": "9999",
        },
        children=[
            html.A("← Hub Analytics", href="/",
                   style={"color": "#6C63FF", "fontWeight": "600", "fontSize": "0.88rem",
                          "textDecoration": "none", "fontFamily": "Inter, sans-serif"}),
            html.Span("›", style={"color": "rgba(255,255,255,0.3)", "fontSize": "1.1rem"}),
            html.Span("Assurance", style={"color": "rgba(255,255,255,0.7)",
                                          "fontSize": "0.88rem", "fontFamily": "Inter, sans-serif"}),
        ],
    )

    # ── Sidebar ──────────────────────────────────────────────
    sidebar = html.Div(
        [
            html.Div(
                [html.Div(html.I(className="bi bi-shield-lock-fill"), className="logo-icon"),
                 html.H2("AssurData")],
                className="sidebar-logo",
            ),
            html.P("Decision Support System", className="sidebar-subtitle"),
            html.Div(className="sidebar-divider"),
            html.P("Filtres Analytiques", className="sidebar-section-label"),
            html.Div([
                html.Div([
                    html.Span([html.I(className="bi bi-geo-alt me-1"), "Région"], className="filter-label"),
                    dcc.Dropdown(
                        id="ins-region-filter",
                        options=[{"label": r, "value": r} for r in sorted(df["region"].unique())],
                        placeholder="Toutes les régions",
                        className="custom-dropdown",
                        style={"marginBottom": "14px"},
                    ),
                ], className="filter-block"),
                html.Div([
                    html.Span([html.I(className="bi bi-tag me-1"), "Type d'Assurance"], className="filter-label"),
                    dcc.Dropdown(
                        id="ins-type-filter",
                        options=[{"label": t, "value": t} for t in sorted(df["type_assurance"].unique())],
                        placeholder="Tous les types",
                        className="custom-dropdown",
                    ),
                ], className="filter-block"),
            ]),
            html.Div(className="sidebar-divider"),
            html.Div(id="ins-strategic-insights-container"),
            html.Div([
                html.P("Conçu par Expert Data Analytics"),
                html.P("© 2026 Projet Assurance — M2"),
            ], className="sidebar-footer"),
        ],
        className="sidebar",
        style={"position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": "260px"},
    )

    # ── Chart Card Factory ────────────────────────────────────
    def make_chart_card(graph_id, title, chip, description, conclusion, width=12):
        return dbc.Col([
            html.Div([
                html.Div([html.H6(title, className="chart-title"), html.Span(chip, className="chart-chip")],
                         className="chart-header"),
                html.P(description, className="chart-description"),
                dcc.Graph(id=graph_id, config={"displayModeBar": False}),
                html.Div(conclusion, className="chart-conclusion"),
            ], className="chart-card")
        ], width=width, className="mb-0")

    # ── Main content ─────────────────────────────────────────
    content = html.Div([
        html.Div(style={"height": "50px"}),
        html.Div([
            dbc.Row([dbc.Col([
                html.Div([html.I(className="bi bi-bar-chart-line me-2"), "Analytique • Portefeuille Assurance"],
                         className="header-badge"),
                html.H1("Performance & Risk Portfolio", className="page-title"),
                html.P("Analyse multidimensionnelle pour pilotage stratégique du portefeuille client",
                       className="page-subtitle"),
            ], width=12)])
        ], className="page-header"),
        dbc.Row([
            dbc.Col(html.Div(id="ins-kpi-total-primes", className="h-100"), width=4),
            dbc.Col(html.Div(id="ins-kpi-total-sinistres", className="h-100"), width=4),
            dbc.Col(html.Div(id="ins-kpi-loss-ratio", className="h-100"), width=4),
        ], className="g-4 mb-4 row-gap"),
        dbc.Row([
            make_chart_card("ins-chart-severity-freq", "Fréquence vs Sévérité", "Scatter Analysis",
                            "Corrélation entre sinistres et coût moyen par type de contrat.",
                            "Contrats Santé : haute fréquence, sévérité maîtrisée.", 7),
            make_chart_card("ins-chart-risk-segment", "Segmentation du Risque", "Risk Profiling",
                            "Score de risque par tranche d'âge.",
                            "18–25 ans : score 20% supérieur à la moyenne.", 5),
        ], className="g-4 mb-4 row-gap"),
        dbc.Row([make_chart_card(
            "ins-chart-profit-region", "Performance Géographique", "Regional KPIs",
            "Primes encaissées – Sinistres versés par zone.", "Dakar génère 60% de la rentabilité.", 12,
        )], className="g-4 mb-4 row-gap"),
        dbc.Row([make_chart_card(
            "ins-chart-bonus-impact", "Diagnostic Bonus / Malus", "Predictive Signal",
            "Coefficient bonus-malus comme prédicteur de sinistralité.",
            "Corrélation > 0.7 : malus isole les profils à haute fréquence.", 12,
        )], className="g-4 mb-4 row-gap"),
        html.Div(id="ins-global-analysis-container"),
        html.Div([render_simulation_controls(), html.Div(id="ins-simulation-results-container")],
                 id="ins-simulation-section"),
    ], className="main-content")

    app.layout = html.Div([back_bar, sidebar, content])

    # ── Callbacks ────────────────────────────────────────────
    @app.callback(
        [Output("ins-kpi-total-primes", "children"),
         Output("ins-kpi-total-sinistres", "children"),
         Output("ins-kpi-loss-ratio", "children"),
         Output("ins-chart-severity-freq", "figure"),
         Output("ins-chart-risk-segment", "figure"),
         Output("ins-chart-profit-region", "figure"),
         Output("ins-chart-bonus-impact", "figure"),
         Output("ins-strategic-insights-container", "children"),
         Output("ins-global-analysis-container", "children")],
        [Input("ins-region-filter", "value"), Input("ins-type-filter", "value")],
    )
    def update_dashboard(region, type_assur):
        dff = df.copy()
        if region:
            dff = dff[dff["region"] == region]
        if type_assur:
            dff = dff[dff["type_assurance"] == type_assur]

        prime_sum    = dff["montant_prime"].sum()
        sinistre_sum = dff["montant_sinistres"].sum()
        l_ratio      = (sinistre_sum / prime_sum * 100) if prime_sum > 0 else 0
        ratio_variant = "success" if l_ratio < 60 else ("warning" if l_ratio < 70 else "danger")

        kpi_p  = make_kpi("Primes Totales",   f"{prime_sum:,.0f} €",    "bi bi-cash-stack",       "+2.1%",     "primary")
        kpi_s  = make_kpi("Charge Sinistres", f"{sinistre_sum:,.0f} €", "bi bi-lightning-charge", "Stable",    "danger")
        kpi_lr = make_kpi("Loss Ratio (S/P)", f"{l_ratio:.1f}%",        "bi bi-activity",         "Cible: 70%", ratio_variant)

        fig1 = create_severity_frequency_chart(dff)
        fig2 = create_risk_segmentation_chart(dff)
        fig3 = create_profitability_map(dff)
        fig4 = create_bonus_malus_impact(dff)

        insights_data    = generate_strategic_insights(dff)
        insights_sidebar = render_sidebar_insights(insights_data)
        global_analysis  = render_global_analysis(dff)

        return kpi_p, kpi_s, kpi_lr, fig1, fig2, fig3, fig4, insights_sidebar, global_analysis

    @app.callback(
        Output("ins-simulation-results-container", "children"),
        [Input("ins-region-filter", "value"),
         Input("ins-type-filter", "value"),
         Input("sim-premium-mod", "value"),
         Input("sim-claim-mod", "value")],
    )
    def update_simulation(region, type_assur, premium_mod, claim_mod):
        dff = df.copy()
        if region:
            dff = dff[dff["region"] == region]
        if type_assur:
            dff = dff[dff["type_assurance"] == type_assur]
        return render_simulation_results(dff, premium_mod, claim_mod)

    return app
