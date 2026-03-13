"""
Étape 6 : Enrichissement des Données (Silver → Gold)
- Charge depuis 'performances_bancaires_clean' (DEV)
- Ajoute Groupe, Type, Coordonnées GPS depuis BANK_METADATA
- Calcule les ratios financiers (Solvabilité, ROE, ROA, Levier, Coeff. Exploitation)
- Harmonise les noms de colonnes (AGENCE → NB_AGENCES, etc.)
- Promotion finale DEV → PROD : sauvegarde dans banque_PROD.performances_bancaires_prod
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.database import MongoDBConnection

# ==============================================================================
# 1. Métadonnées de référence — Banques du Sénégal (27-28 établissements)
# ==============================================================================
# Siège social approximatif à Dakar (coordonnées GPS)
BANK_METADATA = {
    # Groupes Continentaux (Afrique)
    "CBAO":      {"Groupe": "Attijariwafa Bank (Maroc)",           "Type": "Régional",       "Lat": 14.6712, "Lon": -17.4300},
    "BAS":       {"Groupe": "Attijariwafa Bank (Maroc)",           "Type": "Régional",       "Lat": 14.6710, "Lon": -17.4310},
    "BOA":       {"Groupe": "Bank of Africa (Maroc)",              "Type": "Régional",       "Lat": 14.6720, "Lon": -17.4400},
    "ECOBANK":   {"Groupe": "Ecobank Transnational (Togo)",        "Type": "Régional",       "Lat": 14.6730, "Lon": -17.4350},
    "UBA":       {"Groupe": "UBA Group (Nigeria)",                  "Type": "Régional",       "Lat": 14.6740, "Lon": -17.4360},
    "ORABANK":   {"Groupe": "Oragroup (Togo)",                      "Type": "Régional",       "Lat": 14.6725, "Lon": -17.4330},
    "CBI":       {"Groupe": "Coris Bank International (Burkina)",  "Type": "Régional",       "Lat": 14.6745, "Lon": -17.4370},
    "FBNBANK":   {"Groupe": "First Bank of Nigeria",               "Type": "Régional",       "Lat": 14.6735, "Lon": -17.4355},
    "BGFI":      {"Groupe": "BGFI Bank (Gabon)",                   "Type": "Régional",       "Lat": 14.6850, "Lon": -17.4550},
    "BSIC":      {"Groupe": "BSIC Group (Libye)",                  "Type": "Régional",       "Lat": 14.6715, "Lon": -17.4315},
    "BCIM":      {"Groupe": "BCIM Group",                          "Type": "Régional",       "Lat": 14.6700, "Lon": -17.4300},
    "NSIA":      {"Groupe": "NSIA Banque (Côte d'Ivoire)",         "Type": "Régional",       "Lat": 14.6760, "Lon": -17.4340},
    "LBO":       {"Groupe": "Banque Libyano-Emiratie",             "Type": "Régional",       "Lat": 14.6720, "Lon": -17.4320},
    # Groupes Internationaux (hors Afrique)
    "SGBS":      {"Groupe": "Société Générale (France)",           "Type": "International",  "Lat": 14.6698, "Lon": -17.4320},
    "BICIS":     {"Groupe": "Groupe SUNU (Régional)",              "Type": "International",  "Lat": 14.6705, "Lon": -17.4310},
    "CITIBANK":  {"Groupe": "Citigroup (USA)",                      "Type": "International",  "Lat": 14.6680, "Lon": -17.4280},
    # Groupes Régionaux / Locaux sénégalais
    "BIS":       {"Groupe": "Banque Islamique du Sénégal",         "Type": "National Islamique", "Lat": 14.6750, "Lon": -17.4380},
    "BHS":       {"Groupe": "Banque de l'Habitat du Sénégal",      "Type": "National",       "Lat": 14.6800, "Lon": -17.4500},
    "LBA":       {"Groupe": "La Banque Agricole du Sénégal",       "Type": "National",       "Lat": 14.6780, "Lon": -17.4450},
    "BNDE":      {"Groupe": "Banque Nat. pour le Dev. Éco.",       "Type": "National",       "Lat": 14.6900, "Lon": -17.4600},
    "BDK":       {"Groupe": "Banque de Kédougou",                  "Type": "National",       "Lat": 14.6950, "Lon": -17.4650},
    "CDS":       {"Groupe": "Crédit du Sénégal",                   "Type": "National",       "Lat": 14.6710, "Lon": -17.4310},
    "CISA":      {"Groupe": "CISA Sénégal",                        "Type": "National",       "Lat": 14.6700, "Lon": -17.4300},
    "BRM":       {"Groupe": "Banque Régionale de Marchés",         "Type": "National",       "Lat": 14.6770, "Lon": -17.4420},
    "BOP":       {"Groupe": "Banque de l'OMOA",                    "Type": "National",       "Lat": 14.6710, "Lon": -17.4310},
    "BOS":       {"Groupe": "Banque de l'Ouest et du Sud",         "Type": "National",       "Lat": 14.6720, "Lon": -17.4320},
    "BIMAO":     {"Groupe": "BIMAO Sénégal",                       "Type": "National Islamique", "Lat": 14.6725, "Lon": -17.4325},
    "CMB":       {"Groupe": "Crédit Mutuel du Sénégal",            "Type": "National",       "Lat": 14.6735, "Lon": -17.4335},
    # Établissements spécialisés / Financiers
    "LOCAFRIQUE":{"Groupe": "Locafrique (Leasing)",                 "Type": "Spécialisé",    "Lat": 14.6800, "Lon": -17.4400},
    "ALIOS":     {"Groupe": "Alios Finance",                       "Type": "Spécialisé",    "Lat": 14.6810, "Lon": -17.4410},
    "COFINA":    {"Groupe": "Cofina Group",                        "Type": "Inclusion Financière", "Lat": 14.6820, "Lon": -17.4420},
    "FINAO":     {"Groupe": "La Finao",                            "Type": "Spécialisé",    "Lat": 14.6830, "Lon": -17.4430},
    "DSB":       {"Groupe": "Diamond Bank Sénégal",                "Type": "Régional",       "Lat": 14.6745, "Lon": -17.4375},
    "ACCESS":    {"Groupe": "Access Bank (Nigeria)",               "Type": "Régional",       "Lat": 14.6745, "Lon": -17.4375},
    # Alias pour NSIA (harmonisation)
    "NSIA Banque": {"Groupe": "NSIA Banque (Côte d'Ivoire)",       "Type": "Régional",       "Lat": 14.6760, "Lon": -17.4340},
}

DEFAULT_METADATA = {"Groupe": "Non Classifié", "Type": "Autre", "Lat": 14.6928, "Lon": -17.4467}

# Groupe simplifié pour les graphiques (se base sur le champ Goupe_Bancaire du CSV)
GOUPE_BANCAIRE_TO_GROUPE = {
    "Groupes Continentaux":   "Groupes Continentaux",
    "Groupes Internationaux": "Groupes Internationaux",
    "Groupes Règionaux":      "Groupes Régionaux",
    "Groupes Regionaux":      "Groupes Régionaux",
    "Groupes Locaux":         "Groupes Locaux",
}


# ==============================================================================
# 2. Classe d'enrichissement
# ==============================================================================

class DataEnricher:
    """Enrichit les données propres et les promeut vers PROD."""

    def __init__(self):
        self.mongo_dev  = MongoDBConnection(environment='dev')
        self.mongo_prod = MongoDBConnection(environment='prod')

    # ── Chargement depuis DEV ─────────────────────────────────────────────────

    def load_clean_data(self):
        print("\n" + "="*60)
        print("📥 CHARGEMENT DEPUIS 'performances_bancaires_clean' (DEV)")
        print("="*60)

        if not self.mongo_dev.connect():
            print("❌ Connexion DEV échouée")
            return None

        coll = self.mongo_dev.get_collection('performances_bancaires_clean')
        df   = pd.DataFrame(list(coll.find({})))
        self.mongo_dev.close()

        if df.empty:
            print("❌ Aucune donnée — exécutez d'abord cleaning.py")
            return None

        if '_id' in df.columns:
            df = df.drop('_id', axis=1)

        print(f"[OK] {len(df)} documents chargés ({df['Sigle'].nunique()} banques)")
        return df

    # ── Métadonnées bancaires ─────────────────────────────────────────────────

    def add_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        print("\n🌍 Enrichissement avec métadonnées (Groupe, Type, GPS)...")

        df['Groupe']    = None
        df['Type']      = None
        df['Latitude']  = None
        df['Longitude'] = None

        # Harmoniser le sigle NSIA (variantes)
        if 'Sigle' in df.columns:
            df['Sigle'] = df['Sigle'].replace({"NSIA Banque": "NSIA"})

        for idx, row in df.iterrows():
            sigle = str(row.get('Sigle', ''))
            meta  = BANK_METADATA.get(sigle, DEFAULT_METADATA)
            df.at[idx, 'Groupe']    = meta['Groupe']
            df.at[idx, 'Type']      = meta['Type']
            df.at[idx, 'Latitude']  = meta['Lat']
            df.at[idx, 'Longitude'] = meta['Lon']

        # Utiliser Goupe_Bancaire du CSV si Groupe non trouvé
        if 'Goupe_Bancaire' in df.columns:
            mask_nc = df['Groupe'] == 'Non Classifié'
            df.loc[mask_nc, 'Groupe'] = df.loc[mask_nc, 'Goupe_Bancaire'].map(
                GOUPE_BANCAIRE_TO_GROUPE
            ).fillna(df.loc[mask_nc, 'Goupe_Bancaire'])

        non_classes = df[df['Groupe'] == 'Non Classifié']['Sigle'].unique()
        if len(non_classes) > 0:
            print(f"   ⚠️  Non classifiés : {list(non_classes)}")
        print(f"   ✅ Métadonnées ajoutées")
        return df

    # ── Harmonisation des colonnes ────────────────────────────────────────────

    def harmonize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Harmonise les noms de colonnes pour le dashboard."""
        # AGENCE → NB_AGENCES (pour compatibilité dashboard)
        if 'AGENCE' in df.columns and 'NB_AGENCES' not in df.columns:
            df = df.rename(columns={'AGENCE': 'NB_AGENCES'})
        elif 'AGENCE' in df.columns and 'NB_AGENCES' in df.columns:
            df['NB_AGENCES'] = df['NB_AGENCES'].fillna(df['AGENCE'])
            df = df.drop(columns=['AGENCE'])

        # COMPTE → NB_COMPTES (lisibilité)
        if 'COMPTE' in df.columns and 'NB_COMPTES' not in df.columns:
            df = df.rename(columns={'COMPTE': 'NB_COMPTES'})

        # S'assurer que RESULTAT.NET est bien présent (alias)
        if 'RESULTAT.NET' not in df.columns and 'RESULTAT NET' in df.columns:
            df = df.rename(columns={'RESULTAT NET': 'RESULTAT.NET'})

        print("   ✅ Colonnes harmonisées (AGENCE→NB_AGENCES, COMPTE→NB_COMPTES)")
        return df

    # ── Calcul des ratios ─────────────────────────────────────────────────────

    def calculate_ratios(self, df: pd.DataFrame) -> pd.DataFrame:
        print("\n🧮 Calcul des Ratios Financiers...")

        # Alias PNB
        if 'PNB' in df.columns and 'PRODUIT.NET.BANCAIRE' not in df.columns:
            df = df.rename(columns={'PNB': 'PRODUIT.NET.BANCAIRE'})
        elif 'PNB' in df.columns and 'PRODUIT.NET.BANCAIRE' in df.columns:
            df['PRODUIT.NET.BANCAIRE'] = df['PRODUIT.NET.BANCAIRE'].fillna(df['PNB'])
            df = df.drop(columns=['PNB'])

        # Forcer numériques sur colonnes clés
        num_cols = ['BILAN', 'FONDS.PROPRE', 'RESSOURCES', 'EMPLOI',
                    'RESULTAT.NET', 'PRODUIT.NET.BANCAIRE']
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0.0

        # 1. SOLVABILITÉ (Bâle) = Fonds Propres / Bilan × 100
        df['R_SOLVABILITE'] = (df['FONDS.PROPRE'] / df['BILAN'].replace(0, np.nan)) * 100

        # 2. ROE = Résultat Net / Fonds Propres × 100
        df['R_ROE'] = (df['RESULTAT.NET'] / df['FONDS.PROPRE'].replace(0, np.nan)) * 100

        # 3. ROA = Résultat Net / Bilan × 100
        df['R_ROA'] = (df['RESULTAT.NET'] / df['BILAN'].replace(0, np.nan)) * 100

        # 4. LEVIER = Fonds Propres / Ressources × 100
        df['R_LEVIER'] = (df['FONDS.PROPRE'] / df['RESSOURCES'].replace(0, np.nan)) * 100

        # 5. COEFFICIENT D'EXPLOITATION = Charges Générales / PNB × 100
        charges_col = "CHARGES.GENERALES.D'EXPLOITATION"
        if charges_col in df.columns:
            df[charges_col] = pd.to_numeric(df[charges_col], errors='coerce').fillna(0)
            df['R_COEFF_EXPLOITATION'] = (
                df[charges_col] / df['PRODUIT.NET.BANCAIRE'].replace(0, np.nan)
            ) * 100
        else:
            df['R_COEFF_EXPLOITATION'] = None

        # Nettoyage des infinis / NaN dans les ratios
        ratio_cols = [c for c in df.columns if c.startswith('R_')]
        df[ratio_cols] = df[ratio_cols].replace([np.inf, -np.inf], None).round(2)

        print(f"   ✅ {len(ratio_cols)} ratios calculés : {ratio_cols}")
        return df

    # ── Promotion DEV → PROD ──────────────────────────────────────────────────

    def save_to_prod(self, df: pd.DataFrame):
        """
        Sauvegarde les données enrichies dans la BASE PROD
        (collection 'performances_bancaires_prod').
        """
        print("\n" + "="*60)
        print("🚀 PROMOTION DEV → PROD")
        print("="*60)
        print(f"   Banques : {df['Sigle'].nunique()}")
        print(f"   Lignes  : {len(df)}")
        print(f"   Années  : {sorted(df['ANNEE'].dropna().astype(int).unique())}")

        if not self.mongo_prod.connect():
            print("❌ Connexion PROD échouée — vérifiez DB_PROD dans .env")
            # Fallback : sauvegarder dans DEV si PROD indisponible
            print("   [WARN] Fallback : sauvegarde dans DEV.performances_bancaires_prod")
            self._save_records(df, self.mongo_dev, 'performances_bancaires_prod')
            return

        self._save_records(df, self.mongo_prod, 'performances_bancaires_prod')

    def _save_records(self, df: pd.DataFrame, mongo: MongoDBConnection, coll_name: str):
        """Sauvegarde générique dans une collection MongoDB."""
        if not mongo.connect():
            print(f"❌ Connexion échouée pour {coll_name}")
            return

        records = []
        for _, row in df.iterrows():
            record = {}
            for col in df.columns:
                val = row[col]
                if pd.isna(val):
                    record[col] = None
                elif hasattr(val, 'item'): 
                    record[col] = val.item()
                elif isinstance(val, (pd.Timestamp,)):
                    record[col] = val.to_pydatetime()
                else:
                    record[col] = val
            record['_last_updated'] = datetime.utcnow()
            record['_app_version']  = "2.0"
            records.append(record)

        try:
            db   = mongo.client[mongo.db_name]
            coll = db[coll_name]
            coll.delete_many({})
            result = coll.insert_many(records)

            # Index
            coll.create_index([("Sigle", 1), ("ANNEE", 1)])
            coll.create_index([("Sigle", 1)])
            coll.create_index([("ANNEE", 1)])
            coll.create_index([("Groupe", 1)])

            print(f"[OK] {len(result.inserted_ids)} documents insérés dans '{mongo.db_name}.{coll_name}'")
        except Exception as e:
            print(f"❌ Erreur sauvegarde : {e}")
            import traceback; traceback.print_exc()
        finally:
            mongo.close()

    # ── Run ───────────────────────────────────────────────────────────────────

    def run(self):
        print("="*60)
        print("🚀 ENRICHISSEMENT DES DONNÉES — ÉTAPE 6 (Silver → Gold)")
        print("="*60)

        # 1. Charger depuis DEV (Silver)
        df = self.load_clean_data()
        if df is None:
            return

        # 2. Enrichir (Classification & Géo)
        df = self.add_metadata(df)

        # 3. Harmoniser les colonnes
        df = self.harmonize_columns(df)

        # 4. Calculer KPIs (Ratios)
        df = self.calculate_ratios(df)

        # 5. Sauvegarder en PROD (Gold)
        if self.save_to_prod(df):
            print("\n" + "="*60)
            print("[OK] PIPELINE COMPLET — Données disponibles dans PROD")
            print("   -> Lancez le dashboard : python dashboard/app.py")
            print("="*60)


if __name__ == "__main__":
    DataEnricher().run()
