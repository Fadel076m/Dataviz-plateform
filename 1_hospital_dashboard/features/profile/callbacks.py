from dash import Input, Output
from features.profile.charts import profile_bar_chart
from utils.metrics import profile_kpis

def register_profile_callbacks(app, df):
    @app.callback(
        Output("profile-graph", "figure"),
        Input("filter-department", "value"),
        Input("filter-pathology", "value"),
        Input("filter-age", "value"),
        Input("filter-sex", "value"),
        Input("profile-metric-selector", "value")
    )
    def update_profile_chart(dept, patho, age, sex, metric):
        dff = df.copy()
        
        if dept and len(dept) > 0:
            dff = dff[dff["Departement"].isin(dept)]
        if patho and len(patho) > 0:
            dff = dff[dff["Maladie"].isin(patho)]
        if age and len(age) > 0:
            dff = dff[dff["AgeGroup"].isin(age)]
        if sex and len(sex) > 0:
            dff = dff[dff["Sexe"].isin(sex)]
        
        return profile_bar_chart(dff, profile_kpis, metric=metric)
