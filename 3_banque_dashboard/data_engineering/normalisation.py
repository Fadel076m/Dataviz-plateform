"""
Étape 4 : Normalisation et Fusion des Données
- Fusionne les données CSV historiques (2015-2020) avec les données PDF (2019-2023)
- Gère la double présence de 2021 avec fusion intelligente champ par champ :
    Priorité par source pour chaque champ :
    1. PDF 2021-2023  (rapport le plus récent)
    2. PDF 2019-2021  (rapport précédent)
    3. CSV historique (données legacy)
- Sauvegarde dans 'performances_bancaires_unified' (DEV)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.database import MongoDBConnection


# Priorité source : plus le chiffre est BAS, plus la source est fiable
SOURCE_PRIORITY = {
    'pdf_extraction': 1,     # PDF en général (géré + finement ci-dessous)
    'csv_historique': 3,
}
# PDF 2021-2023 vs PDF 2019-2021 → distingué par _source_file
PDF_RECENT_PRIORITY   = 1
PDF_OLDER_PRIORITY    = 2
CSV_PRIORITY          = 3


class DataNormalizer:
    """Normalise et fusionne les données CSV historiques et PDF BCEAO."""

    def __init__(self):
        self.mongo = MongoDBConnection(environment='dev')
        self.df_csv = None
        self.df_pdf = None
        self.df_merged = None

    # ── Chargement ────────────────────────────────────────────────────────────

    def load_data(self):
        print("\n" + "="*80)
        print("📥 CHARGEMENT DES DONNÉES DEPUIS MONGODB DEV")
        print("="*80)

        if not self.mongo.connect():
            print("❌ Connexion MongoDB échouée")
            return False

        collection = self.mongo.get_collection()

        # ── Données CSV (source = 'csv_historique') ───────────────────────
        csv_docs = list(collection.find({"_source": "csv_historique"}))
        print(f"\n📂 Données CSV historiques : {len(csv_docs)} documents")
        if csv_docs:
            self.df_csv = pd.DataFrame(csv_docs)
            if '_id' in self.df_csv.columns:
                self.df_csv = self.df_csv.drop('_id', axis=1)
            annees_csv = sorted(self.df_csv['ANNEE'].dropna().astype(int).unique()) if 'ANNEE' in self.df_csv.columns else []
            print(f"   Banques : {self.df_csv['Sigle'].nunique() if 'Sigle' in self.df_csv.columns else '?'}")
            print(f"   Années  : {annees_csv}")

        # ── Données PDF (type = 'pdf_extraction') ─────────────────────────
        pdf_docs = list(collection.find({"_type": "pdf_extraction"}))
        print(f"\n📄 Données PDF extraites : {len(pdf_docs)} documents")
        if pdf_docs:
            self.df_pdf = pd.DataFrame(pdf_docs)
            for col in ['_id', '_import_date', '_type']:
                if col in self.df_pdf.columns:
                    self.df_pdf = self.df_pdf.drop(col, axis=1)
            annees_pdf = sorted(self.df_pdf['ANNEE'].dropna().astype(int).unique()) if 'ANNEE' in self.df_pdf.columns else []
            print(f"   Banques : {self.df_pdf['Sigle'].nunique() if 'Sigle' in self.df_pdf.columns else '?'}")
            print(f"   Années  : {annees_pdf}")

        self.mongo.close()

        if csv_docs and not pdf_docs:
            print("\n⚠️  Aucune donnée PDF — seules les données CSV seront disponibles")
        return True

    # ── Analyse des schémas ───────────────────────────────────────────────────

    def analyze_schemas(self):
        print("\n" + "="*80)
        print("🔍 ANALYSE DES SCHÉMAS CSV vs PDF")
        print("="*80)

        if self.df_csv is None or self.df_pdf is None:
            print("⚠️  L'une des sources est absente, analyse limitée")
            return

        csv_cols = set(c for c in self.df_csv.columns if not c.startswith('_'))
        pdf_cols = set(c for c in self.df_pdf.columns if not c.startswith('_'))

        common   = csv_cols & pdf_cols
        only_csv = csv_cols - pdf_cols
        only_pdf = pdf_cols - csv_cols

        print(f"\n✅ Colonnes communes    : {len(common)}")
        print(f"   CSV seulement       : {sorted(only_csv)}")
        print(f"   PDF seulement       : {sorted(only_pdf)}")

        # Vérifier chevauchements (Banque/Année)
        if 'Sigle' in self.df_csv.columns and 'Sigle' in self.df_pdf.columns:
            csv_keys = set(zip(self.df_csv['Sigle'].astype(str), self.df_csv['ANNEE'].astype(str)))
            pdf_keys = set(zip(self.df_pdf['Sigle'].astype(str), self.df_pdf['ANNEE'].astype(str)))
            overlaps = csv_keys & pdf_keys
            if overlaps:
                print(f"\n[WARN] Chevauchements (Banque, Année) CSV ∩ PDF : {len(overlaps)}")
                for b, y in sorted(overlaps)[:10]:
                    print(f"   - {b} | {y}")
                print(f"   -> Fusion intelligente champ par champ appliquée")
            else:
                print(f"\n[OK] Aucun chevauchement détecté")

    # ── Fusion intelligente ────────────────────────────────────────────────────

    def normalize_and_merge(self):
        """
        Fusion 3 niveaux :
        - Chaque enregistrement reçoit une priorité selon sa source
        - Pour chaque champ d'un (Banque, Année) donné, on prend la valeur
          de la source la plus fiable (priorité la plus basse)
        """
        print("\n" + "="*80)
        print("🔄 NORMALISATION ET FUSION INTELLIGENTE")
        print("="*80)

        frames = []

        # ── Traitement CSV ────────────────────────────────────────────────
        if self.df_csv is not None:
            df_csv = self.df_csv.copy()
            df_csv['_source_type']     = 'csv_historique'
            df_csv['_source_priority'] = CSV_PRIORITY
            frames.append(df_csv)

        # ── Traitement PDF : distinguer récent vs ancien par l'année max ──
        if self.df_pdf is not None:
            df_pdf = self.df_pdf.copy()

            # Identifier les PDF selon les années présentes
            # PDF 2021-2023 → ANNEE max ≥ 2022
            # PDF 2019-2021 → ANNEE max ≤ 2021
            if 'ANNEE' in df_pdf.columns:
                df_pdf['ANNEE'] = pd.to_numeric(df_pdf['ANNEE'], errors='coerce')

                df_pdf_recent = df_pdf[df_pdf['ANNEE'] >= 2022].copy()
                df_pdf_older  = df_pdf[df_pdf['ANNEE'] <= 2021].copy()

                # Pour 2021 spécifiquement : les deux PDFs peuvent y contribuer
                df_pdf_2021_recent = df_pdf[df_pdf['ANNEE'] == 2021].copy()

                df_pdf_recent['_source_type']     = 'pdf_recent_2021_2023'
                df_pdf_recent['_source_priority'] = PDF_RECENT_PRIORITY

                df_pdf_older['_source_type']     = 'pdf_older_2019_2021'
                df_pdf_older['_source_priority'] = PDF_OLDER_PRIORITY

                frames.append(df_pdf_recent)
                frames.append(df_pdf_older)
            else:
                df_pdf['_source_type']     = 'pdf_extraction'
                df_pdf['_source_priority'] = PDF_RECENT_PRIORITY
                frames.append(df_pdf)

        if not frames:
            print("❌ Aucune donnée à fusionner")
            return False

        # ── Concaténation brute ───────────────────────────────────────────
        df_all = pd.concat(frames, ignore_index=True)

        # S'assurer que ANNEE et Sigle sont bien typés
        df_all['ANNEE'] = pd.to_numeric(df_all['ANNEE'], errors='coerce')
        df_all['Sigle'] = df_all['Sigle'].astype(str).str.strip()

        # Trier : priorité la plus haute (chiffre le plus bas) en premier
        df_all = df_all.sort_values('_source_priority', ascending=True)

        print(f"\n   Lignes avant dédoublonnage : {len(df_all)}")

        # ── Fusion champ par champ ───────────────────────────────────────
        # Pour chaque (Sigle, ANNEE), on prend la première valeur non-nulle/non-zéro
        # dans l'ordre de priorité (pdf_recent > pdf_older > csv)

        meta_cols   = [c for c in df_all.columns if c.startswith('_')]
        data_cols   = [c for c in df_all.columns if not c.startswith('_') and c not in ['Sigle', 'ANNEE']]

        def first_valid(series):
            """Prend la première valeur non-null et non-zéro d'une série triée par priorité."""
            valid = series.dropna()
            valid = valid[valid != 0] if valid.dtype in [float, int] else valid
            if not valid.empty:
                return valid.iloc[0]
            # Retour à la première valeur disponible (même si 0 ou NaN)
            return series.iloc[0] if not series.empty else None

        # Fusion sur les colonnes de données
        df_merged_data = df_all.groupby(['Sigle', 'ANNEE'], sort=False)[data_cols].agg(first_valid).reset_index()

        # Garder les métadonnées de la source prioritaire
        df_meta = df_all.drop_duplicates(subset=['Sigle', 'ANNEE'], keep='first')[['Sigle', 'ANNEE'] + meta_cols]
        self.df_merged = df_merged_data.merge(df_meta, on=['Sigle', 'ANNEE'], how='left')

        print(f"   Lignes après fusion     : {len(self.df_merged)}")

        if 'ANNEE' in self.df_merged.columns:
            print(f"\n📅 Répartition par année après fusion :")
            for yr, cnt in self.df_merged['ANNEE'].value_counts().sort_index().items():
                print(f"   {int(yr)} : {cnt} banques")

        if 'Sigle' in self.df_merged.columns:
            print(f"\n🏦 Banques distinctes : {self.df_merged['Sigle'].nunique()}")

        return True

    # ── Sauvegarde ────────────────────────────────────────────────────────────

    def save_to_mongodb(self):
        print("\n" + "="*80)
        print("💾 SAUVEGARDE DANS 'performances_bancaires_unified' (DEV)")
        print("="*80)

        if self.df_merged is None or len(self.df_merged) == 0:
            print("⚠️  Aucune donnée à sauvegarder")
            return False

        if not self.mongo.connect():
            return False

        try:
            db = self.mongo.client[self.mongo.db_name]
            collection_unified = db['performances_bancaires_unified']
            collection_unified.drop()
            print(f"   [CLEAN] Collection '_unified' réinitialisée")

            records = []
            for _, row in self.df_merged.iterrows():
                record = {}
                for col in self.df_merged.columns:
                    val = row[col]
                    if pd.isna(val):
                        record[col] = None
                    elif isinstance(val, (np.int64, np.float64)):
                        record[col] = int(val) if isinstance(val, np.int64) else float(val)
                    else:
                        record[col] = val
                record['_unified_date'] = datetime.now()
                records.append(record)

            batch_size = 100
            inserted = 0
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                result = collection_unified.insert_many(batch)
                inserted += len(result.inserted_ids)

            print(f"\n[OK] {inserted} documents insérés dans 'performances_bancaires_unified'")

            # Index
            collection_unified.create_index([("Sigle", 1), ("ANNEE", 1)])
            collection_unified.create_index([("ANNEE", 1)])
            collection_unified.create_index([("Sigle", 1)])
            print("   🔍 Index créés")
            return True

        except Exception as e:
            print(f"❌ Erreur sauvegarde : {e}")
            import traceback; traceback.print_exc()
            return False
        finally:
            self.mongo.close()

    # ── Run ───────────────────────────────────────────────────────────────────

    def run(self):
        print("="*80)
        print("🚀 NORMALISATION ET FUSION — ÉTAPE 4")
        print("="*80)

        if not self.load_data():
            return

        self.analyze_schemas()

        if not self.normalize_and_merge():
            return

        if self.save_to_mongodb():
            print("\n" + "="*80)
            print("[OK] NORMALISATION TERMINÉE")
            print("   -> Collection : 'performances_bancaires_unified' (DEV)")
            print("   -> Prochaine étape : cleaning.py (Étape 5)")
            print("="*80)
        else:
            print("\n❌ Erreur lors de la sauvegarde")


if __name__ == "__main__":
    DataNormalizer().run()
