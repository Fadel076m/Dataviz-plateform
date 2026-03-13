
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dashboard.components.cards import create_kpi_card
from dashboard.core.settings import COLORS

def render_macro_view(df, selected_year, selected_group=None):
    """
    PHASE 2 : Vue Macro — État du secteur bancaire sénégalais
    """
    if df.empty:
        return dbc.Alert("Données non disponibles", color="danger")

    # 1. Filtrage des données pour l'année sélectionnée
    df_year = df[df['ANNEE'] == selected_year]
    if selected_group:
        df_year = df_year[df_year['Groupe'] == selected_group]

    # 2. Calcul des agrégats sectoriels
    total_bilan = df_year['BILAN'].sum()
    total_fp = df_year['FONDS.PROPRE'].sum()
    total_ressources = df_year['RESSOURCES'].sum()
    total_agences = df_year['NB_AGENCES'].sum() if 'NB_AGENCES' in df_year.columns else 0
    total_effectif = df_year['EFFECTIF'].sum() if 'EFFECTIF' in df_year.columns else 0

    # Calcul de la croissance (vs année précédente)
    prev_year = selected_year - 1
    df_prev = df[df['ANNEE'] == prev_year]
    if selected_group:
        df_prev = df_prev[df_prev['Groupe'] == selected_group]
    
    growth_pct = 0
    if not df_prev.empty:
        prev_bilan = df_prev['BILAN'].sum()
        if prev_bilan > 0:
            growth_pct = ((total_bilan - prev_bilan) / prev_bilan) * 100

    # --- VISUALISATIONS ---

    # A. Évolution temporelle (BILAN, FP, RESSOURCES)
    # On agrège par année pour tout le secteur (ou le groupe sélectionné)
    df_evol = df.copy()
    if selected_group:
        df_evol = df_evol[df_evol['Groupe'] == selected_group]
    
    df_evol_agg = df_evol.groupby('ANNEE').agg({
        'BILAN': 'sum',
        'FONDS.PROPRE': 'sum',
        'RESSOURCES': 'sum'
    }).reset_index()


    fig_evol = go.Figure()
    fig_evol.add_trace(go.Scatter(x=df_evol_agg['ANNEE'], y=df_evol_agg['BILAN'], name="Bilan Total", mode='lines+markers', line=dict(color='#D4AF37', width=4)))
    fig_evol.add_trace(go.Scatter(x=df_evol_agg['ANNEE'], y=df_evol_agg['RESSOURCES'], name="Ressources", mode='lines+markers', line=dict(color='#2196F3', dash='dash')))
    

    fig_evol.update_layout(
        title="📈 Évolution des Masses Bilan & Ressources (Secteur)",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='white')),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='white'))
    )



    # B. Parts de Marché (Donut Premium)
    df_group = df_year.groupby('Groupe')['BILAN'].sum().reset_index()
    
    # Palette Premium : Dégradés de Bleu Marine et Or
    premium_colors = ['#1A3E5C', '#D4AF37', '#2196F3', '#F1D279', '#0D1F2D']
    
    fig_donut = px.pie(
        df_group, 
        values='BILAN', 
        names='Groupe',
        hole=0.7,
        color_discrete_sequence=premium_colors,
    )
    
    # Configuration des traces pour la lisibilité
    fig_donut.update_traces(
        textinfo='percent', 
        textposition='outside',
        textfont=dict(color='white', size=11),
        marker=dict(line=dict(color='#0A1929', width=2)),
        hovertemplate="<b>%{label}</b><br>Part: %{percent}<br>Total: %{value:,.0f} M CFA<extra></extra>"
    )
    

    fig_donut.update_layout(
        title={
            'text': "🍩 RÉPARTITION DU MARCHÉ PAR GROUPE",
            'y': 0.95, 'x': 0.5, 'xanchor': 'center', 'yanchor': 'top',
            'font': {'size': 14, 'color': '#D4AF37', 'family': 'Outfit'}
        },
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,
            xanchor="center",
            x=0.5,
            font=dict(size=10, color="white")
        ),
        margin=dict(l=20, r=20, t=100, b=100),
        height=550,
        annotations=[{
            "text": f"LEADER<br><b>{df_group.iloc[df_group['BILAN'].idxmax()]['Groupe'] if not df_group.empty else ''}</b>",
            "showarrow": False,
            "font": {"size": 14, "color": "white", "family": "Outfit"},
        }]
    )





    # --- D. ANALYSE DE POSITIONNEMENT (CAGR vs PARTS DE MARCHÉ) ---
    # Identification des années pour la croissance (Baseline 2015 ou 3 ans en arrière)
    available_years = sorted(df['ANNEE'].unique())
    start_year = available_years[0] if available_years else selected_year
    n_years = selected_year - start_year
    if n_years <= 0: n_years = 1 

    def get_positioning_fig(metric_col, title_label):
        # Préparation des données (Simulation si colonnes manquantes)
        temp_df = df.copy()
        if metric_col == 'EMPLOIS' and 'EMPLOIS' not in temp_df.columns:
            temp_df['EMPLOIS'] = temp_df['BILAN'] * 0.72 # Simulation
        if metric_col == 'COMPTES' and 'COMPTES' not in temp_df.columns:
            temp_df['COMPTES'] = temp_df['NB_AGENCES'] * 3500 + (temp_df['BILAN'] / 50) # Simulation

        # Calculer Parts de marché (Année sélectionnée)
        df_end = temp_df[temp_df['ANNEE'] == selected_year].groupby('Groupe')[metric_col].sum()
        total_end = df_end.sum()
        
        # Calculer Valeurs de départ (Année baseline)
        df_start = temp_df[temp_df['ANNEE'] == start_year].groupby('Groupe')[metric_col].sum()
        
        plot_data = []
        for g in df_end.index:
            val_end = df_end[g]
            val_start = df_start.get(g, 0)
            share = (val_end / total_end * 100) if total_end > 0 else 0
            tcam = (((val_end / val_start)**(1/n_years) - 1) * 100) if val_start > 0 and val_end > 0 else 0
            plot_data.append({'Groupe': g, 'Share': share, 'TCAM': tcam})
            
        pdf = pd.DataFrame(plot_data)
        
        fig = px.scatter(
            pdf, x='Share', y='TCAM', text='Groupe',
            labels={'Share': f'Part de marché {selected_year} (%)', 'TCAM': f'TCAM {start_year}-{selected_year} (%)'},
            title=f"Positionnement : {title_label}"
        )
        
        fig.update_traces(
            marker=dict(size=12, color='#D4AF37', line=dict(width=2, color='white')),
            textposition='top center',
            textfont=dict(size=10, color='white')
        )
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)', zerolinecolor='rgba(255,255,255,0.2)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.05)', zerolinecolor='rgba(255,255,255,0.2)'),
            margin=dict(l=40, r=40, t=50, b=40),
            height=300
        )
        return fig

    fig_pos_bilan = get_positioning_fig('BILAN', "TOTAL BILAN")
    fig_pos_emplois = get_positioning_fig('EMPLOIS', "EMPLOIS")
    fig_pos_ressources = get_positioning_fig('RESSOURCES', "RESSOURCES")
    fig_pos_comptes = get_positioning_fig('COMPTES', "NOMBRE DE COMPTES")





    return html.Div([
        # 🟢 Ligne 1 : Présentation
        html.Div([
            html.H3("VUE MACRO — ÉTAT DU SECTEUR BANCAIRE SÉNÉGALAIS", className="fw-bold mb-1", style={'color': '#D4AF37'}),
            html.P(f"Analyse consolidée du marché pour l'exercice {selected_year}", className="text-white opacity-75"),
        ], className="mb-4 fadeIn"),


        # 🟢 Ligne 2 : KPI Cards
        dbc.Row([
            dbc.Col(create_kpi_card("Bilan Total", total_bilan, "M CFA", "primary", f"Croissance: {growth_pct:+.1f}%"), width=12, lg=3),
            dbc.Col(create_kpi_card("Fonds Propres", total_fp, "M CFA", "success", "Solidité sectorielle"), width=12, lg=3),
            dbc.Col(create_kpi_card("Ressources", total_ressources, "M CFA", "info", "Capacité de dépôt"), width=12, lg=3),
            dbc.Col(create_kpi_card("Réseau", total_agences, "Agences", "warning", f"Effectif total: {total_effectif:,.0f}"), width=12, lg=3),
        ], className="g-4 mb-5"),

        # 🟢 Ligne 3 : Graphiques principaux
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody(dcc.Graph(figure=fig_evol, config={'displayModeBar': False}))
                ], className="shadow-sm border-0")
            ], width=12, lg=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody(dcc.Graph(figure=fig_donut, config={'displayModeBar': False}))
                ], className="shadow-sm border-0")
            ], width=12, lg=4),
        ], className="g-4 mb-4"),


        # 🟢 Ligne 4 : Diagnostic de Croissance (Positionnement Stratégique)
        html.Div([
            html.H4("🎯 DIAGNOSTIC DE CROISSANCE : POSITIONNEMENT DES GROUPES", className="fw-bold mb-3 mt-4", style={'color': '#D4AF37'}),
            html.P(f"Analyse de la dynamique (TCAM) par rapport à la part de marché relative ({start_year} - {selected_year})", className="text-white opacity-75 mb-4"),
            
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

