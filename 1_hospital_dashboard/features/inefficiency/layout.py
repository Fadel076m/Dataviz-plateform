import dash_bootstrap_components as dbc
from dash import html, dcc


def inefficiency_section(fig):
    return dbc.Card(
        className="border-danger shadow-sm mb-4",
        children=[
            dbc.CardBody([
                html.H4("🚨 Détection d’inefficiences"),
                html.P(
                    "Identification des séjours atypiques en durée et/ou en coût.",
                    className="text-danger fw-bold"
                ),
                dcc.Graph(figure=fig)
            ])
        ]
    )
