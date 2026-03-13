"""
layout.py — Mise en page du Dashboard Solaire
Header, filtres, KPI cards, sections graphiques, conclusions.
"""

from dash import html, dcc
from . import data_processing as dp

# Charger les données pour les options de filtres
df = dp.load_data()
COUNTRIES = sorted(df["Country"].unique())
MONTHS = [
    {"label": m, "value": i}
    for i, m in enumerate(
        ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
         "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"],
        start=1,
    )
]

# ──────────────────────────────────────────────
# COMPOSANTS RÉUTILISABLES
# ──────────────────────────────────────────────

def make_kpi_card(card_id, icon, title, subtitle=""):
    """Crée une carte KPI avec icône, valeur, et sous-titre."""
    return html.Div(
        className="kpi-card",
        children=[
            html.Div(icon, className="kpi-icon"),
            html.Div(
                className="kpi-content",
                children=[
                    html.P(title, className="kpi-title"),
                    html.H3(id=card_id, className="kpi-value", children="—"),
                    html.P(subtitle, className="kpi-subtitle"),
                ],
            ),
        ],
    )


def section_header(icon, title, subtitle=""):
    """En-tête de section avec icône."""
    return html.Div(
        className="section-header",
        children=[
            html.H2([html.Span(icon, className="section-icon"), f" {title}"]),
            html.P(subtitle, className="section-subtitle") if subtitle else None,
        ],
    )


# ──────────────────────────────────────────────
# LAYOUT PRINCIPAL
# ──────────────────────────────────────────────

