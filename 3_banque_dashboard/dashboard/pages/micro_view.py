
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dashboard.components.cards import create_kpi_card, create_ratio_card
from dashboard.core.settings import COLORS

def render_micro_view(df, selected_year, selected_bank):
    """
    PHASE 4 (Générique) : Vue Micro — Positionnement stratégique d'une banque spécifique
    """
    if df.empty:
        return dbc.Alert("Données non disponibles", color="danger")

    # 1. Filtrage
    bank_data = df[df['Sigle'] == selected_bank].sort_values('ANNEE')
    bank_year = bank_data[bank_data['ANNEE'] == selected_year]
    
    if bank_year.empty:
        return dbc.Alert(f"Pas de données pour {selected_bank} en {selected_year}", color="warning")

    row = bank_year.iloc[0]
    
    # Moyennes secteur pour comparaison
    sector_avg = df[df['ANNEE'] == selected_year].mean(numeric_only=True)


    # --- VISUALISATIONS ---

    # A. Évolution Historique (Bilan & Résultat)
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Bar(x=bank_data['ANNEE'], y=bank_data['BILAN'], name="Bilan", marker_color='#1A3E5C', opacity=0.7))
    fig_hist.add_trace(go.Scatter(x=bank_data['ANNEE'], y=bank_data['RESULTAT.NET'], name="Résultat Net", mode='lines+markers', line=dict(color='#D4AF37', width=3), yaxis='y2'))
    
    fig_hist.update_layout(
        title=f"📈 Croissance Historique : {selected_bank}",
        yaxis=dict(title="Bilan (M CFA)", gridcolor='rgba(255,255,255,0.1)'),
        yaxis2=dict(title="Résultat (M CFA)", overlaying='y', side='right', gridcolor='rgba(255,255,255,0.1)'),
        template="plotly_dark", 
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", y=1.1)
    )

    # B. Radar : Banque vs Secteur
    metrics = ['R_SOLVABILITE', 'R_ROE', 'R_LEVIER']
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=[row[m] for m in metrics],
        theta=['Solvabilité', 'Rentabilité (ROE)', 'Levier'],
        fill='toself', name=selected_bank, 
        line=dict(color='#D4AF37', width=3),
        fillcolor='rgba(212, 175, 55, 0.2)'
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=[sector_avg[m] for m in metrics],
        theta=['Solvabilité', 'Rentabilité (ROE)', 'Levier'],
        fill='toself', name='Moyenne Secteur', 
        line=dict(color='rgba(255,255,255,0.5)', dash='dash'),
        fillcolor='rgba(255,255,255,0.1)'
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, gridcolor='rgba(255,255,255,0.1)'),
            angularaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            bgcolor='rgba(0,0,0,0)'
        ),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        title="🎯 Diagnostic vs Secteur"
    )
    
    # Correction pour les moyennes si manquantes
    sector_avg = sector_avg.fillna(0)



    return html.Div([
        html.Div([
            html.H3(f"🏦 ANALYSE MICRO — FOCUS SUR {selected_bank.upper()}", className="fw-bold mb-1", style={'color': '#D4AF37'}),
            html.P(f"Diagnostic détaillé et positionnement stratégique - Exercice {selected_year}", className="text-white opacity-75"),
        ], className="mb-4 fadeIn"),


        # 🟢 KPIs
        dbc.Row([
            dbc.Col(create_kpi_card("Total Bilan", row['BILAN'], "M CFA", "primary"), width=12, lg=3),
            dbc.Col(create_kpi_card("Résultat Net", row['RESULTAT.NET'], "M CFA", "success" if row['RESULTAT.NET'] > 0 else "danger"), width=12, lg=3),
            dbc.Col(create_kpi_card("Fonds Propres", row['FONDS.PROPRE'], "M CFA", "info"), width=12, lg=3),
            dbc.Col(create_kpi_card("Ressources", row['RESSOURCES'], "M CFA", "secondary"), width=12, lg=3),
        ], className="g-4 mb-4"),

        # 📊 Analyse Profonde
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Indicateurs de Solidité & Rentabilité", className="fw-bold"),
                    dbc.CardBody([
                        create_ratio_card("Solvabilité", row['R_SOLVABILITE'], f"Moyenne secteur: {sector_avg['R_SOLVABILITE']:.1f}%", "success" if row['R_SOLVABILITE'] > 8 else "warning"),
                        create_ratio_card("ROE (Rentabilité)", row['R_ROE'], f"Moyenne secteur: {sector_avg['R_ROE']:.1f}%", "primary"),
                        create_ratio_card("Levier Financier", row['R_LEVIER'], f"Moyenne secteur: {sector_avg['R_LEVIER']:.1f}%", "info"),
                    ])
                ], className="shadow-sm border-0 h-100")
            ], width=12, lg=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody(dcc.Graph(figure=fig_hist, config={'displayModeBar': False}))
                ], className="shadow-sm border-0 h-100")
            ], width=12, lg=8),
        ], className="g-4 mb-4"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody(dcc.Graph(figure=fig_radar, config={'displayModeBar': False}))
                ], className="shadow-sm border-0")
            ], width=12, lg=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Informations Complémentaires", className="fw-bold"),
                    dbc.CardBody([
                        html.Ul([
                            html.Li([html.B("Groupe : "), row['Groupe']]),
                            html.Li([html.B("Nombre d'agences : "), f"{row['NB_AGENCES']:.0f}"]),
                            html.Li([html.B("Effectif : "), f"{row['EFFECTIF']:.0f}"]),
                            html.Li([html.B("Siège : "), "Dakar, Sénégal"]),
                        ], className="list-unstyled")
                    ])
                ], className="shadow-sm border-0 h-100")
            ], width=12, lg=6),
        ], className="g-4")
    ])
