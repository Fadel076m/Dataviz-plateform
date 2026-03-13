import plotly.express as px
import plotly.graph_objects as go
from utils.colors import MEDICAL_COLORS, DEPARTMENT_COLORS, CUSTOM_TEMPLATE

def department_bar_chart(df, department_kpis_func, metric="cost"):
    """Graphique comparatif par département"""
    dept_df = department_kpis_func(df)
    
    # Configuration selon la métrique choisie
    if metric == "stay":
        y_col = "avg_stay"
        color_col = MEDICAL_COLORS["primary"]
        title_y = "Durée moyenne (jours)"
        text_format = ".1f"
        suffix = "j"
    else:
        y_col = "avg_cost"
        color_col = MEDICAL_COLORS["secondary"]
        title_y = "Coût moyen (€)"
        text_format = ",.0f"
        suffix = "€"
    
    fig = px.bar(
        dept_df,
        x="Departement",
        y=y_col,
        title="",
        color_discrete_sequence=[color_col]
    )
    
    fig.update_layout(
        xaxis_title="<b>Département</b>",
        yaxis_title=f"<b>{title_y}</b>",
        template=CUSTOM_TEMPLATE,
        showlegend=False
    )
    
    # Ajouter des annotations
    for i, row in dept_df.iterrows():
        val = row[y_col]
        fig.add_annotation(
            x=row["Departement"],
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


def department_sunburst(df):
    """Sunburst chart hiérarchique"""
    # Préparer les données
    dept_data = df.groupby(['Departement', 'Maladie']).agg({
        'PatientID': 'count',
        'Cout': 'mean',
        'DureeSejour': 'mean'
    }).reset_index()
    
    fig = px.sunburst(
        dept_data,
        path=['Departement', 'Maladie'],
        values='PatientID',
        color='Cout',
        color_continuous_scale=px.colors.sequential.Blues,
        title=""
    )
    
    fig.update_layout(
        template=CUSTOM_TEMPLATE,
        margin=dict(t=30, l=0, r=0, b=0)
    )
    
    return fig