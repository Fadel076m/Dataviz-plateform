# data_loader.py
import pandas as pd
import os

def clean_data(df):
    """
    Nettoie et prépare les données
    """
    df = df.copy()
    
    # Conversion des dates si les colonnes existent
    date_columns = ["DateAdmission", "DateSortie"]
    for col in date_columns:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
            except:
                print(f"⚠️ Impossible de convertir {col} en date")
    
    # Création de tranches d'âge
    if "Age" in df.columns:
        df["AgeGroup"] = pd.cut(
            df["Age"],
            bins=[0, 18, 35, 60, 120],
            labels=["0-18", "19-35", "36-60", "60+"]
        )
    
    # Création du coût par jour
    if "Cout" in df.columns and "DureeSejour" in df.columns:
        df["CostPerDay"] = df["Cout"] / df["DureeSejour"]
    
    print(f"📊 Données nettoyées: {df.shape[0]} patients, {df['Maladie'].nunique()} pathologies")
    return df
