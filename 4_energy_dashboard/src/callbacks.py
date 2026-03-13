"""
callbacks.py — Callbacks interactifs du Dashboard Solaire
Filtres → KPIs + Graphiques Plotly stylisés.
"""

from dash import Input, Output, State, html, callback, dash_table
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from . import data_processing as dp

# ──────────────────────────────────────────────
# PALETTE SOLAIRE
# ──────────────────────────────────────────────

COLORS = {
    "bg": "#0f0f23",
    "card": "#1a1a3e",
    "text": "#e0e0e0",
    "accent": "#FFB800",
    "accent2": "#FF6B35",
    "accent3": "#00D4AA",
    "dc": "#FFB800",
    "ac": "#FF6B35",
    "grid": "rgba(255,255,255,0.06)",
    "line_grid": "rgba(255,255,255,0.1)",
    "countries": {
        "Norway": "#4FC3F7",
        "Brazil": "#66BB6A",
        "India": "#FF7043",
        "Australia": "#FFD54F",
    },
}

MONTH_NAMES = [
    "Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
    "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"
]


def base_layout(title=""):
    """Layout Plotly de base – thème sombre."""
    return go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=COLORS["text"], size=12),
        margin=dict(l=50, r=30, t=40, b=50),
        title=dict(text=title, font=dict(size=14, color=COLORS["accent"])),
        xaxis=dict(gridcolor=COLORS["grid"], zeroline=False),
        yaxis=dict(gridcolor=COLORS["grid"], zeroline=False),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        hoverlabel=dict(
            bgcolor="#1a1a3e",
            font_size=12,
            font_family="Inter, sans-serif",
        ),
    )


# ──────────────────────────────────────────────
# DONNÉES GLOBALES
# ──────────────────────────────────────────────

DF = dp.load_data()


# ──────────────────────────────────────────────
# ENREGISTREMENT DES CALLBACKS
# ──────────────────────────────────────────────

