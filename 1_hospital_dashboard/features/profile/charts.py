import plotly.express as px
import plotly.graph_objects as go
from utils.colors import MEDICAL_COLORS, AGE_GROUP_COLORS, CUSTOM_TEMPLATE

def profile_bar_chart(df, profile_kpis_func, metric="cost"):
    """Graphique coût/durée par tranche d'âge"""
    profile_df = profile_kpis_func(df)
    
    # Configuration selon la métrique choisie
    if metric == "stay":
        y_col = "avg_stay"
        color_col = MEDICAL_COLORS["primary"]
        title_y = "Durée moyenne (jours)"
        text_format = ".1f"
        suffix = "j"
    else:
        y_col = "avg_cost"
        color_col = MEDICAL_COLORS["warning"]
        title_y = "Coût moyen (€)"
        text_format = ",.0f"
        suffix = "€"
    
    fig = px.bar(
        profile_df,
        x="AgeGroup",
        y=y_col,
        title="",
        color_discrete_sequence=[color_col]
    )
    
    fig.update_layout(
        xaxis_title="<b>Tranche d'âge</b>",
        yaxis_title=f"<b>{title_y}</b>",
        template=CUSTOM_TEMPLATE,
        showlegend=False
    )
    
    # Ajouter des annotations
    for i, row in profile_df.iterrows():
        val = row[y_col]
        fig.add_annotation(
            x=row["AgeGroup"],
            y=val,
            text=f"<b>{val:{text_format}}{suffix}</b>",
            showarrow=False,
            font=dict(size=12, color=color_col),
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor=color_col,
            borderwidth=1,
            borderpad=3,
            yshift=10
        )
    
    return fig


def age_distribution_chart(df):
    """Distribution des âges"""
    fig = px.histogram(
        df,
        x="Age",
        nbins=20,
        title="",
        color_discrete_sequence=[MEDICAL_COLORS['primary']],
        opacity=0.8
    )
    
    # Ajouter une ligne pour la moyenne
    avg_age = df["Age"].mean()
    fig.add_vline(
        x=avg_age,
        line_dash="dash",
        line_color=MEDICAL_COLORS['accent'],
        annotation_text=f"Moyenne: {avg_age:.1f} ans",
        annotation_position="top right"
    )
    
    fig.update_layout(
        template=CUSTOM_TEMPLATE,
        xaxis_title="<b>Âge</b>",
        yaxis_title="<b>Nombre de patients</b>",
        bargap=0.1
    )
    
    return fig