import plotly.express as px
from utils.metrics import inefficiency_flags

def scatter_inefficiencies(df):
    """Scatter plot des inefficiences"""
    dff = inefficiency_flags(df.copy())
    
    fig = px.scatter(
        dff,
        x="DureeSejour",
        y="Cout",
        color="Maladie",
        size="Cout",
        hover_data=["PatientID", "Departement", "Traitement"],
        title="Détection des séjours atypiques"
    )
    
    # Ajout de lignes de seuil
    q95_duree = df["DureeSejour"].quantile(0.95)
    q95_cout = df["Cout"].quantile(0.95)
    
    fig.add_hline(y=q95_cout, line_dash="dash", line_color="red")
    fig.add_vline(x=q95_duree, line_dash="dash", line_color="red")
    
    fig.update_layout(template="plotly_white")
    
    return fig