def create_layout():
    return html.Div(
        className="dashboard-container",
        children=[
            # ────── HEADER ──────
            html.Header(
                className="dashboard-header",
                children=[
                    html.Div(
                        className="header-content",
                        children=[
                            html.Div(
                                className="header-title-group",
                                children=[
                                    html.H1([
                                        html.Span("☀️", className="header-emoji"),
                                        " Solar Park ",
                                        html.Span("Analytics", className="highlight"),
                                    ]),
                                    html.P(
                                        "Suivi et analyse de la production d'énergie solaire photovoltaïque",
                                        className="header-tagline",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="header-badge",
                                children=[
                                    html.Span("📡 LIVE", className="live-badge"),
                                    html.Span("2024", className="year-badge"),
                                ],
                            ),
                        ],
                    ),
                ],
            ),

            # ────── FILTRES ──────
            html.Div(
                className="filters-bar",
                children=[
                    html.Div(
                        className="filter-group",
                        children=[
                            html.Label("🌍 Pays", className="filter-label"),
                            dcc.Dropdown(
                                id="filter-country",
                                options=[{"label": c, "value": c} for c in COUNTRIES],
                                value=COUNTRIES,
                                multi=True,
                                placeholder="Sélectionner un pays...",
                                className="dropdown-dark",
                            ),
                        ],
                    ),
                    html.Div(
                        className="filter-group",
                        children=[
                            html.Label("📅 Mois", className="filter-label"),
                            dcc.Dropdown(
                                id="filter-month",
                                options=MONTHS,
                                value=[],
                                multi=True,
                                placeholder="Tous les mois",
                                className="dropdown-dark",
                            ),
                        ],
                    ),
                    html.Div(
                        className="filter-group",
                        children=[
                            html.Label("📆 Plage de dates", className="filter-label"),
                            dcc.DatePickerRange(
                                id="filter-daterange",
                                start_date=df["Date"].min(),
                                end_date=df["Date"].max(),
                                display_format="DD/MM/YYYY",
                                className="datepicker-dark",
                            ),
                        ],
                    ),
                ],
            ),

            # ────── KPI CARDS ──────
            html.Div(
                className="kpi-section",
                children=[
                    section_header("📊", "Indicateurs clés de performance",
                                   "Vue d'ensemble instantanée du parc solaire"),
                    html.Div(
                        className="kpi-grid",
                        children=[
                            make_kpi_card("kpi-total-prod", "⚡", "Production Totale", "kWh"),
                            make_kpi_card("kpi-avg-hourly", "📈", "Moy. Horaire", "kW"),
                            make_kpi_card("kpi-efficiency", "🔋", "Rendement AC/DC", "%"),
                            make_kpi_card("kpi-loss-rate", "📉", "Taux de Perte", "%"),
                            make_kpi_card("kpi-peak", "🏔️", "Pic Production", "kW"),
                            make_kpi_card("kpi-anomaly-rate", "⚠️", "Taux Anomalies", "%"),
                            make_kpi_card("kpi-capacity", "🎯", "Facteur Capacité", "%"),
                            make_kpi_card("kpi-irradiation", "☀️", "Irradiation Moy.", "kWh/m²"),
                        ],
                    ),
                ],
            ),

            # ────── SECTION PRODUCTION ──────
            html.Div(
                className="section",
                children=[
                    section_header("⚡", "Analyse de la Production",
                                   "Suivi temporel de la puissance DC et AC"),
                    html.Div(
                        className="charts-grid-2",
                        children=[
                            html.Div(className="chart-card", children=[
                                html.H4("Profil Horaire Moyen — DC vs AC", className="chart-title"),
                                dcc.Graph(id="chart-hourly-profile", config={"displayModeBar": False}),
                            ]),
                            html.Div(className="chart-card", children=[
                                html.H4("Répartition de la Production par Pays", className="chart-title"),
                                dcc.Graph(id="chart-country-pie", config={"displayModeBar": False}),
                            ]),
                        ],
                    ),
                    html.Div(
                        className="chart-card chart-full",
                        children=[
                            html.H4("Production Journalière Cumulée", className="chart-title"),
                            dcc.Graph(id="chart-daily-production", config={"displayModeBar": False}),
                        ],
                    ),
                ],
            ),

            # ────── SECTION ENVIRONNEMENT ──────
            html.Div(
                className="section",
                children=[
                    section_header("🌡️", "Analyse Environnementale",
                                   "Impact de l'irradiation et de la température sur la production"),
                    html.Div(
                        className="charts-grid-2",
                        children=[
                            html.Div(className="chart-card", children=[
                                html.H4("Irradiation vs Puissance DC", className="chart-title"),
                                dcc.Graph(id="chart-irr-vs-dc", config={"displayModeBar": False}),
                            ]),
                            html.Div(className="chart-card", children=[
                                html.H4("Température Module vs Production AC", className="chart-title"),
                                dcc.Graph(id="chart-temp-vs-ac", config={"displayModeBar": False}),
                            ]),
                        ],
                    ),
                    html.Div(
                        className="chart-card chart-full",
                        children=[
                            html.H4("Heatmap — Production Moyenne par Heure et Mois",
                                     className="chart-title"),
                            dcc.Graph(id="chart-heatmap", config={"displayModeBar": False}),
                        ],
                    ),
                ],
            ),

            # ────── SECTION EFFICACITÉ ──────
            html.Div(
                className="section",
                children=[
                    section_header("🔋", "Efficacité et Pertes",
                                   "Analyse du rendement de conversion et de la saisonnalité"),
                    html.Div(
                        className="charts-grid-2",
                        children=[
                            html.Div(className="chart-card", children=[
                                html.H4("Production Mensuelle par Pays", className="chart-title"),
                                dcc.Graph(id="chart-monthly-bar", config={"displayModeBar": False}),
                            ]),
                            html.Div(className="chart-card", children=[
                                html.H4("Distribution de la Puissance AC par Mois",
                                         className="chart-title"),
                                dcc.Graph(id="chart-monthly-box", config={"displayModeBar": False}),
                            ]),
                        ],
                    ),
                ],
            ),

            # ────── SECTION ANOMALIES ──────
            html.Div(
                className="section",
                children=[
                    section_header("⚠️", "Détection d'Anomalies",
                                   "Identification automatique des comportements anormaux"),
                    html.Div(
                        className="charts-grid-2",
                        children=[
                            html.Div(className="chart-card", children=[
                                html.H4("Répartition des Types d'Anomalies",
                                         className="chart-title"),
                                dcc.Graph(id="chart-anomaly-pie", config={"displayModeBar": False}),
                            ]),
                            html.Div(className="chart-card", children=[
                                html.H4("Production avec Anomalies Surlignées",
                                         className="chart-title"),
                                dcc.Graph(id="chart-anomaly-timeline", config={"displayModeBar": False}),
                            ]),
                        ],
                    ),
                    html.Div(
                        className="chart-card chart-full",
                        children=[
                            html.H4("📋 Détail des Anomalies Récentes", className="chart-title"),
                            html.Div(id="anomaly-table-container"),
                        ],
                    ),
                ],
            ),

            # ────── CONCLUSIONS ──────
            html.Div(
                className="section conclusions-section",
                children=[
                    section_header("📝", "Conclusions et Recommandations",
                                   "Analyse synthétique et axes d'optimisation"),
                    html.Div(
                        className="conclusions-grid",
                        children=[
                            html.Div(className="conclusion-card", children=[
                                html.H4("🔧 Conclusions Techniques"),
                                html.Ul([
                                    html.Li("Le rendement AC/DC global oscille autour de 90%, ce qui indique un fonctionnement normal des onduleurs avec des marges d'optimisation."),
                                    html.Li("Les pertes de conversion suivent un schéma prévisible corrélé à la charge — les pertes proportionnelles augmentent aux faibles charges."),
                                    html.Li("L'échauffement des modules (Temp_Delta) impacte directement le rendement, surtout au-delà de 25°C de delta."),
                                ]),
                            ]),
                            html.Div(className="conclusion-card", children=[
                                html.H4("⚡ Conclusions Énergétiques"),
                                html.Ul([
                                    html.Li("Les sites tropicaux (Inde, Brésil) présentent une production plus stable sur l'année grâce à une irradiation constante."),
                                    html.Li("La Norvège montre une forte saisonnalité avec un pic estival prononcé et une production quasi nulle en hiver."),
                                    html.Li("L'Australie bénéficie d'un excellent facteur de capacité grâce à un ensoleillement élevé et des températures modérées."),
                                ]),
                            ]),
                            html.Div(className="conclusion-card", children=[
                                html.H4("🛠️ Recommandations Maintenance"),
                                html.Ul([
                                    html.Li("Prioriser l'inspection des onduleurs sur les sites présentant un taux d'anomalies 'panne onduleur' supérieur à 2%."),
                                    html.Li("Mettre en place un nettoyage préventif des panneaux quand l'irradiation est élevée mais la production chute."),
                                    html.Li("Surveiller les modules présentant un delta de température > 20°C pour prévenir la dégradation prématurée."),
                                ]),
                            ]),
                            html.Div(className="conclusion-card", children=[
                                html.H4("🎯 Recommandations Stratégiques"),
                                html.Ul([
                                    html.Li("Investir dans des onduleurs haute efficacité pour réduire le taux de perte de conversion sous les 8%."),
                                    html.Li("Envisager le stockage d'énergie sur les sites à forte variabilité saisonnière (Norvège)."),
                                    html.Li("Développer la capacité installée sur les sites à fort facteur de capacité (Inde, Australie) pour maximiser le ROI."),
                                    html.Li("Implémenter un système de monitoring temps réel avec alertes automatiques sur les anomalies critiques."),
                                ]),
                            ]),
                        ],
                    ),
                ],
            ),

            # ────── FOOTER ──────
            html.Footer(
                className="dashboard-footer",
                children=[
                    html.P([
                        "Solar Park Analytics — Dashboard conçu par Fadel ADAM avec ",
                        html.Span("Dash", style={"fontWeight": "600"}),
                        " & ",
                        html.Span("Plotly", style={"fontWeight": "600"}),
                        " | Données 2024 | 4 pays | 35 136 observations",
                    ]),
                ],
            ),
        ],
    )
