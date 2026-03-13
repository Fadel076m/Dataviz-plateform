"""
dashboard/utils/data.py
Chargement des données enrichies depuis MongoDB PROD pour le dashboard.
- Charge depuis banque_prod.performances_bancaires_prod en priorité
- Fallback sur banque_dev si PROD indisponible
- Harmonise les colonnes (NB_AGENCES, Groupe, RESULTAT.NET)
- Pas de simulation : les données sont supposées propres depuis le pipeline ETL
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from config.database import MongoDBConnection


def load_data() -> pd.DataFrame:
    """
    Charge les données enrichies depuis la collection PROD.
    Essaie d'abord banque_prod (PROD), puis banque_dev (DEV) en fallback.
    """
    df = _try_load(environment='prod')
    if df is None or df.empty:
        print("[DATA] PROD indisponible — chargement depuis DEV")
        df = _try_load(environment='dev')

    if df is None or df.empty:
        print("[DATA] ❌ Aucune donnée disponible")
        return pd.DataFrame()

    return _clean_for_dashboard(df)


def _try_load(environment: str) -> pd.DataFrame | None:
    """Tente de charger depuis MongoDB (env donné). Retourne None si échec."""
    try:
        mongo = MongoDBConnection(environment=environment)
        if not mongo.connect():
            return None

        collection = mongo.get_collection('performances_bancaires_prod')
        cursor = collection.find({})
        df = pd.DataFrame(list(cursor))
        mongo.close()

        if df.empty:
            return None

        print(f"[DATA] ✅ {len(df)} lignes chargées depuis {environment.upper()}")
        return df

    except Exception as e:
        print(f"[DATA] Erreur chargement {environment} : {e}")
        return None


def _clean_for_dashboard(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoie et harmonise le DataFrame pour le dashboard."""

    # Supprimer les colonnes MongoDB
    mongo_cols = [c for c in df.columns if c.startswith('_')]
    df = df.drop(columns=mongo_cols, errors='ignore')
    if '_id' in df.columns:
        df = df.drop('_id', axis=1)

    # 1. Forcer les scalaires (éviter les listes dans les cellules MongoDB)
    for col in df.columns:
        mask = df[col].apply(lambda x: isinstance(x, (list, tuple)))
        if mask.any():
            df.loc[mask, col] = df.loc[mask, col].apply(
                lambda x: x[0] if len(x) > 0 else None
            )

    # 2. Colonnes numériques clés
    numeric_cols = [
        'BILAN', 'RESSOURCES', 'FONDS.PROPRE', 'RESULTAT.NET',
        'EMPLOI', 'PRODUIT.NET.BANCAIRE',
        'R_SOLVABILITE', 'R_ROE', 'R_ROA', 'R_LEVIER', 'R_COEFF_EXPLOITATION',
        'ANNEE', 'EFFECTIF', 'NB_AGENCES', 'NB_COMPTES',
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # 3. Harmoniser NB_AGENCES (compatibilité avec ancienne colonne AGENCE)
    if 'NB_AGENCES' not in df.columns or df['NB_AGENCES'].isna().all():
        if 'AGENCE' in df.columns:
            df['NB_AGENCES'] = pd.to_numeric(df['AGENCE'], errors='coerce')
        else:
            df['NB_AGENCES'] = None

    # 4. Textes identifiants
    for col in ['Sigle', 'Groupe', 'Type']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({'nan': 'Inconnu', '': 'Inconnu'})

    # 5. Groupe : fallback sur Goupe_Bancaire si absent
    if 'Groupe' not in df.columns or (df['Groupe'] == 'Inconnu').all():
        if 'Goupe_Bancaire' in df.columns:
            df['Groupe'] = df['Goupe_Bancaire'].fillna('Inconnu')
        else:
            df['Groupe'] = 'Inconnu'

    # 6. Remplir les NaN numériques par 0 pour les colonnes financières
    for col in ['BILAN', 'RESSOURCES', 'FONDS.PROPRE', 'RESULTAT.NET',
                'R_SOLVABILITE', 'R_ROE', 'R_LEVIER', 'ANNEE']:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    # 7. ANNEE en entier
    if 'ANNEE' in df.columns:
        df['ANNEE'] = df['ANNEE'].astype(int)

    return df
