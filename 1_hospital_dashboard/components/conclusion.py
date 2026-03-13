# conclusion.py
from dash import html
import dash_bootstrap_components as dbc

def conclusion_section():
    return dbc.Card(
        className="conclusion-card shadow-sm",
        children=[
            dbc.CardBody([
                html.Div([
                    html.Span("🧠", className="fs-2 me-3"),
                    html.Div([
                        html.H4("Recommandations stratégiques", className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.H6("🎯 Optimisation des coûts", className="text-primary"),
                                    html.P("Les pathologies 'Cancer' et 'Fracture' représentent "
                                          "45% du budget total. Recommandation : analyse détaillée "
                                          "des traitements pour ces pathologies.",
                                          className="text-muted small")
                                ], className="p-3 bg-white rounded mb-3")
                            ], md=4),
                            dbc.Col([
                                html.Div([
                                    html.H6("⏱️ Réduction des durées", className="text-success"),
                                    html.P("Le département 'Cardiologie' présente une durée moyenne "
                                          "élevée. Mise en place d'un parcours optimisé recommandée.",
                                          className="text-muted small")
                                ], className="p-3 bg-white rounded mb-3")
                            ], md=4),
                            dbc.Col([
                                html.Div([
                                    html.H6("📊 Surveillance continue", className="text-info"),
                                    html.P("Mettre en place un tableau de bord opérationnel pour "
                                          "suivre en temps réel les indicateurs clés.",
                                          className="text-muted small")
                                ], className="p-3 bg-white rounded mb-3")
                            ], md=4),
                        ]),
                        html.Hr(),
                        html.Small([
                            "Analyse réalisée par ",
                            html.Strong("Fadel ADAM", className="text-primary"),
                            " | Direction de la Performance Hospitalière"
                        ], className="text-muted")
                    ])
                ], className="d-flex")
            ])
        ]
    )