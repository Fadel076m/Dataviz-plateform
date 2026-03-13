"""
data_processing.py — Module de traitement des données solaires
Chargement, nettoyage, calcul des KPIs et détection d'anomalies.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ──────────────────────────────────────────────
# 1. CHARGEMENT ET PRÉPARATION DES DONNÉES
# ──────────────────────────────────────────────

DATA_PATH = Path(__file__).parent.parent / "data" / "salar_data.csv"


def load_data():
    """Charge et prépare le dataset solaire."""
    df = pd.read_csv(DATA_PATH, sep=";")

    # Parsing des dates
    df["DateTime"] = pd.to_datetime(df["DateTime"], format="%d/%m/%Y %H:%M")
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")

    # Métriques dérivées
    df["Efficiency"] = np.where(
        df["DC_Power"] > 0,
        (df["AC_Power"] / df["DC_Power"]) * 100,
        0.0,
    )
    df["Energy_Loss"] = df["DC_Power"] - df["AC_Power"]
    df["Loss_Rate"] = np.where(
        df["DC_Power"] > 0,
        (df["Energy_Loss"] / df["DC_Power"]) * 100,
        0.0,
    )
    df["Temp_Delta"] = df["Module_Temperature"] - df["Ambient_Temperature"]

    # Détection d'anomalies
    df["Anomaly_Type"] = detect_anomalies(df)
    df["Is_Anomaly"] = df["Anomaly_Type"] != "Normal"

    # Colonnes utilitaires
    df["Month_Name"] = df["DateTime"].dt.strftime("%b")
    df["Date_Str"] = df["Date"].dt.strftime("%Y-%m-%d")

    return df


# ──────────────────────────────────────────────
# 2. DÉTECTION D'ANOMALIES
# ──────────────────────────────────────────────

def detect_anomalies(df):
    """
    Détecte les anomalies selon 5 règles métier.
    Retourne une Series avec le type d'anomalie.
    """
    anomaly = pd.Series("Normal", index=df.index)

    # Règle 1 : Onduleur en panne — DC > 0 mais AC = 0
    mask_inverter = (df["DC_Power"] > 0) & (df["AC_Power"] == 0)
    anomaly[mask_inverter] = "🔴 Panne onduleur"

    # Règle 2 : Production nocturne (heures 22-4) avec AC > 0
    mask_night = (df["Hour"].isin([22, 23, 0, 1, 2, 3, 4])) & (df["AC_Power"] > 0)
    anomaly[mask_night] = "🟡 Production nocturne"

    # Règle 3 : Forte irradiation mais faible production
    mask_low_prod = (df["Irradiation"] > 0.5) & (df["AC_Power"] < 5)
    anomaly[mask_low_prod] = "🟠 Faible rendement"

    # Règle 4 : Surchauffe module (delta > 25°C)
    temp_delta = df["Module_Temperature"] - df["Ambient_Temperature"]
    mask_overheat = temp_delta > 25
    anomaly[mask_overheat] = "🟡 Surchauffe module"

    # Règle 5 : Rendement très faible sous charge
    efficiency = np.where(
        df["DC_Power"] > 0,
        (df["AC_Power"] / df["DC_Power"]) * 100,
        100.0,
    )
    mask_low_eff = (df["DC_Power"] > 10) & (efficiency < 70)
    anomaly[mask_low_eff] = "🔴 Rendement critique"

    return anomaly


# ──────────────────────────────────────────────
# 3. FILTRAGE DES DONNÉES
# ──────────────────────────────────────────────

def filter_data(df, countries=None, months=None, start_date=None, end_date=None):
    """Filtre le dataframe selon les critères sélectionnés."""
    filtered = df.copy()

    if countries and len(countries) > 0:
        filtered = filtered[filtered["Country"].isin(countries)]

    if months and len(months) > 0:
        filtered = filtered[filtered["Month"].isin(months)]

    if start_date:
        filtered = filtered[filtered["Date"] >= pd.to_datetime(start_date)]

    if end_date:
        filtered = filtered[filtered["Date"] <= pd.to_datetime(end_date)]

    return filtered


# ──────────────────────────────────────────────
# 4. CALCUL DES KPIs
# ──────────────────────────────────────────────

def compute_kpis(df):
    """Calcule les 8 KPIs stratégiques à partir du dataframe filtré."""
    total_ac = df["AC_Power"].sum()
    total_dc = df["DC_Power"].sum()
    n_rows = len(df)

    kpis = {
        # 1. Production totale (kWh)
        "total_production": round(total_ac, 1),

        # 2. Production moyenne horaire (kW)
        "avg_hourly_production": round(df["AC_Power"].mean(), 2),

        # 3. Rendement AC/DC (%)
        "ac_dc_efficiency": round(
            (total_ac / total_dc * 100) if total_dc > 0 else 0, 1
        ),

        # 4. Taux de perte énergétique (%)
        "loss_rate": round(
            ((total_dc - total_ac) / total_dc * 100) if total_dc > 0 else 0, 1
        ),

        # 5. Pic de production (kW)
        "peak_production": round(df["AC_Power"].max(), 2),

        # 6. Taux d'anomalies (%)
        "anomaly_rate": round(
            (df["Is_Anomaly"].sum() / n_rows * 100) if n_rows > 0 else 0, 2
        ),

        # 7. Facteur de capacité (%)
        "capacity_factor": round(
            (df["AC_Power"].mean() / df["AC_Power"].max() * 100)
            if df["AC_Power"].max() > 0
            else 0,
            1,
        ),

        # 8. Irradiation moyenne (kWh/m²)
        "avg_irradiation": round(df["Irradiation"].mean(), 3),
    }

    return kpis


# ──────────────────────────────────────────────
# 5. AGRÉGATIONS POUR GRAPHIQUES
# ──────────────────────────────────────────────

def hourly_profile(df):
    """Profil moyen horaire DC vs AC."""
    return df.groupby("Hour").agg(
        DC_Power=("DC_Power", "mean"),
        AC_Power=("AC_Power", "mean"),
        Irradiation=("Irradiation", "mean"),
    ).reset_index()


def daily_production(df):
    """Production journalière par pays."""
    return df.groupby(["Date_Str", "Country"]).agg(
        Daily_AC=("AC_Power", "sum"),
        Daily_DC=("DC_Power", "sum"),
        Daily_Yield=("Daily_Yield", "max"),
    ).reset_index()


def monthly_production(df):
    """Production mensuelle par pays."""
    return df.groupby(["Month", "Month_Name", "Country"]).agg(
        Total_AC=("AC_Power", "sum"),
        Total_DC=("DC_Power", "sum"),
        Avg_Irradiation=("Irradiation", "mean"),
        Avg_Temp=("Module_Temperature", "mean"),
    ).reset_index().sort_values("Month")


def heatmap_data(df):
    """Données pour heatmap Hour × Month → AC_Power."""
    pivot = df.pivot_table(
        values="AC_Power",
        index="Hour",
        columns="Month",
        aggfunc="mean",
    )
    return pivot


def anomaly_summary(df):
    """Résumé des anomalies détectées."""
    anomalies = df[df["Is_Anomaly"]].copy()
    if len(anomalies) == 0:
        return pd.DataFrame(columns=[
            "DateTime", "Country", "Anomaly_Type",
            "DC_Power", "AC_Power", "Irradiation", "Efficiency"
        ])
    return anomalies[[
        "DateTime", "Country", "Anomaly_Type",
        "DC_Power", "AC_Power", "Irradiation", "Efficiency"
    ]].sort_values("DateTime", ascending=False).head(200)


def country_distribution(df):
    """Répartition de la production par pays."""
    return df.groupby("Country").agg(
        Total_AC=("AC_Power", "sum"),
    ).reset_index()
