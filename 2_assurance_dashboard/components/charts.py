import plotly.express as px
import plotly.graph_objects as go

# ── Premium Color Palette ─────────────────────────────────
PALETTE = ['#5b6cf9', '#f43f5e', '#10b981', '#f59e0b', '#7c3aed', '#0ea5e9']

FONT = 'Inter, -apple-system, BlinkMacSystemFont, sans-serif'

LAYOUT_DEFAULTS = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family=FONT, color='#1e2235', size=12),
    margin=dict(t=20, l=10, r=10, b=10),
    legend=dict(
        orientation="h",
        yanchor="bottom", y=1.04,
        xanchor="right",  x=1,
        bgcolor="rgba(0,0,0,0)",
        font=dict(size=11)
    ),
    hoverlabel=dict(
        bgcolor='#ffffff',
        bordercolor='rgba(0,0,0,0.08)',
        font=dict(family=FONT, size=12, color='#1e2235')
    )
)

AXIS_STYLE = dict(
    showgrid=True,
    gridcolor='rgba(0,0,0,0.05)',
    linecolor='rgba(0,0,0,0.08)',
    tickfont=dict(size=11, family=FONT, color='#64748b'),
    title_font=dict(size=12, family=FONT, color='#64748b')
)


def _apply_theme(fig):
    fig.update_layout(**LAYOUT_DEFAULTS)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig


# ── Charts ────────────────────────────────────────────────

def create_severity_frequency_chart(df):
    agg = df.groupby('type_assurance').agg({
        'nb_sinistres': 'mean',
        'montant_sinistres': 'mean',
        'id_assure': 'count'
    }).reset_index()

    fig = px.scatter(
        agg,
        x='nb_sinistres',
        y='montant_sinistres',
        size='id_assure',
        color='type_assurance',
        color_discrete_sequence=PALETTE,
        labels={
            'nb_sinistres': 'Fréquence moyenne',
            'montant_sinistres': 'Sévérité moyenne (€)',
            'type_assurance': 'Type'
        },
        size_max=40
    )
    fig.update_traces(marker=dict(opacity=0.85, line=dict(width=1.5, color='white')))
    return _apply_theme(fig)


def create_risk_segmentation_chart(df):
    fig = px.histogram(
        df,
        x='segment_age',
        y='score_risque',
        color='sexe',
        barmode='group',
        histfunc='avg',
        color_discrete_map={'masculin': PALETTE[0], 'feminin': '#f472b6'},
        labels={
            'segment_age': "Tranche d'âge",
            'score_risque': 'Score de risque moyen',
            'sexe': 'Genre'
        }
    )
    fig.update_traces(marker_line_width=0, opacity=0.9)
    return _apply_theme(fig)


def create_profitability_map(df):
    region_perf = (
        df.groupby('region')['rentabilite_nette']
        .sum()
        .sort_values()
        .reset_index()
    )
    fig = px.bar(
        region_perf,
        x='rentabilite_nette',
        y='region',
        orientation='h',
        color='rentabilite_nette',
        color_continuous_scale=[[0, '#f43f5e'], [0.5, '#f59e0b'], [1, '#10b981']],
        labels={'rentabilite_nette': 'Rentabilité Nette (€)', 'region': 'Région'}
    )
    fig.update_traces(marker_line_width=0)
    fig.update_coloraxes(showscale=False)
    return _apply_theme(fig)


def create_bonus_malus_impact(df):
    fig = px.box(
        df,
        x='nb_sinistres',
        y='bonus_malus',
        color_discrete_sequence=[PALETTE[0]],
        labels={
            'nb_sinistres': 'Nombre de sinistres',
            'bonus_malus': 'Coefficient Bonus/Malus'
        }
    )
    fig.update_traces(
        marker=dict(opacity=0.6, size=5),
        line=dict(color=PALETTE[0]),
        fillcolor='rgba(91,108,249,0.12)',
        boxmean='sd'
    )
    return _apply_theme(fig)
