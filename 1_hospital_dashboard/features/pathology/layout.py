# pathology_section.py
import dash_bootstrap_components as dbc
from dash import html, dcc

def pathology_section(fig):
    return dbc.Card(
        className="analysis-section border-0",
        children=[
            dbc.CardBody([
                html.Div([
                    html.Span("📈", className="fs-2 me-3"),
                    html.Div([
                        html.H4("Analyse par pathologie", className="mb-1"),
                        html.P("Identification des pathologies les plus consommatrices de ressources",
                              className="text-muted mb-0")
                    ]),
                    # Selecteur de métrique
                    html.Div([
                        dbc.RadioItems(
                            id="pathology-metric-selector",
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
                
                dcc.Graph(
                    figure=fig, 
                    id="pathology-graph",
                    className="graph-container",
                    config={
                        'displayModeBar': True,
                        'displaylogo': False,
                        'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
                        'toImageButtonOptions': {
                            'format': 'png',
                            'filename': 'analyse_pathologies',
                            'height': 500,
                            'width': 1200,
                            'scale': 2
                        }
                    }
                ),
                
                # Légende d'interprétation
                # Astuce d'interaction
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Small("💡 ", className="text-primary"),
                            html.Small("Utilisez les boutons ci-dessus pour basculer entre l'analyse des coûts et des durées d'hospitalisation.", className="text-muted"),
                        ], className="mt-2 text-center")
                    ], md=12)
                ])
            ])
        ]
    )