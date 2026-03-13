from dash import Input, Output, callback
from utils.metrics import global_kpis
from components.kpis import kpi_cards

def register_component_callbacks(app, df):
    @app.callback(
        Output("kpi-container", "children"),
        Input("filter-department", "value"),
        Input("filter-pathology", "value"),
        Input("filter-age", "value"),
        Input("filter-sex", "value")
    )
    def update_kpis(dept, patho, age, sex):
        dff = df.copy()

        # Application des filtres
        if dept and len(dept) > 0:
            dff = dff[dff["Departement"].isin(dept)]
        if patho and len(patho) > 0:
            dff = dff[dff["Maladie"].isin(patho)]
        if age and len(age) > 0:
            dff = dff[dff["AgeGroup"].isin(age)]
        if sex and len(sex) > 0:
            dff = dff[dff["Sexe"].isin(sex)]

        # Calcul des KPI
        kpis = global_kpis(dff)
        return kpi_cards(kpis)

    # Callback pour le bouton reset
    @app.callback(
        Output("filter-department", "value"),
        Output("filter-pathology", "value"),
        Output("filter-age", "value"),
        Output("filter-sex", "value"),
        Input("reset-filters", "n_clicks"),
        prevent_initial_call=True
    )
    def reset_filters(n_clicks):
        return [], [], [], []
