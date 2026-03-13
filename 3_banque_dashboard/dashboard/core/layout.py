
from dash import dcc, html
import dash_bootstrap_components as dbc
import pandas as pd
from dashboard.core.settings import COLORS

def create_layout(df):
    """
    Crée le layout principal avec une navigation par onglets (Tabs).
    """
    
    # Options pour les dropdowns (Sécurisées contre les types mixtes/NaNs)
    years = sorted([y for y in df['ANNEE'].unique() if pd.notna(y)], reverse=True) if not df.empty and 'ANNEE' in df.columns else []
    groups = sorted([str(g) for g in df['Groupe'].unique() if pd.notna(g)]) if not df.empty and 'Groupe' in df.columns else []
    banks = sorted([str(b) for b in df['Sigle'].unique() if pd.notna(b)]) if not df.empty and 'Sigle' in df.columns else []
    
    default_year = years[0] if years else None
    default_bank = "UBA" if "UBA" in banks else (banks[0] if banks else None)


    # --- Barre Latérale (Sidebar) ---
    sidebar = html.Div([
        html.Div([
            html.Div(html.I(className="fas fa-university fa-3x text-warning mb-3")),
            html.H2("BCEAO Insight", className="text-white text-center pb-2", style={'fontWeight': '900', 'fontSize': '1.5rem'}),
            html.P("Fadel ADAM - Big Data & Data Strategy", className="text-muted text-center small"),
        ], className="text-center pt-4"),

        
        html.Hr(className="border-light opacity-25"),
        
        # Filtres Globaux
        html.Div([
            html.Label("📅 Année d'Analyse", className="text-white mt-3 fw-bold small"),

            dcc.Dropdown(
                id='year-selector',
                options=[{'label': str(y), 'value': y} for y in years],
                value=default_year,
                clearable=False,
                className="mb-3 shadow-sm custom-dropdown",
                style={'color': '#000000'}
            ),
            
            html.Label("🏢 Filtre Groupe", className="text-white mt-3 fw-bold small"),
            dcc.Dropdown(
                id='group-selector',
                options=[{'label': g, 'value': g} for g in groups],
                value=None,
                placeholder="Tous les groupes",
                className="mb-3 shadow-sm custom-dropdown",
                style={'color': '#000000'}
            ),
            
            html.Label("🏦 Focus Banque", className="text-white mt-3 fw-bold small"),
            dcc.Dropdown(
                id='bank-selector',
                options=[{'label': b, 'value': b} for b in banks],
                value=default_bank,
                clearable=False,
                className="mb-4 shadow-sm custom-dropdown",
                style={'color': '#000000'}
            ),

        ], className="px-3"),
        
        html.Div(style={"height": "50px"}),


        html.Div([
            # Composant invisible pour le téléchargement
            dcc.Download(id="download-report-pdf"),
            
            # Bouton Export Notebook
            dbc.Button([
                html.I(className="fas fa-file-pdf me-2"),
                "Rapport Stratégique"
            ],
                       id="btn-generate-report",
                       color="warning",
                       className="w-100 shadow-sm fw-bold border-0 d-flex justify-content-center align-items-center py-2"
            ),
            html.P("Génération via Notebook + PDF", className="text-muted x-small text-center mt-2", style={"fontSize": "0.7rem"}),
            html.Div(id="report-loading-status", className="text-center small")
        ], className="px-3 footer-sidebar"),

        # Dummy div pour les callbacks
        html.Div(id='report-status-dummy', style={'display': 'none'})

        
    ], className="sidebar-container d-print-none", 
       style={
        'position': 'fixed', 'top': 0, 'left': 0, 'bottom': 0, 'width': '280px',
        'padding': '2rem 1rem', 'zIndex': 1000, 'background': 'linear-gradient(180deg, #1A3E5C 0%, #0D1F2E 100%)'
    })

    # --- Contenu Principal ---
    content = html.Div([
        # En-tête
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Span("Sénégal | Secteur Bancaire", className="badge bg-soft-primary text-primary mb-2 px-3 py-2"),
                        html.H1("Intelligence Stratégique & Performance", className="fw-bold mb-0"),
                    ])
                ], width=8),
                dbc.Col([
                    html.Div([
                        html.Small("Dernière mise à jour", className="text-muted d-block"),
                        html.Strong(pd.Timestamp.now().strftime('%d %B %Y'))
                    ], className="text-end")
                ], width=4)
            ], className="mb-4 align-items-end")
        ], fluid=True),
        
        # --- Navigation par Onglets (Tabs) ---
        dbc.Container([
            dbc.Tabs([
                dbc.Tab(label="1. VUE MACRO", tab_id="tab-macro", label_class_name="fw-bold px-4 py-3"),
                dbc.Tab(label="2. COMPARATIF", tab_id="tab-comparative", label_class_name="fw-bold px-4 py-3"),
                dbc.Tab(label="3. ANALYSE MICRO", tab_id="tab-micro", label_class_name="fw-bold px-4 py-3"),
                dbc.Tab(label="4. FOCUS UBA", tab_id="tab-uba", label_class_name="fw-bold px-4 py-3"),
            ], id="main-tabs", active_tab="tab-macro", className="mb-4 custom-tabs"),
            
            # Conteneur Dynamique pour le contenu des onglets
            html.Div(id="tab-content", className="mt-4 animated fadeIn")
        ], fluid=True),

        # Pied de page
        html.Footer([
            dbc.Container([
                html.Hr(className="opacity-25"),
                dbc.Row([
                    dbc.Col("© 2024 BCEAO Insight | Direction de la Stabilité Financière", className="text-muted small"),
                    dbc.Col("Propulsé par Dash & MongoDB", className="text-muted text-end small")
                ])
            ], fluid=True)
        ], className="mt-auto py-4")
        

    ], style={
        'marginLeft': '280px', 
        'padding': '2rem 3rem', 
        'backgroundColor': 'transparent', 
        'minHeight': '100vh',
        'display': 'flex',
        'flexDirection': 'column'
    })


    return html.Div([sidebar, content])
