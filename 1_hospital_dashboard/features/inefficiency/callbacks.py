from dash import Input, Output
from features.inefficiency.charts import scatter_inefficiencies

def register_inefficiency_callbacks(app, df):
    @app.callback(
        Output("inefficiency-graph", "figure"),
        Input("filter-department", "value"),
        Input("filter-pathology", "value"),
        Input("filter-age", "value"),
        Input("filter-sex", "value")
    )
    def update_inefficiency_chart(dept, patho, age, sex):
        dff = df.copy()
        
        if dept and len(dept) > 0:
            dff = dff[dff["Departement"].isin(dept)]
        if patho and len(patho) > 0:
            dff = dff[dff["Maladie"].isin(patho)]
        if age and len(age) > 0:
            dff = dff[dff["AgeGroup"].isin(age)]
        if sex and len(sex) > 0:
            dff = dff[dff["Sexe"].isin(sex)]
        
        return scatter_inefficiencies(dff)
