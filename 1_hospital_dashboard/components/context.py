# context.py
from dash import html
import dash_bootstrap_components as dbc

def context_section():
    return dbc.Card(
        className="dashboard-header",
        children=[
            dbc.CardBody([
                html.H1("🏥 Dashboard de Performance Hospitalière", 
                       className="text-white mb-3"),
                html.P(
                    "Outil d'analyse stratégique pour optimiser la prise en charge "
                    "des patients tout en maîtrisant les coûts et la qualité des soins.",
                    className="lead text-light mb-4"
                ),
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Span("🎯", className="fs-4 me-2"),
                            html.Span("Objectif :", className="fw-bold me-2"),
                            html.Span("Amélioration continue des parcours de soins", 
                                     className="text-light")
                        ], className="d-flex align-items-center mb-2")
                    ], md=4),
                    dbc.Col([
                        html.Div([
                            html.Span("📊", className="fs-4 me-2"),
                            html.Span("Indicateurs :", className="fw-bold me-2"),
                            html.Span("Durée, coût, qualité, efficience", 
                                     className="text-light")
                        ], className="d-flex align-items-center mb-2")
                    ], md=4),
                    dbc.Col([
                        html.Div([
                            html.Span("👨‍⚕️", className="fs-4 me-2"),
                            html.Span("Auteur :", className="fw-bold me-2"),
                            html.Span("Fadel ADAM", className="badge-medical")
                        ], className="d-flex align-items-center")
                    ], md=4),
                ])
            ])
        ]
    )