import dash_bootstrap_components as dbc
from dash import html, dcc

def profile_section(fig):
    return dbc.Card(
        className="shadow-sm mb-4",
        children=[
            dbc.CardBody([
                html.Div([
                    html.Div([
                        html.H4("👥 Analyse par profil patient"),
                        html.P(
                            "Analyse des durées et coûts selon l’âge des patients.",
                            style={"fontStyle": "italic", "marginBottom": "0"}
                        ),
                    ]),
                    # Selecteur de métrique
                    html.Div([
                        dbc.RadioItems(
                            id="profile-metric-selector",
                            className="btn-group",
                            inputClassName="btn-check",
                            labelClassName="btn btn-outline-primary",
                            labelCheckedClassName="active",
                            options=[
                                {"label": "Coût moyen (€)", "value": "cost"},
                                {"label": "Durée moyenne (jours)", "value": "stay"},
                            ],
                            value="cost",
                        )
                    ], className="ms-auto")
                ], className="d-flex align-items-center mb-4"),
                
                dcc.Graph(figure=fig, id="profile-graph")
            ])
        ]
    )
