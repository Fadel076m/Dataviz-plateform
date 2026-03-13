"""
Script d'ingestion des données historiques CSV vers MongoDB Atlas
Étape 1 : Import du fichier base_senegal.csv
- Validation stricte du schéma (30 colonnes de référence)
- Filtre sur les années ≤ 2020 (2021+ provient des PDF BCEAO)
- Tag _source='csv_historique' pour chaque enregistrement
Projet BCEAO - Data Engineering
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))
from config.database import MongoDBConnection

# ── Schéma de référence — EXACTEMENT les colonnes du CSV ──────────────────────
# (dans l'ordre du fichier)
SCHEMA_COLONNES = [
    "Sigle", "Goupe_Bancaire", "ANNEE",
    "EMPLOI", "BILAN", "RESSOURCES", "FONDS.PROPRE",
    "EFFECTIF", "AGENCE", "COMPTE",
    "INTERETS.ET.PRODUITS.ASSIMILES",
    "NTERETS.ET.CHARGES.ASSIMILEES",
    "REVENUS.DES.TITRES.A.REVENU.VARIABLE",
    "COMMISSIONS.(PRODUITS)", "COMMISSIONS.(CHARGES)",
    "GAINS.OU.PERTES.NETS.SUR.OPERATIONS.DES.PORTEFEUILLES.DE.NEGOCIATION",
    "GAINS.OU.PERTES.NETS.SUR.OPERATIONS.DES.PORTEFEUILLES.DE.PLACEMENT.ET.ASSIMILES",
    "AUTRES.PRODUITS.D'EXPLOITATION.BANCAIRE",
    "AUTRES.CHARGES.D'EXPLOITATION.BANCAIRE",
    "PRODUIT.NET.BANCAIRE",
    "SUBVENTIONS.D'INVESTISSEMENT",
    "CHARGES.GENERALES.D'EXPLOITATION",
    "DOTATIONS.AUX.AMORTISSEMENTS.ET.AUX.DEPRECIATIONS.DES.IMMOBILISATIONS.INCORPORELLES.ET.CORPORELLES",
    "RESULTAT.BRUT.D'EXPLOITATION",
    "COÛT.DU.RISQUE",
    "RESULTAT.D'EXPLOITATION",
    "GAINS.OU.PERTES.NETS.SUR.ACTIFS.IMMOBILISES",
    "RESULTAT.AVANT.IMPÔT",
    "IMPÔTS.SUR.LES.BENEFICES",
    "RESULTAT.NET",
]

# Colonnes numériques à convertir
NUMERIC_COLS = [c for c in SCHEMA_COLONNES if c not in ("Sigle", "Goupe_Bancaire")]

# Année max pour le CSV (les PDF couvrent 2021-2023)
ANNEE_MAX_CSV = 2020


class ExcelToMongoDB:
    """Importe les données CSV historiques vers MongoDB avec validation de schéma."""

    def __init__(self, csv_path, environment='dev'):
        self.csv_path = csv_path
        self.environment = environment
        self.mongo = MongoDBConnection(environment=environment)
        self.df = None

    # ── Chargement ────────────────────────────────────────────────────────────

    def load_csv(self):
        print("\n" + "=" * 80)
        print("📂 CHARGEMENT DU FICHIER CSV")
        print("=" * 80)

        if not os.path.exists(self.csv_path):
            print(f"❌ Fichier introuvable : {self.csv_path}")
            return False

        # Détection automatique du délimiteur
        for sep in [';', ',', '\t']:
            try:
                df = pd.read_csv(self.csv_path, sep=sep, encoding='utf-8', dtype=str)
                if len(df.columns) > 5:
                    self.df = df
                    print(f"[OK] CSV chargé avec délimiteur '{sep}' | {len(df)} lignes | {len(df.columns)} colonnes")
                    break
            except Exception:
                continue

        if self.df is None:
            print("❌ Impossible de lire le fichier CSV")
            return False
        return True

    # ── Validation du schéma ──────────────────────────────────────────────────

    def validate_schema(self):
        """Vérifie que les colonnes attendues sont présentes."""
        print("\n🔍 VALIDATION DU SCHÉMA (30 colonnes référence)")
        cols_csv = list(self.df.columns)
        manquantes = [c for c in SCHEMA_COLONNES if c not in cols_csv]
        superflues = [c for c in cols_csv if c not in SCHEMA_COLONNES]

        if manquantes:
            print(f"   [WARN] Colonnes manquantes ({len(manquantes)}) : {manquantes}")
            # Ajouter les colonnes manquantes avec None pour rester cohérent
            for col in manquantes:
                self.df[col] = None
        else:
            print(f"   [OK] Toutes les {len(SCHEMA_COLONNES)} colonnes de référence sont présentes")

        if superflues:
            print(f"   ℹ️  Colonnes supplémentaires ignorées : {superflues}")

        # Garder uniquement les colonnes du schéma
        self.df = self.df[[c for c in SCHEMA_COLONNES if c in self.df.columns]]
        return True

    # ── Nettoyage & types ─────────────────────────────────────────────────────

    def clean_data(self):
        """Nettoie et type les données."""
        print("\n🧹 NETTOYAGE DES DONNÉES")

        n_avant = len(self.df)

        # Supprimer lignes complètement vides
        self.df = self.df.dropna(how='all')

        # Normaliser les identifiants textes
        for col in ['Sigle', 'Goupe_Bancaire']:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(str).str.strip()
                self.df[col] = self.df[col].replace({'nan': None, 'NaN': None, '': None})

        # Convertir les colonnes numériques
        for col in NUMERIC_COLS:
            if col in self.df.columns:
                # Remplacer les tirets et valeurs vides par NaN
                self.df[col] = self.df[col].replace({'-': None, '–': None, '': None, 'nan': None})
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

        # Filtre : garder seulement les années ≤ 2020
        if 'ANNEE' in self.df.columns:
            n_avant_filtre = len(self.df)
            self.df = self.df[self.df['ANNEE'] <= ANNEE_MAX_CSV]
            n_filtre = n_avant_filtre - len(self.df)
            if n_filtre > 0:
                print(f"   ℹ️  {n_filtre} lignes de 2021+ ignorées (couvertes par les PDF BCEAO)")

        # Supprimer les doublons exacts
        doublons = self.df.duplicated(subset=['Sigle', 'ANNEE']).sum()
        if doublons > 0:
            print(f"   ⚠️  {doublons} doublons (Sigle, ANNEE) supprimés")
            self.df = self.df.drop_duplicates(subset=['Sigle', 'ANNEE'], keep='last')

        n_apres = len(self.df)
        print(f"   [OK] Nettoyage terminé : {n_avant} → {n_apres} lignes")
        print(f"   🏦 Banques distinctes : {self.df['Sigle'].nunique()}")
        print(f"   📅 Années : {sorted(self.df['ANNEE'].dropna().astype(int).unique())}")
        return True

    # ── Import MongoDB ────────────────────────────────────────────────────────

    def import_to_mongodb(self, clear_collection=True):
        """Importe le DataFrame dans la collection MongoDB de base (Bronze)."""
        print("\n⬆️  IMPORTATION DANS MONGODB")

        if not self.mongo.connect():
            return False

        try:
            collection = self.mongo.get_collection()

            if clear_collection:
                # Supprimer uniquement les docs CSV (pas les PDF déjà présents)
                result = collection.delete_many({"_source": "csv_historique"})
                print(f"   [CLEAN] {result.deleted_count} anciens documents CSV supprimés")

            records = []
            for _, row in self.df.iterrows():
                record = {}
                for col in self.df.columns:
                    val = row[col]
                    if pd.isna(val):
                        record[col] = None
                    elif isinstance(val, (np.int64, np.int32)):
                        record[col] = int(val)
                    elif isinstance(val, (np.float64, np.float32)):
                        record[col] = float(val)
                    else:
                        record[col] = val

                # Métadonnées de traçabilité
                record['_source'] = 'csv_historique'
                record['_source_file'] = Path(self.csv_path).name
                record['_import_date'] = datetime.utcnow()
                records.append(record)

            result = collection.insert_many(records)
            print(f"   [OK] {len(result.inserted_ids)} documents insérés")

            # Créer les index
            collection.create_index([("Sigle", 1), ("ANNEE", 1)])
            collection.create_index([("ANNEE", 1)])
            print("   🔍 Index (Sigle, ANNEE) créés")

            self.mongo.get_stats()
            return True

        except Exception as e:
            print(f"❌ Erreur lors de l'import : {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.mongo.close()

    # ── Run ───────────────────────────────────────────────────────────────────

    def run(self, clear_collection=True, preview=True):
        print("=" * 80)
        print("🚀 INGESTION CSV -> MONGODB ATLAS (Etape 1)")
        print("=" * 80)

        if not self.load_csv():
            return False
        if not self.validate_schema():
            return False
        if not self.clean_data():
            return False

        if preview:
            print("👀 Aperçu (5 premières lignes) :")
            print(self.df[['Sigle', 'Goupe_Bancaire', 'ANNEE', 'BILAN', 'RESULTAT.NET']].head().to_string())

        if not self.import_to_mongodb(clear_collection=clear_collection):
            return False

        print("\n" + "=" * 80)
        print(" [OK] INGESTION TERMINEE")
        print("   ▶  Prochaine étape : Étape 3 — OCR des rapports PDF BCEAO")
        print("=" * 80)
        return True


def main():
    # Chemin vers le CSV (depuis la racine du projet)
    root = Path(__file__).resolve().parent.parent
    csv_path = root / "data" / "base_senegal.csv"

    importer = ExcelToMongoDB(
        csv_path=str(csv_path),
        environment='dev'
    )
    importer.run(clear_collection=True, preview=True)


if __name__ == "__main__":
    main()
