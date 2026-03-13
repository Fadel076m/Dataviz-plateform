# metrics.py
# KPI NIVEAU 1 — Vue stratégique

def global_kpis(df):
    return {
        "patients": df["PatientID"].nunique(),
        "avg_stay": round(df["DureeSejour"].mean(), 1),
        "median_stay": round(df["DureeSejour"].median(), 1),
        "avg_cost": round(df["Cout"].mean(), 2),
        "avg_cost_day": round(df["Cout"].sum() / df["DureeSejour"].sum(), 2),
        "total_cost": round(df["Cout"].sum(), 2)
    }


# KPI NIVEAU 2 — Par pathologie

def pathology_kpis(df):
    return (
        df.groupby("Maladie")
        .agg(
            avg_stay=("DureeSejour", "mean"),
            avg_cost=("Cout", "mean")
        )
        .reset_index()
    )


# KPI NIVEAU 2 — Par département

def department_kpis(df):
    return (
        df.groupby("Departement")
        .agg(
            avg_stay=("DureeSejour", "mean"),
            avg_cost=("Cout", "mean"),
            total_cost=("Cout", "sum"),
            cost_per_day=("Cout", lambda x: x.sum() / df.loc[x.index, "DureeSejour"].sum())
        )
        .reset_index()
    )

# KPI NIVEAU 3 — Profil patient
# CORRECTION ICI : ajoutez observed=False pour éviter le warning

def profile_kpis(df):
    return (
        df.groupby("AgeGroup", observed=False)  # <-- Ajout de observed=False
        .agg(
            avg_stay=("DureeSejour", "mean"),
            avg_cost=("Cout", "mean")
        )
        .reset_index()
    )

# KPI NIVEAU 4 — Inefficiences

def inefficiencies(df):
    return df[
        (df["DureeSejour"] > df["DureeSejour"].quantile(0.95)) |
        (df["Cout"] > df["Cout"].quantile(0.95))
    ]

def inefficiency_flags(df):
    df = df.copy()

    df["LongStay"] = df["DureeSejour"] > df["DureeSejour"].quantile(0.95)
    df["HighCost"] = df["Cout"] > df["Cout"].quantile(0.95)

    return df