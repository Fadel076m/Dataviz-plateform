"""
Étape 5 : Nettoyage et Validation des Données
- Chargement depuis 'performances_bancaires_unified'
- Fusion intelligente des doublons (Banque/Année)
- Détection et correction des aberrations (IQR method)
- Validation : nombre de banques ≥ 20, colonnes critiques remplies
- Sauvegarde dans 'performances_bancaires_clean' (DEV)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.database import MongoDBConnection

# Colonnes monétaires principales (en millions FCFA)
MONETARY_COLS = ['BILAN', 'EMPLOI', 'RESSOURCES', 'FONDS.PROPRE', 'RESULTAT.NET',
                 'PRODUIT.NET.BANCAIRE', "CHARGES.GENERALES.D'EXPLOITATION"]

# Colonnes qui ne peuvent pas être négatives
POSITIVE_ONLY_COLS = ['BILAN', 'EMPLOI', 'RESSOURCES', 'FONDS.PROPRE', 'EFFECTIF', 'AGENCE']

# Colonnes clés pour valider la couverture
KEY_COLS = ['BILAN', 'FONDS.PROPRE', 'RESULTAT.NET', 'RESSOURCES',
            'PRODUIT.NET.BANCAIRE', 'EMPLOI', 'EFFECTIF', 'AGENCE']

# Nombre minimum de banques attendues
MIN_BANKS = 20


class DataCleaner:
    """Nettoie, valide et prépare les données pour l'enrichissement."""

    def __init__(self):
        self.mongo = MongoDBConnection(environment='dev')
        self.df = None
        self.stats = {
            'lignes_initiales': 0,
            'lignes_finales': 0,
            'doublons_fusionnes': 0,
            'outliers_corriges': 0,
        }

    # ── Chargement ────────────────────────────────────────────────────────────

    def load_unified_data(self):
        print("\n" + "="*80)
        print("📥 CHARGEMENT DEPUIS 'performances_bancaires_unified'")
        print("="*80)

        if not self.mongo.connect():
            print("❌ Connexion MongoDB échouée")
            return False

        try:
            db = self.mongo.client[self.mongo.db_name]
            docs = list(db['performances_bancaires_unified'].find({}))

            if not docs:
                print("⚠️  Collection vide. Exécutez d'abord normalisation.py")
                return False

            self.df = pd.DataFrame(docs)
            for col in ['_id', '_unified_date']:
                if col in self.df.columns:
                    self.df = self.df.drop(col, axis=1)

            self.stats['lignes_initiales'] = len(self.df)
            print(f"\n[OK] {len(self.df)} documents chargés")
            print(f"   Banques : {self.df['Sigle'].nunique() if 'Sigle' in self.df.columns else '?'}")
            print(f"   Années  : {sorted(self.df['ANNEE'].dropna().astype(int).unique()) if 'ANNEE' in self.df.columns else '?'}")
            return True

        except Exception as e:
            print(f"❌ Erreur : {e}")
            return False
        finally:
            self.mongo.close()

    # ── Nettoyage des types ───────────────────────────────────────────────────

    def fix_types(self):
        """Convert colonnes numériques et textes."""
        print("\n🔧 CONVERSION DES TYPES")

        # ANNEE en entier
        if 'ANNEE' in self.df.columns:
            self.df['ANNEE'] = pd.to_numeric(self.df['ANNEE'], errors='coerce').astype('Int64')

        # Colonnes numériques
        all_num_cols = MONETARY_COLS + ['EFFECTIF', 'AGENCE', 'COMPTE']
        for col in all_num_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

        # Colonnes texte
        for col in ['Sigle', 'Goupe_Bancaire']:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(str).str.strip()
                self.df[col] = self.df[col].replace({'nan': None, '': None})

        print("   ✅ Types convertis")

    # ── Fusion des doublons restants ──────────────────────────────────────────

    def handle_duplicates(self):
        """Fusionne les doublons résiduels (Banque, Année) par first_valid."""
        print("\n" + "="*80)
        print("🔍 FUSION DES DOUBLONS RÉSIDUELS (Banque, Année)")
        print("="*80)

        if 'Sigle' not in self.df.columns or 'ANNEE' not in self.df.columns:
            return

        n_avant = len(self.df)
        doublons = self.df.duplicated(subset=['Sigle', 'ANNEE'], keep=False).sum()

        if doublons == 0:
            print(f"   ✅ Aucun doublon (Sigle, ANNEE) détecté")
            return

        print(f"   ⚠️  {doublons} lignes doublons détectées → fusion en cours")

        meta_cols = [c for c in self.df.columns if c.startswith('_')]
        data_cols = [c for c in self.df.columns if not c.startswith('_')]

        def first_valid(series):
            if pd.api.types.is_numeric_dtype(series):
                valid = series.dropna()
                valid = valid[valid != 0]
                return valid.iloc[0] if not valid.empty else series.iloc[0]
            else:
                valid = series.dropna()
                return valid.iloc[0] if not valid.empty else None

        df_data   = self.df.groupby(['Sigle', 'ANNEE'], sort=False)[data_cols].agg(first_valid).reset_index()
        df_meta   = self.df.sort_values('_source_priority', ascending=True).drop_duplicates(
            ['Sigle', 'ANNEE'], keep='first')[['Sigle', 'ANNEE'] + meta_cols]
        self.df   = df_data.merge(df_meta, on=['Sigle', 'ANNEE'], how='left')

        n_apres = len(self.df)
        self.stats['doublons_fusionnes'] = n_avant - n_apres
        print(f"   ✅ {self.stats['doublons_fusionnes']} doublons fusionnés → {n_apres} lignes")

    # ── Détection outliers (méthode IQR) ─────────────────────────────────────

    def detect_and_fix_aberrations(self):
        """
        Détecte les valeurs aberrantes par méthode IQR par année.
        Stratégie : plafonner les valeurs extrêmes (winsorisation) plutôt que les supprimer.
        """
        print("\n" + "="*80)
        print("🛠️  DÉTECTION DES ABERRATIONS (Méthode IQR)")
        print("="*80)

        total_corriges = 0

        for col in MONETARY_COLS:
            if col not in self.df.columns:
                continue

            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

            # Correction par année pour comparer des valeurs comparables
            for year in self.df['ANNEE'].dropna().unique():
                mask_year = (self.df['ANNEE'] == year)
                série = self.df.loc[mask_year, col].dropna()

                if len(série) < 4:
                    continue

                Q1  = série.quantile(0.25)
                Q3  = série.quantile(0.75)
                IQR = Q3 - Q1

                if IQR == 0:
                    continue

                lower = Q1 - 3.0 * IQR
                upper = Q3 + 3.0 * IQR

                # Détecter les outliers
                mask_out = mask_year & (
                    (self.df[col] < lower) | (self.df[col] > upper)
                ) & self.df[col].notna()

                n_out = mask_out.sum()
                if n_out > 0:
                    total_corriges += n_out
                    # Winsorisation : plafonner aux bornes IQR
                    self.df.loc[mask_out & (self.df[col] < lower), col] = lower
                    self.df.loc[mask_out & (self.df[col] > upper), col] = upper
                    print(f"   ⚠️  {col} ({int(year)}) : {n_out} outlier(s) corrigé(s) [lower={lower:.0f}, upper={upper:.0f}]")

        # Suppression des valeurs impossibles (négatifs sur colonnes positives)
        for col in POSITIVE_ONLY_COLS:
            if col in self.df.columns:
                mask_neg = (self.df[col] < 0) & self.df[col].notna()
                if mask_neg.sum() > 0:
                    print(f"   ⚠️  {col} : {mask_neg.sum()} valeurs négatives → None")
                    self.df.loc[mask_neg, col] = None

        self.stats['outliers_corriges'] = total_corriges
        print(f"\n   ✅ Total outliers corrigés : {total_corriges}")

    # ── Analyse valeurs manquantes ────────────────────────────────────────────

    def analyze_missing_values(self):
        print("\n" + "="*80)
        print("📊 ANALYSE DES VALEURS MANQUANTES")
        print("="*80)

        existing = [c for c in KEY_COLS if c in self.df.columns]
        print(f"\n{'Colonne':<60} {'Rempli':>8} {'% Couvert':>10}")
        print("-" * 80)
        for col in existing:
            n_valid  = self.df[col].notna().sum()
            pct      = n_valid / len(self.df) * 100
            icon     = "✅" if pct > 80 else "⚠️ " if pct > 50 else "❌"
            print(f"  {icon} {col:<55} {n_valid:>6}   {pct:>8.1f}%")

    # ── Validation finale ─────────────────────────────────────────────────────

    def validate_quality(self):
        print("\n" + "="*80)
        print("✅ VALIDATION DE QUALITÉ")
        print("="*80)

        issues = []

        n_banks = self.df['Sigle'].nunique() if 'Sigle' in self.df.columns else 0
        print(f"\n🏦 Banques distinctes : {n_banks}")
        if n_banks < MIN_BANKS:
            issues.append(f"Seulement {n_banks} banques (attendu >= {MIN_BANKS})")
            print(f"   [WARN] ATTENTION : moins de {MIN_BANKS} banques !")
        else:
            print(f"   [OK] Couverture bancaire satisfaisante")

        # Années
        if 'ANNEE' in self.df.columns:
            years = sorted(self.df['ANNEE'].dropna().astype(int).unique())
            print(f"\n📅 Années disponibles : {years}")
            expected = list(range(2015, 2024))
            manquantes = [y for y in expected if y not in years]
            if manquantes:
                print(f"   ⚠️  Années manquantes : {manquantes}")

        # Doublons résiduels
        dups = self.df.duplicated(subset=['Sigle', 'ANNEE']).sum()
        if dups > 0:
            issues.append(f"{dups} doublons (Sigle, ANNEE) encore présents")
            print(f"\n❌ {dups} doublons résiduels !")
        else:
            print(f"\n✅ Aucun doublon (Sigle, ANNEE)")

        if not issues:
            print("\n" + "="*80)
            print("✅ VALIDATION RÉUSSIE — Données prêtes pour l'enrichissement")
            print("="*80)
        else:
            print("\n⚠️  Problèmes détectés :")
            for issue in issues:
                print(f"   - {issue}")

        return len(issues) == 0

    # ── Sauvegarde ────────────────────────────────────────────────────────────

    def save_clean_data(self):
        print("\n" + "="*80)
        print("💾 SAUVEGARDE DANS 'performances_bancaires_clean' (DEV)")
        print("="*80)

        if self.df is None or len(self.df) == 0:
            print("⚠️  Aucune donnée")
            return False

        if not self.mongo.connect():
            return False

        try:
            db = self.mongo.client[self.mongo.db_name]
            coll = db['performances_bancaires_clean']
            coll.drop()
            print(f"   [CLEAN] Collection '_clean' réinitialisée")

            records = []
            for _, row in self.df.iterrows():
                record = {}
                for col in self.df.columns:
                    val = row[col]
                    if pd.isna(val):
                        record[col] = None
                    elif hasattr(val, 'item'): # Gère numpy/pandas types
                        record[col] = val.item()
                    else:
                        record[col] = val
                record['_cleaned_date'] = datetime.now()
                records.append(record)

            batch_size = 100
            inserted = 0
            for i in range(0, len(records), batch_size):
                result = coll.insert_many(records[i:i+batch_size])
                inserted += len(result.inserted_ids)

            # Index unique sur (Sigle, ANNEE)
            coll.create_index([("Sigle", 1), ("ANNEE", 1)], unique=True)
            coll.create_index([("ANNEE", 1)])

            self.stats['lignes_finales'] = int(inserted)
            print(f"\n[OK] {inserted} documents dans 'performances_bancaires_clean'")

            # Rapport qualité pipeline
            quality = {
                "date": datetime.now().isoformat(),
                "nb_banques": int(self.df['Sigle'].nunique()),
                "sigles": sorted([str(s) for s in self.df['Sigle'].unique()]),
                "annees": sorted([int(y) for y in self.df['ANNEE'].dropna().unique()]),
                "lignes_initiales": int(self.stats['lignes_initiales']),
                "lignes_finales": int(inserted),
                "doublons_fusionnes": int(self.stats['doublons_fusionnes']),
                "outliers_corriges": int(self.stats['outliers_corriges']),
            }
            report_path = Path(__file__).resolve().parent.parent / "data" / "pipeline_quality_report.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(quality, f, indent=2, ensure_ascii=False)
            print(f"   📄 Rapport qualité : {report_path}")

            return True

        except Exception as e:
            print(f"❌ Erreur : {e}")
            import traceback; traceback.print_exc()
            return False
        finally:
            self.mongo.close()

    # ── Run ───────────────────────────────────────────────────────────────────

    def run(self):
        print("="*80)
        print("🧹 NETTOYAGE ET VALIDATION — ÉTAPE 5")
        print("="*80)

        if not self.load_unified_data():
            return
        self.fix_types()
        self.handle_duplicates()
        self.detect_and_fix_aberrations()
        self.analyze_missing_values()
        self.validate_quality()

        if self.save_clean_data():
            print("\n" + "="*80)
            print("[OK] NETTOYAGE TERMINÉ")
            print(f"   Lignes initiales         : {self.stats['lignes_initiales']}")
            print(f"   Doublons fusionnés        : {self.stats['doublons_fusionnes']}")
            print(f"   Outliers corrigés (IQR)   : {self.stats['outliers_corriges']}")
            print(f"   Lignes finales            : {self.stats['lignes_finales']}")
            print("\n   -> Prochaine étape : enrichment.py (Étape 6)")
            print("="*80)


if __name__ == "__main__":
    DataCleaner().run()
