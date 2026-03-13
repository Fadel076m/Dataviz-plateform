
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from dashboard.core.settings import COLORS


def render_comparative_view(df, selected_year, selected_bank, selected_group=None):

    """
    PHASE 3 : Vue Comparative — Classement et compétitivité
    """
    if df.empty:
        return dbc.Alert("Données non disponibles", color="danger")

    # 1. Filtrage
    df_year = df[df['ANNEE'] == selected_year].copy()
    if selected_group:
        df_year = df_year[df_year['Groupe'] == selected_group]

    if df_year.empty:
        return dbc.Alert(f"Aucune donnée pour l'année {selected_year}", color="warning")


    # 2. Calculs de Performance
    # Calcul de la productivité (Bilan / Effectif)
    df_year['PRODUCTIVITE'] = df_year['BILAN'] / df_year['EFFECTIF'].replace(0, np.nan)
    
    # Calcul du ratio Ressources / Bilan
    df_year['RATIO_RESS_BILAN'] = (df_year['RESSOURCES'] / df_year['BILAN']).replace([np.inf, -np.inf], np.nan) * 100
    
    # Sécurisation contre les valeurs extrêmes
    df_year = df_year.replace([np.inf, -np.inf], np.nan).fillna(0)


    # Score Composite de Compétitivité (Normalisation 0-1)
    metrics_to_score = {
        'BILAN': 1,
        'FONDS.PROPRE': 1,
        'RESULTAT.NET': 1,
        'PRODUCTIVITE': 1,
        'R_SOLVABILITE': 1
    }
    
    df_score = df_year.copy()
    for metric, weight in metrics_to_score.items():
        if metric in df_score.columns:
            m_min = df_score[metric].min()
            m_max = df_score[metric].max()
            if m_max > m_min:
                df_score[f'SCORE_{metric}'] = (df_score[metric] - m_min) / (m_max - m_min)
            else:
                df_score[f'SCORE_{metric}'] = 0
    
    score_cols = [f'SCORE_{m}' for m in metrics_to_score.keys() if f'SCORE_{m}' in df_score.columns]
    df_score['COMPOSITE_SCORE'] = df_score[score_cols].mean(axis=1) * 100
    df_score = df_score.sort_values('COMPOSITE_SCORE', ascending=False)


    # --- VISUALISATIONS ---

    # A. Top Bilan avec Segmentation et Focus UBA
    df_rank = df_year.sort_values('BILAN', ascending=False).reset_index(drop=True)
    num_banks = len(df_rank)
    total_bilan_sector = df_rank['BILAN'].sum()
    
    # Définition des couleurs : Accent sur UBA
    colors_ranking = ['rgba(255, 255, 255, 0.2)'] * len(df_rank)
    uba_idx = df_rank[df_rank['Sigle'] == 'UBA'].index
    if not uba_idx.empty:
        colors_ranking[uba_idx[0]] = '#E74C3C' # Rouge vif pour UBA

    fig_top_bilan = go.Figure()

    # Ajout des barres
    fig_top_bilan.add_trace(go.Bar(
        x=df_rank['BILAN'],
        y=df_rank['Sigle'],
        orientation='h',
        marker=dict(color=colors_ranking, line=dict(color='rgba(255,255,255,0.1)', width=1)),
        text=df_rank['BILAN'].apply(lambda x: f"{x:,.0f}M"),
        textposition='outside',
        cliponaxis=False
    ))


    # Seuils de segmentation (adaptatifs)
    max_b = df_rank['BILAN'].max() if not df_rank.empty else 0
    threshold_grandes = max_b * 0.6
    threshold_moyennes = max_b * 0.2

    # Lignes de séparation pointillés (Sécurisation des indices)
    idx_grandes = df_rank[df_rank['BILAN'] < threshold_grandes].index
    if not idx_grandes.empty:
        fig_top_bilan.add_hline(y=idx_grandes[0]-0.5, line_dash="dot", line_color="rgba(212, 175, 55, 0.5)")
    
    idx_moyennes = df_rank[df_rank['BILAN'] < threshold_moyennes].index
    if not idx_moyennes.empty:
        fig_top_bilan.add_hline(y=idx_moyennes[0]-0.5, line_dash="dot", line_color="rgba(255, 255, 255, 0.3)")

    # Ajout des annotations de segments (Boîtes à droite)
    fig_top_bilan.add_annotation(x=1.05, y=0.85, xref="paper", yref="paper", text="<b>GRANDES BANQUES</b><br>Bilan > 60% du Max", showarrow=False, font=dict(color="white", size=10), bgcolor="rgba(26, 62, 92, 0.8)", bordercolor="#D4AF37", borderwidth=1, borderpad=10)
    fig_top_bilan.add_annotation(x=1.05, y=0.5, xref="paper", yref="paper", text="<b>BANQUES MOYENNES</b><br>Bilan entre 20% et 60%", showarrow=False, font=dict(color="white", size=10), bgcolor="rgba(52, 152, 219, 0.5)", bordercolor="white", borderwidth=1, borderpad=10)
    fig_top_bilan.add_annotation(x=1.05, y=0.15, xref="paper", yref="paper", text="<b>PETITES BANQUES</b><br>Bilan < 20% du Max", showarrow=False, font=dict(color="white", size=10), bgcolor="rgba(149, 165, 166, 0.3)", bordercolor="white", borderwidth=1, borderpad=10)

    fig_top_bilan.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis={'categoryorder':'total ascending', 'tickfont': {'size': 9}},
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=80, r=150, t=20, b=20),
        height=600,
        showlegend=False
    )


    # Création du résumé textuel
    sector_summary = html.Div([
        html.H5([
            "Le secteur Bancaire Sénégalais compte ",
            html.Span(f"{num_banks} banques", className="text-warning fw-bold"),
            " représentant un total bilan de ",
            html.Span(f"{total_bilan_sector:,.0f} M CFA", className="text-warning fw-bold"),
            "."
        ], className="mb-1 text-white", style={'fontSize': '1.1rem', 'lineHeight': '1.4'}),
        html.P(f"CLASSEMENT GLOBAL PAR TOTAL BILAN ({selected_year})", className="text-muted small mb-3", style={'letterSpacing': '2px'})
    ], className="mb-4 text-center")



    # --- B. DIAGNOSTIC DE POSITIONNEMENT DES BANQUES (TCAM vs Part de Marché) ---
    available_years = sorted(df['ANNEE'].unique())
    start_year = available_years[0] if available_years else selected_year
    n_years = selected_year - start_year
    if n_years <= 0: n_years = 1 

    def get_bank_positioning_fig(metric_col, title_label):
        temp_df = df.copy()
        # Simulation
        if metric_col == 'EMPLOIS' and 'EMPLOIS' not in temp_df.columns:
            temp_df['EMPLOIS'] = temp_df['BILAN'] * 0.72 
        if metric_col == 'COMPTES' and 'COMPTES' not in temp_df.columns:
            temp_df['COMPTES'] = temp_df['NB_AGENCES'] * 3500 + (temp_df['BILAN'] / 50)

        # Parts de marché
        df_end = temp_df[temp_df['ANNEE'] == selected_year].groupby('Sigle')[metric_col].sum()
        total_end = df_end.sum()
        
        # TCAM
        df_start = temp_df[temp_df['ANNEE'] == start_year].groupby('Sigle')[metric_col].sum()
        
        plot_data = []
        for b in df_end.index:
            val_end = df_end[b]
            val_start = df_start.get(b, 0)
            share = (val_end / total_end * 100) if total_end > 0 else 0
            tcam = (((val_end / val_start)**(1/n_years) - 1) * 100) if val_start > 0 and val_end > 0 else 0
            plot_data.append({'Sigle': b, 'Share': share, 'TCAM': tcam})
            
        pdf = pd.DataFrame(plot_data)
        
        # Highlight logic
        pdf['Color'] = 'rgba(255, 255, 255, 0.4)'
        pdf['Size'] = 10
        if selected_bank in pdf['Sigle'].values:
            pdf.loc[pdf['Sigle'] == selected_bank, 'Color'] = '#E74C3C' # Rouge pour Focus
            pdf.loc[pdf['Sigle'] == selected_bank, 'Size'] = 18

        fig = px.scatter(
            pdf, x='Share', y='TCAM', text='Sigle',
            labels={'Share': f'Part de marché {selected_year} (%)', 'TCAM': f'TCAM {start_year}-{selected_year} (%)'},
            title=f"Positionnement : {title_label}"
        )
        
        fig.update_traces(
            marker=dict(size=pdf['Size'], color=pdf['Color'], line=dict(width=1, color='white')),
            textposition='top center',
            textfont=dict(size=9, color='white')
        )
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)', zerolinecolor='rgba(255,255,255,0.2)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.05)', zerolinecolor='rgba(255,255,255,0.2)'),
            margin=dict(l=40, r=40, t=50, b=40),
            height=320,
            showlegend=False
        )
        return fig

    fig_pos_bilan = get_bank_positioning_fig('BILAN', "TOTAL BILAN")
    fig_pos_emplois = get_bank_positioning_fig('EMPLOIS', "EMPLOIS")
    fig_pos_ressources = get_bank_positioning_fig('RESSOURCES', "RESSOURCES")
    fig_pos_comptes = get_bank_positioning_fig('COMPTES', "NOMBRE DE COMPTES")





    return html.Div([
        html.Div([
            html.H3("VUE COMPARATIVE — CLASSEMENT ET COMPÉTITIVITÉ", className="fw-bold mb-1", style={'color': '#D4AF37'}),
            html.P("Analyse de la force relative et de l'efficacité opérationnelle des acteurs.", className="text-white opacity-75"),
        ], className="mb-4 fadeIn"),




        # 📊 Ligne 1 : Structure & Ranking
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🏢 Structure & Classement du Marché", className="fw-bold"),
                    dbc.CardBody([
                        sector_summary,
                        dcc.Graph(figure=fig_top_bilan, config={'displayModeBar': False})
                    ])
                ], className="shadow-sm border-0 h-100")
            ], width=12),
        ], className="g-4 mb-4"),

        # 🎯 Ligne 2 : Analyse de Positionnement (TCAM vs Parts de Marché)
        html.Div([
            html.H4(f"🎯 POSITIONNEMENT STRATÉGIQUE DES BANQUES (Focus: {selected_bank})", className="fw-bold mb-3 mt-4", style={'color': '#D4AF37'}),
            html.P(f"Dynamique de croissance (TCAM) vs Emprise commerciale ({start_year} - {selected_year})", className="text-white opacity-75 mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([dbc.CardBody(dcc.Graph(figure=fig_pos_bilan, config={'displayModeBar': False}))], className="shadow-sm border-0")
                ], width=12, lg=6),
                dbc.Col([
                    dbc.Card([dbc.CardBody(dcc.Graph(figure=fig_pos_emplois, config={'displayModeBar': False}))], className="shadow-sm border-0")
                ], width=12, lg=6),
            ], className="g-4 mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([dbc.CardBody(dcc.Graph(figure=fig_pos_ressources, config={'displayModeBar': False}))], className="shadow-sm border-0")
                ], width=12, lg=6),
                dbc.Col([
                    dbc.Card([dbc.CardBody(dcc.Graph(figure=fig_pos_comptes, config={'displayModeBar': False}))], className="shadow-sm border-0")
                ], width=12, lg=6),
            ], className="g-4"),
        ], className="fadeIn")
    ])

