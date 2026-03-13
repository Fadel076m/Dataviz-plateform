
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dashboard.components.cards import create_kpi_card
from dashboard.core.settings import COLORS

def generate_strategic_summary(row, sector_avg):
    """Génère un résumé textuel dynamique pour UBA"""
    
    forces = []
    faiblesses = []
    
    # Logique pour les forces
    if row['R_SOLVABILITE'] > 12:
        forces.append("Excellente solidité financière avec un ratio de solvabilité très supérieur aux normes réglementaires.")
    elif row['R_SOLVABILITE'] > 8:
        forces.append("Structure de capital conforme aux exigences de Bâle III.")
        
    if row['R_ROE'] > sector_avg['R_ROE']:
        forces.append(f"Rentabilité des fonds propres ({row['R_ROE']:.1f}%) supérieure à la moyenne du marché.")
    
    # Logique pour les faiblesses
    if row['R_ROE'] < 5:
        faiblesses.append("Faiblesse relative de la rentabilité nette par rapport aux capitaux engagés.")
    
    if row['NB_AGENCES'] < sector_avg['NB_AGENCES'] * 0.5:
        faiblesses.append("Réseau physique restreint par rapport aux leaders du marché, limitant la collecte de dépôts de détail.")

    # Recommandations
    recos = [
        "Accélérer la digitalisation des services pour compenser le réseau physique limité.",
        "Optimiser le coefficient d'exploitation pour améliorer le ROE.",
        "Renforcer le positionnement sur le segment Corporate pour capitaliser sur le réseau panafricain du groupe."
    ]

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H5("💪 Forces", className="text-success fw-bold"),
                html.Ul([html.Li(f) for f in forces]) if forces else html.P("Aucun point saillant identifié.")
            ], width=12, lg=6),
            dbc.Col([
                html.H5("⚠️ Points de Vigilance", className="text-danger fw-bold"),
                html.Ul([html.Li(f) for f in faiblesses]) if faiblesses else html.P("Stabilité opérationnelle correcte.")
            ], width=12, lg=6),
        ], className="mb-4"),
        html.Hr(),
        html.H5("🚀 Recommandations Stratégiques", className="text-primary fw-bold"),
        html.Ul([html.Li(r) for r in recos])
    ])

