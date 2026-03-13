# data_loader.py
import pandas as pd
import os

def load_data(filename="hospital_data.csv"):
    """
    Charge les données depuis le fichier CSV
    """
    # Essayer différents chemins
    possible_paths = [
        filename,  # Chemin relatif
        os.path.join(os.path.dirname(__file__), filename),  # Même dossier que data_loader.py
        os.path.join("hospital_dashboard", filename),  # Dossier hospital_dashboard
    ]
    
    df = None
    for path in possible_paths:
        try:
            print(f"🔍 Tentative de chargement depuis: {path}")
            df = pd.read_csv(path)
            print(f"✅ Fichier chargé avec succès: {path}")
            print(f"   Dimensions: {df.shape[0]} lignes × {df.shape[1]} colonnes")
            break
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"❌ Erreur avec {path}: {e}")
            continue
    
    if df is None:
        raise FileNotFoundError(
            f"Impossible de trouver le fichier {filename}. "
            f"Vérifiez qu'il se trouve dans: {possible_paths}"
        )
    
    # Création de la colonne AgeGroup si elle n'existe pas
    if "AgeGroup" not in df.columns and "Age" in df.columns:
        bins = [0, 18, 35, 50, 65, 120]
        labels = ["0-18", "19-35", "36-50", "51-65", "65+"]
        df["AgeGroup"] = pd.cut(df["Age"], bins=bins, labels=labels, right=False)

    return df