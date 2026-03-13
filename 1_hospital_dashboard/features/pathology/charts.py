# pathology_charts.py
import plotly.express as px
import plotly.graph_objects as go
from utils.colors import MEDICAL_COLORS, PATHOLOGY_COLORS, CUSTOM_TEMPLATE

def pathology_bar_chart(df, pathology_kpis_func, metric="cost"):
    """
    Graphique comparatif durée moyenne / coût moyen par pathologie
    metric: 'cost' ou 'stay'
    """
    patho_df = pathology_kpis_func(df)
    
    # Configuration selon la métrique choisie
    if metric == "stay":
        y_col = "avg_stay"
        color_col = MEDICAL_COLORS["primary"]
        title_y = "Durée moyenne (jours)"
        text_format = ".1f"
        suffix = "j"
    else:
        y_col = "avg_cost"
        color_col = MEDICAL_COLORS["accent"]
        title_y = "Coût moyen (€)"
        text_format = ",.0f"
        suffix = "€"

    # Créer le graphique
    fig = px.bar(
        patho_df,
        x="Maladie",
        y=y_col,
        title="",
        color_discrete_sequence=[color_col]
    )
    
    # Mise en forme
    fig.update_layout(
        xaxis_title="<b>Pathologie</b>",
        yaxis_title=f"<b>{title_y}</b>",
        template=CUSTOM_TEMPLATE,
        showlegend=False,
        margin=dict(l=50, r=50, t=30, b=50)
    )
    
    # Ajouter des annotations pour les valeurs
    for i, row in patho_df.iterrows():
        val = row[y_col]
        fig.add_annotation(
            x=row["Maladie"],
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


def pathology_pie_chart(df):
    """
    Répartition des patients par pathologie
    """
    patho_counts = df["Maladie"].value_counts().reset_index()
    patho_counts.columns = ["Maladie", "count"]
    
    fig = px.pie(
        patho_counts,
        values="count",
        names="Maladie",
        title="",
        color="Maladie",
        color_discrete_map=PATHOLOGY_COLORS,
        hole=0.4
    )
    
    fig.update_layout(
        template=CUSTOM_TEMPLATE,
        showlegend=True,
        legend=dict(
            title="<b>Pathologies</b>",
            orientation="v"
        ),
        annotations=[dict(
            text=f"Total<br>{df.shape[0]}<br>patients",
            x=0.5, y=0.5,
            font_size=14,
            showarrow=False,
            font_color=MEDICAL_COLORS['dark']
        )]
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        insidetextorientation='radial',
        hovertemplate="<b>%{label}</b><br>Patients: %{value}<br>%{percent}",
        marker=dict(line=dict(color='white', width=1))
    )
    
    return fig