def render_uba_focus(df, selected_year):
    """
    PHASE 4 : Cas d'étude : United Bank for Africa (UBA)
    """
    uba_data = df[df['Sigle'] == 'UBA'].sort_values('ANNEE')
    uba_year = uba_data[uba_data['ANNEE'] == selected_year]
    
    if uba_year.empty:
        return dbc.Alert("Données UBA non disponibles pour cette année.", color="warning")

    row = uba_year.iloc[0]
    sector_data = df[df['ANNEE'] == selected_year]
    sector_avg = sector_data.mean(numeric_only=True)

    # --- VISUALISATIONS SPÉCIFIQUES ---


    # 1. Positionnement Scatter (Bilan vs Solvabilité)
    fig_scatter = px.scatter(
        sector_data, x='R_SOLVABILITE', y='BILAN',
        size='FONDS.PROPRE', color='Groupe', hover_name='Sigle',
        title="Bilan vs Solvabilité (UBA mis en avant)",
        template="plotly_dark"
    )
    # Ajouter UBA spécifiquement
    fig_scatter.add_trace(go.Scatter(
        x=[row['R_SOLVABILITE']], y=[row['BILAN']],
        mode='markers+text', text=["UBA"], textposition="top center",
        marker=dict(size=25, color='#E74C3C', symbol='star', line=dict(width=2, color='white')),
        name="Focus UBA"
    ))
    fig_scatter.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    # 2. Part de Marché Relative
    total_sector_bilan = sector_data['BILAN'].sum()
    uba_market_share = (row['BILAN'] / total_sector_bilan) * 100 if total_sector_bilan > 0 else 0
    
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = uba_market_share,
        title = {'text': "Part de Marché (%)", 'font': {'color': 'white', 'size': 14}},
        number = {'font': {'color': '#D4AF37', 'size': 30}},
        gauge = {
            'axis': {'range': [0, 20], 'tickcolor': "white"},
            'bar': {'color': "#D4AF37"},
            'bgcolor': "rgba(0,0,0,0)",
            'bordercolor': "white",
            'steps': [
                {'range': [0, 5], 'color': 'rgba(255, 255, 255, 0.05)'},
                {'range': [5, 10], 'color': 'rgba(255, 255, 255, 0.1)'}
            ],
        }
    ))
    fig_gauge.update_layout(height=250, margin=dict(t=50, b=20, l=30, r=30), paper_bgcolor='rgba(0,0,0,0)', font_color="white")



    return html.Div([
        html.Div([
            html.Img(src="https://www.ubagroup.com/wp-content/uploads/2018/09/uba-logo.png", style={"height": "40px", "float": "right"}),
            html.H3("FOCUS STRATÉGIQUE : UBA SÉNÉGAL", className="fw-bold mb-1", style={'color': '#D4AF37'}),
            html.P(f"Analyse comparative et diagnostic stratégique - Exercice {selected_year}", className="text-white opacity-75"),
        ], className="mb-4 clearfix fadeIn"),


        # 🔴 Ligne 1 : Résumé Stratégique (Le Dashboard intelligent)
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🧠 Diagnostic Automatique & Recommandations", className="bg-danger text-white fw-bold"),
                    dbc.CardBody(generate_strategic_summary(row, sector_avg))
                ], className="shadow border-danger mb-4")
            ], width=12)
        ]),

        # 📊 Ligne 2 : Positionnement Concurrentiel
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📍 Positionnement Marché", className="fw-bold"),
                    dbc.CardBody(dcc.Graph(figure=fig_scatter, config={'displayModeBar': False}))
                ], className="shadow-sm border-0 h-100")
            ], width=12, lg=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📈 Emprise Commerciale", className="fw-bold"),
                    dbc.CardBody([
                        dcc.Graph(figure=fig_gauge, config={'displayModeBar': False}),
                        html.P(f"UBA détient {uba_market_share:.2f}% des actifs bancaires au Sénégal en {selected_year}.", className="text-center small text-muted")
                    ])
                ], className="shadow-sm border-0 h-100")
            ], width=12, lg=4),
        ], className="g-4 mb-4"),

        # 📉 Ligne 3 : Trajectoire vs Secteur
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Comparaison des Fondamentaux (vs Moyenne Secteur)", className="fw-bold"),
                    dbc.CardBody([
                        html.Table([
                            html.Thead(html.Tr([html.Th("Indicateur"), html.Th("UBA"), html.Th("Moyenne Secteur"), html.Th("Écart")])),
                            html.Tbody([
                                html.Tr([
                                    html.Td("Bilan (M CFA)"), html.Td(f"{row['BILAN']:,.0f}"), html.Td(f"{sector_avg['BILAN']:,.0f}"),
                                    html.Td(f"{((row['BILAN']/sector_avg['BILAN'])-1)*100:+.1f}%", className="text-success" if row['BILAN'] > sector_avg['BILAN'] else "text-danger")
                                ]),
                                html.Tr([
                                    html.Td("Solvabilité (%)"), html.Td(f"{row['R_SOLVABILITE']:.1f}%"), html.Td(f"{sector_avg['R_SOLVABILITE']:.1f}%"),
                                    html.Td(f"{row['R_SOLVABILITE'] - sector_avg['R_SOLVABILITE']:+.1f} pts", className="text-success" if row['R_SOLVABILITE'] > sector_avg['R_SOLVABILITE'] else "text-danger")
                                ]),
                                html.Tr([
                                    html.Td("ROE (%)"), html.Td(f"{row['R_ROE']:.1f}%"), html.Td(f"{sector_avg['R_ROE']:.1f}%"),
                                    html.Td(f"{row['R_ROE'] - sector_avg['R_ROE']:+.1f} pts", className="text-success" if row['R_ROE'] > sector_avg['R_ROE'] else "text-danger")
                                ]),
                            ])
                        ], className="table table-sm table-borderless")
                    ])
                ], className="shadow-sm border-0")
            ], width=12)
        ], className="g-4")
    ])
