# app.py
import dash
import dash_bootstrap_components as dbc
from dash import html
import plotly.express as px

# Imports projets
from data.loader import load_data
from utils.metrics import global_kpis, pathology_kpis, department_kpis, profile_kpis

# Components
from components.filters import filters_layout
from components.context import context_section
from components.kpis import kpi_cards
from components.conclusion import conclusion_section
from components.callbacks import register_component_callbacks

# Features
from features.pathology.layout import pathology_section
from features.pathology.charts import pathology_bar_chart
from features.pathology.callbacks import register_pathology_callbacks

from features.department.layout import department_section
from features.department.charts import department_bar_chart
from features.department.callbacks import register_department_callbacks

from features.profile.layout import profile_section
from features.profile.charts import profile_bar_chart
from features.profile.callbacks import register_profile_callbacks

from features.inefficiency.layout import inefficiency_section
from features.inefficiency.charts import scatter_inefficiencies
from features.inefficiency.callbacks import register_inefficiency_callbacks


# Chargement des données
df = load_data("hospital_data.csv")

# Calcul des KPI initiaux
kpis = global_kpis(df)

# Création des graphiques initiaux
# 1. Graphique pathologie
patho_df = pathology_kpis(df)
fig_pathology = pathology_bar_chart(df, pathology_kpis)

# 2. Graphique département
dept_df = department_kpis(df)
fig_department = department_bar_chart(df, department_kpis)

# 3. Graphique profil
profile_df = profile_kpis(df)
fig_profile = profile_bar_chart(df, profile_kpis)

# 4. Graphique inefficiences
fig_ineff = scatter_inefficiencies(df)


# Création de l'application
app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                suppress_callback_exceptions=True)

# Ajout du CSS
app.css.config.serve_locally = True
app.css.append_css({"external_url": "assets/styles.css"})

# Layout de l'application
app.layout = dbc.Container(
    fluid=True,
    className="p-4",
    children=[
        # Section de contexte
        context_section(),
        
        # Filtres
        filters_layout(df),
        
        # KPI Cards (sera mis à jour par les callbacks)
        html.Div(id="kpi-container", children=kpi_cards(kpis)),
        
        # Graphiques (avec IDs pour les callbacks)
        pathology_section(fig_pathology),
        department_section(fig_department),
        profile_section(fig_profile),
        inefficiency_section(fig_ineff),
        
        # Conclusion
        conclusion_section()
    ]
)

# Enregistrement des callbacks
register_component_callbacks(app, df)
register_pathology_callbacks(app, df)
register_department_callbacks(app, df)
register_profile_callbacks(app, df)
register_inefficiency_callbacks(app, df)

if __name__ == "__main__":
    app.run(debug=True, port=8050)