def register_callbacks(app):
    """Enregistre tous les callbacks Dash."""

    @app.callback(
        # KPI outputs
        Output("kpi-total-prod", "children"),
        Output("kpi-avg-hourly", "children"),
        Output("kpi-efficiency", "children"),
        Output("kpi-loss-rate", "children"),
        Output("kpi-peak", "children"),
        Output("kpi-anomaly-rate", "children"),
        Output("kpi-capacity", "children"),
        Output("kpi-irradiation", "children"),
        # Graph outputs
        Output("chart-hourly-profile", "figure"),
        Output("chart-country-pie", "figure"),
        Output("chart-daily-production", "figure"),
        Output("chart-irr-vs-dc", "figure"),
        Output("chart-temp-vs-ac", "figure"),
        Output("chart-heatmap", "figure"),
        Output("chart-monthly-bar", "figure"),
        Output("chart-monthly-box", "figure"),
        Output("chart-anomaly-pie", "figure"),
        Output("chart-anomaly-timeline", "figure"),
        Output("anomaly-table-container", "children"),
        # Inputs
        Input("filter-country", "value"),
        Input("filter-month", "value"),
        Input("filter-daterange", "start_date"),
        Input("filter-daterange", "end_date"),
    )
    def update_dashboard(countries, months, start_date, end_date):
        # Filtrage
        filtered = dp.filter_data(DF, countries, months, start_date, end_date)

        if len(filtered) == 0:
            empty_fig = go.Figure(layout=base_layout())
            empty_fig.add_annotation(
                text="Aucune donnée pour les filtres sélectionnés",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=16, color=COLORS["text"]),
            )
            return (
                "—", "—", "—", "—", "—", "—", "—", "—",
                empty_fig, empty_fig, empty_fig, empty_fig,
                empty_fig, empty_fig, empty_fig, empty_fig,
                empty_fig, empty_fig,
                html.P("Aucune anomalie détectée", className="no-data"),
            )

        # KPIs
        kpis = dp.compute_kpis(filtered)

        # Formatage des valeurs KPI
        kpi_vals = [
            f"{kpis['total_production']:,.0f}",
            f"{kpis['avg_hourly_production']:.2f}",
            f"{kpis['ac_dc_efficiency']:.1f}%",
            f"{kpis['loss_rate']:.1f}%",
            f"{kpis['peak_production']:.1f}",
            f"{kpis['anomaly_rate']:.2f}%",
            f"{kpis['capacity_factor']:.1f}%",
            f"{kpis['avg_irradiation']:.3f}",
        ]

        # ── GRAPHIQUE 1 : Profil Horaire DC vs AC ──
        hourly = dp.hourly_profile(filtered)
        fig_hourly = go.Figure(layout=base_layout())
        fig_hourly.add_trace(go.Scatter(
            x=hourly["Hour"], y=hourly["DC_Power"],
            name="DC Power", mode="lines+markers",
            line=dict(color=COLORS["dc"], width=3),
            marker=dict(size=6),
            fill="tozeroy", fillcolor="rgba(255,184,0,0.1)",
        ))
        fig_hourly.add_trace(go.Scatter(
            x=hourly["Hour"], y=hourly["AC_Power"],
            name="AC Power", mode="lines+markers",
            line=dict(color=COLORS["ac"], width=3),
            marker=dict(size=6),
            fill="tozeroy", fillcolor="rgba(255,107,53,0.1)",
        ))
        fig_hourly.update_xaxes(title_text="Heure", dtick=2)
        fig_hourly.update_yaxes(title_text="Puissance moyenne (kW)")

        # ── GRAPHIQUE 2 : Répartition par pays (pie) ──
        country_dist = dp.country_distribution(filtered)
        fig_pie = go.Figure(layout=base_layout())
        fig_pie.add_trace(go.Pie(
            labels=country_dist["Country"],
            values=country_dist["Total_AC"],
            hole=0.55,
            marker=dict(
                colors=[COLORS["countries"].get(c, "#888") for c in country_dist["Country"]],
                line=dict(color=COLORS["bg"], width=2),
            ),
            textinfo="label+percent",
            textfont_size=12,
            hoverinfo="label+value+percent",
        ))
        fig_pie.update_layout(showlegend=False)

        # ── GRAPHIQUE 3 : Production journalière ──
        daily = dp.daily_production(filtered)
        fig_daily = go.Figure(layout=base_layout())
        for country in sorted(daily["Country"].unique()):
            cd = daily[daily["Country"] == country]
            fig_daily.add_trace(go.Bar(
                x=cd["Date_Str"], y=cd["Daily_AC"],
                name=country,
                marker_color=COLORS["countries"].get(country, "#888"),
                opacity=0.85,
            ))
        fig_daily.update_layout(barmode="stack", bargap=0.05)
        fig_daily.update_xaxes(title_text="Date", tickangle=-45, nticks=20)
        fig_daily.update_yaxes(title_text="Production AC (kW)")

        # ── GRAPHIQUE 4 : Irradiation vs DC ──
        sample = filtered[filtered["DC_Power"] > 0].sample(
            min(3000, len(filtered[filtered["DC_Power"] > 0])), random_state=42
        ) if len(filtered[filtered["DC_Power"] > 0]) > 0 else filtered
        fig_irr = go.Figure(layout=base_layout())
        for country in sorted(sample["Country"].unique()):
            cs = sample[sample["Country"] == country]
            fig_irr.add_trace(go.Scatter(
                x=cs["Irradiation"], y=cs["DC_Power"],
                name=country, mode="markers",
                marker=dict(
                    color=COLORS["countries"].get(country, "#888"),
                    size=5, opacity=0.6,
                ),
            ))
        # Trendline globale
        if len(sample) > 10:
            z = np.polyfit(sample["Irradiation"], sample["DC_Power"], 1)
            p = np.poly1d(z)
            x_trend = np.linspace(sample["Irradiation"].min(), sample["Irradiation"].max(), 100)
            fig_irr.add_trace(go.Scatter(
                x=x_trend, y=p(x_trend),
                name="Tendance", mode="lines",
                line=dict(color="white", width=2, dash="dash"),
            ))
        fig_irr.update_xaxes(title_text="Irradiation (kWh/m²)")
        fig_irr.update_yaxes(title_text="Puissance DC (kW)")

        # ── GRAPHIQUE 5 : Température vs AC ──
        fig_temp = go.Figure(layout=base_layout())
        sample_temp = filtered[filtered["AC_Power"] > 0]
        if len(sample_temp) > 3000:
            sample_temp = sample_temp.sample(3000, random_state=42)
        if len(sample_temp) > 0:
            fig_temp.add_trace(go.Scatter(
                x=sample_temp["Module_Temperature"],
                y=sample_temp["AC_Power"],
                mode="markers",
                marker=dict(
                    color=sample_temp["Irradiation"],
                    colorscale="YlOrRd",
                    size=5, opacity=0.6,
                    colorbar=dict(title="Irradiation", thickness=15),
                ),
                name="",
                showlegend=False,
            ))
        fig_temp.update_xaxes(title_text="Température Module (°C)")
        fig_temp.update_yaxes(title_text="Puissance AC (kW)")

        # ── GRAPHIQUE 6 : Heatmap Hour × Month ──
        heatmap = dp.heatmap_data(filtered)
        fig_heatmap = go.Figure(layout=base_layout())
        fig_heatmap.add_trace(go.Heatmap(
            z=heatmap.values,
            x=[MONTH_NAMES[m - 1] for m in heatmap.columns],
            y=heatmap.index,
            colorscale=[
                [0, "#0f0f23"],
                [0.2, "#1a1a5e"],
                [0.4, "#FF6B35"],
                [0.7, "#FFB800"],
                [1, "#FFEB3B"],
            ],
            colorbar=dict(title="kW moy.", thickness=15),
            hovertemplate="Mois: %{x}<br>Heure: %{y}h<br>AC moy: %{z:.1f} kW<extra></extra>",
        ))
        fig_heatmap.update_yaxes(title_text="Heure", dtick=2)
        fig_heatmap.update_xaxes(title_text="Mois")
        fig_heatmap.update_layout(height=450)

        # ── GRAPHIQUE 7 : Production mensuelle bar groupé ──
        monthly = dp.monthly_production(filtered)
        fig_monthly = go.Figure(layout=base_layout())
        for country in sorted(monthly["Country"].unique()):
            cm = monthly[monthly["Country"] == country]
            fig_monthly.add_trace(go.Bar(
                x=cm["Month_Name"], y=cm["Total_AC"],
                name=country,
                marker_color=COLORS["countries"].get(country, "#888"),
            ))
        fig_monthly.update_layout(barmode="group", bargap=0.15)
        fig_monthly.update_xaxes(title_text="Mois")
        fig_monthly.update_yaxes(title_text="Production AC totale (kW)")

        # ── GRAPHIQUE 8 : Box plot mensuel ──
        fig_box = go.Figure(layout=base_layout())
        ac_positive = filtered[filtered["AC_Power"] > 0]
        for month in sorted(ac_positive["Month"].unique()):
            month_data = ac_positive[ac_positive["Month"] == month]
            fig_box.add_trace(go.Box(
                y=month_data["AC_Power"],
                name=MONTH_NAMES[month - 1],
                marker_color=COLORS["accent"],
                line_color=COLORS["accent2"],
                boxpoints=False,
            ))
        fig_box.update_yaxes(title_text="Puissance AC (kW)")
        fig_box.update_layout(showlegend=False)

        # ── GRAPHIQUE 9 : Anomalies pie ──
        anomalies_df = filtered[filtered["Is_Anomaly"]]
        fig_anomaly_pie = go.Figure(layout=base_layout())
        if len(anomalies_df) > 0:
            anom_counts = anomalies_df["Anomaly_Type"].value_counts()
            anom_colors = {
                "🔴 Panne onduleur": "#EF5350",
                "🟡 Production nocturne": "#FFD54F",
                "🟠 Faible rendement": "#FF7043",
                "🟡 Surchauffe module": "#FFA726",
                "🔴 Rendement critique": "#E53935",
            }
            fig_anomaly_pie.add_trace(go.Pie(
                labels=anom_counts.index,
                values=anom_counts.values,
                hole=0.5,
                marker=dict(
                    colors=[anom_colors.get(t, "#888") for t in anom_counts.index],
                    line=dict(color=COLORS["bg"], width=2),
                ),
                textinfo="label+percent",
                textfont_size=11,
            ))
            fig_anomaly_pie.update_layout(showlegend=False)
        else:
            fig_anomaly_pie.add_annotation(
                text="✅ Aucune anomalie détectée",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=16, color=COLORS["accent3"]),
            )

        # ── GRAPHIQUE 10 : Timeline avec anomalies ──
        fig_anom_timeline = go.Figure(layout=base_layout())
        # Agrégation horaire pour alléger le graphique
        daily_agg = filtered.groupby("Date_Str").agg(
            AC_Power=("AC_Power", "mean"),
            Anomaly_Count=("Is_Anomaly", "sum"),
        ).reset_index()
        fig_anom_timeline.add_trace(go.Scatter(
            x=daily_agg["Date_Str"], y=daily_agg["AC_Power"],
            name="AC moy.", mode="lines",
            line=dict(color=COLORS["ac"], width=2),
        ))
        # Highlight anomalies
        anom_days = daily_agg[daily_agg["Anomaly_Count"] > 0]
        if len(anom_days) > 0:
            fig_anom_timeline.add_trace(go.Scatter(
                x=anom_days["Date_Str"], y=anom_days["AC_Power"],
                name="Jours avec anomalies", mode="markers",
                marker=dict(color="#EF5350", size=8, symbol="x"),
            ))
        fig_anom_timeline.update_xaxes(title_text="Date", nticks=15)
        fig_anom_timeline.update_yaxes(title_text="AC moy. (kW)")

        # ── TABLEAU ANOMALIES ──
        anom_table_data = dp.anomaly_summary(filtered)
        if len(anom_table_data) > 0:
            anom_table_data["DateTime"] = anom_table_data["DateTime"].dt.strftime(
                "%d/%m/%Y %H:%M"
            )
            anomaly_table = dash_table.DataTable(
                data=anom_table_data.round(2).to_dict("records"),
                columns=[
                    {"name": "Date/Heure", "id": "DateTime"},
                    {"name": "Pays", "id": "Country"},
                    {"name": "Type", "id": "Anomaly_Type"},
                    {"name": "DC (kW)", "id": "DC_Power"},
                    {"name": "AC (kW)", "id": "AC_Power"},
                    {"name": "Irradiation", "id": "Irradiation"},
                    {"name": "Rendement %", "id": "Efficiency"},
                ],
                page_size=10,
                sort_action="native",
                filter_action="native",
                style_table={"overflowX": "auto"},
                style_header={
                    "backgroundColor": "#1a1a3e",
                    "color": "#FFB800",
                    "fontWeight": "600",
                    "border": "1px solid rgba(255,255,255,0.1)",
                    "fontFamily": "Inter, sans-serif",
                    "fontSize": "13px",
                    "padding": "12px 16px",
                },
                style_cell={
                    "backgroundColor": "rgba(15,15,35,0.8)",
                    "color": "#e0e0e0",
                    "border": "1px solid rgba(255,255,255,0.06)",
                    "fontFamily": "Inter, sans-serif",
                    "fontSize": "12px",
                    "textAlign": "center",
                    "padding": "10px 14px",
                },
                style_data_conditional=[
                    {
                        "if": {"filter_query": '{Anomaly_Type} contains "🔴"'},
                        "backgroundColor": "rgba(229,57,53,0.15)",
                        "color": "#EF5350",
                    },
                    {
                        "if": {"filter_query": '{Anomaly_Type} contains "🟠"'},
                        "backgroundColor": "rgba(255,112,67,0.15)",
                        "color": "#FF7043",
                    },
                    {
                        "if": {"filter_query": '{Anomaly_Type} contains "🟡"'},
                        "backgroundColor": "rgba(255,213,79,0.1)",
                        "color": "#FFD54F",
                    },
                    {
                        "if": {"row_index": "odd"},
                        "backgroundColor": "rgba(26,26,62,0.5)",
                    },
                ],
                style_filter={
                    "backgroundColor": "#12122e",
                    "color": "#e0e0e0",
                    "border": "1px solid rgba(255,255,255,0.1)",
                },
            )
        else:
            anomaly_table = html.P(
                "✅ Aucune anomalie détectée pour la période sélectionnée.",
                className="no-data",
            )

        return (
            *kpi_vals,
            fig_hourly, fig_pie, fig_daily,
            fig_irr, fig_temp, fig_heatmap,
            fig_monthly, fig_box,
            fig_anomaly_pie, fig_anom_timeline,
            anomaly_table,
        )
