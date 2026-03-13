# filters.py
import dash_bootstrap_components as dbc
from dash import html, dcc

def filters_layout(df):
    return dbc.Card(
        className="filter-card",
        children=[
            dbc.CardBody([
                html.H5("🎛️ Filtres analytiques", className="mb-4"),
                
                dbc.Row([
                    dbc.Col([
                        html.Label("🏥 Département", className="fw-bold mb-2"),
                        dcc.Dropdown(
                            id="filter-department",
                            options=[
                                {"label": d, "value": d}
                                for d in sorted(df["Departement"].unique())
                            ],
                            multi=True,
                            placeholder="Sélectionnez un département...",
                            className="filter-dropdown"
                        )
                    ], md=3, className="mb-3"),
                    
                    dbc.Col([
                        html.Label("🩺 Pathologie", className="fw-bold mb-2"),
                        dcc.Dropdown(
                            id="filter-pathology",
                            options=[
                                {"label": m, "value": m}
                                for m in sorted(df["Maladie"].unique())
                            ],
                            multi=True,
                            placeholder="Sélectionnez une pathologie...",
                            className="filter-dropdown"
                        )
                    ], md=3, className="mb-3"),
                    
                    dbc.Col([
                        html.Label("👶 Tranche d'âge", className="fw-bold mb-2"),
                        dcc.Dropdown(
                            id="filter-age",
                            options=[
                                {"label": a, "value": a}
                                for a in df["AgeGroup"].dropna().unique()
                            ],
                            multi=True,
                            placeholder="Sélectionnez une tranche...",
                            className="filter-dropdown"
                        )
                    ], md=3, className="mb-3"),
                    
                    dbc.Col([
                        html.Label("⚤ Sexe", className="fw-bold mb-2"),
                        dcc.Dropdown(
                            id="filter-sex",
                            options=[
                                {"label": "Homme", "value": "M"},
                                {"label": "Femme", "value": "F"}
                            ],
                            multi=True,
                            placeholder="Sélectionnez le sexe...",
                            className="filter-dropdown"
                        )
                    ], md=3, className="mb-3"),
                ]),
                
                # Bouton reset
                dbc.Row([
                    dbc.Col([
                        html.Button("🔄 Réinitialiser les filtres", 
                                   id="reset-filters",
                                   className="btn btn-outline-primary btn-sm mt-2",
                                   n_clicks=0)
                    ], md=12, className="text-end")
                ])
            ])
        ]
    )