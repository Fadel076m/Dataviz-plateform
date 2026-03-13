"""
pipeline_master.py
==================
Pipeline complet de données bancaires BCEAO.

Étapes :
  1. Ingestion CSV (base_senegal.csv) → DEV.performances_bancaires
  2. OCR PDF (bilans BCEAO)          → DEV.performances_bancaires
  3. Normalisation & Fusion           → DEV.performances_bancaires_unified
  4. Nettoyage & Validation           → DEV.performances_bancaires_clean
  5. Enrichissement & Ratios         → DEV.performances_bancaires_prod
  6. Migration DEV → PROD            → PROD.performances_bancaires_prod

Usage :
  python scripts/pipeline_master.py [--step N]  (défaut = toutes les étapes)
"""

import sys
import re
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

# Ajouter la racine au path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from config.database import MongoDBConnection

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES GLOBALES
# ══════════════════════════════════════════════════════════════════════════════

CSV_PATH = ROOT / "data" / "base_senegal.csv"
PDF_DIR  = ROOT / "data" / "pdf"

# Colonnes dans l'ordre EXACT du CSV (après Sigle, Goupe_Bancaire, ANNEE)
CSV_COLUMNS = [
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

# Groupes des banques (Sigle → Goupe_Bancaire selon le CSV)
BANK_GROUPS = {
    "BAS":      "Groupes Continentaux",
    "BCIM":     "Groupes Règionaux",
    "BDK":      "Groupes Règionaux",
    "BGFI":     "Groupes Règionaux",
    "BICIS":    "Groupes Internationaux",
    "BIS":      "Groupes Règionaux",
    "BNDE":     "Groupes Locaux",
    "BOA":      "Groupes Continentaux",
    "BRM":      "Groupes Règionaux",
    "BHS":      "Groupes Locaux",
    "BSIC":     "Groupes Règionaux",
    "CBAO":     "Groupes Continentaux",
    "CBI":      "Groupes Règionaux",
    "CDS":      "Groupes Règionaux",
    "CISA":     "Groupes Internationaux",
    "CITIBANK": "Groupes Continentaux",
    "ECOBANK":  "Groupes Continentaux",
    "FBNBANK":  "Groupes Continentaux",
    "LBA":      "Groupes Locaux",
    "LBO":      "Groupes Locaux",
    "NSIA Banque": "Groupes Règionaux",
    "ORABANK":  "Groupes Continentaux",
    "SGBS":     "Groupes Internationaux",
    "UBA":      "Groupes Continentaux",
}

# Métadonnées enrichissement
BANK_METADATA = {
    "CBAO":     {"Groupe": "Attijariwafa Bank (Maroc)",          "Type": "Régional",       "Lat": 14.6712, "Lon": -17.4300},
    "SGBS":     {"Groupe": "Société Générale (France)",          "Type": "International",  "Lat": 14.6698, "Lon": -17.4320},
    "BICIS":    {"Groupe": "Groupe SUNU (Régional)",             "Type": "Régional",       "Lat": 14.6705, "Lon": -17.4310},
    "ECOBANK":  {"Groupe": "Ecobank Transnational (Togo)",       "Type": "Régional",       "Lat": 14.6730, "Lon": -17.4350},
    "BOA":      {"Groupe": "Bank of Africa (Maroc)",             "Type": "Régional",       "Lat": 14.6720, "Lon": -17.4400},
    "BIS":      {"Groupe": "Banque Islamique du Sénégal",        "Type": "National",       "Lat": 14.6750, "Lon": -17.4380},
    "UBA":      {"Groupe": "UBA Group (Nigeria)",                "Type": "Régional",       "Lat": 14.6740, "Lon": -17.4360},
    "BHS":      {"Groupe": "Banque de l'Habitat du Sénégal",     "Type": "National",       "Lat": 14.6800, "Lon": -17.4500},
    "LBA":      {"Groupe": "La Banque Africaine",                "Type": "National",       "Lat": 14.6780, "Lon": -17.4450},
    "CITIBANK": {"Groupe": "Citigroup (USA)",                    "Type": "International",  "Lat": 14.6680, "Lon": -17.4280},
    "BNDE":     {"Groupe": "BNDE (Sénégal)",                     "Type": "National",       "Lat": 14.6900, "Lon": -17.4600},
    "NSIA Banque": {"Groupe": "NSIA Banque (Côte d'Ivoire)",     "Type": "Régional",       "Lat": 14.6760, "Lon": -17.4340},
    "ORABANK":  {"Groupe": "Oragroup (Togo)",                    "Type": "Régional",       "Lat": 14.6725, "Lon": -17.4330},
    "BGFI":     {"Groupe": "BGFI Bank (Gabon)",                  "Type": "Régional",       "Lat": 14.6850, "Lon": -17.4550},
    "BDK":      {"Groupe": "Banque de Dakar",                    "Type": "National",       "Lat": 14.6950, "Lon": -17.4650},
    "CISA":     {"Groupe": "Crédit International SA",            "Type": "National",       "Lat": 14.6700, "Lon": -17.4300},
    "CDS":      {"Groupe": "Crédit du Sénégal",                  "Type": "National",       "Lat": 14.6710, "Lon": -17.4310},
    "CBI":      {"Groupe": "Coris Bank (Burkina Faso)",          "Type": "Régional",       "Lat": 14.6745, "Lon": -17.4370},
    "BRM":      {"Groupe": "Banque Régionale de Marchés",        "Type": "National",       "Lat": 14.6770, "Lon": -17.4420},
    "BSIC":     {"Groupe": "BSIC Group (Libye)",                 "Type": "Régional",       "Lat": 14.6715, "Lon": -17.4315},
    "FBNBANK":  {"Groupe": "First Bank of Nigeria",              "Type": "Régional",       "Lat": 14.6735, "Lon": -17.4355},
    "BCIM":     {"Groupe": "BCIM Group",                         "Type": "Régional",       "Lat": 14.6700, "Lon": -17.4300},
    "LBO":      {"Groupe": "Banque Libyano-Emiratie",            "Type": "Régional",       "Lat": 14.6720, "Lon": -17.4320},
    "BAS":      {"Groupe": "Attijariwafa Bank (Maroc)",          "Type": "Régional",       "Lat": 14.6710, "Lon": -17.4310},
}
DEFAULT_META = {"Groupe": "Non Classifié", "Type": "Autre", "Lat": 14.6928, "Lon": -17.4467}

# ══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES
# ══════════════════════════════════════════════════════════════════════════════

def header(title: str):
    print(f"\n{'═'*70}")
    print(f"  {title}")
    print(f"{'═'*70}")


def safe_int(v):
    """Convertit en int Python natif ou None."""
    if v is None:
        return None
    if isinstance(v, float) and np.isnan(v):
        return None
    try:
        return int(v)
    except (ValueError, TypeError):
        return None


def clean_record(record: dict) -> dict:
    """Nettoie un dict pour MongoDB (NaN → None, numpy → python natif)."""
    cleaned = {}
    for k, v in record.items():
        if isinstance(v, float) and np.isnan(v):
            cleaned[k] = None
        elif isinstance(v, (np.integer,)):
            cleaned[k] = int(v)
        elif isinstance(v, (np.floating,)):
            cleaned[k] = float(v) if not np.isnan(v) else None
        elif isinstance(v, pd.Timestamp):
            cleaned[k] = v.to_pydatetime()
        else:
            cleaned[k] = v
    return cleaned


def normalize_text(t: str) -> str:
    if not t:
        return ""
    t = t.upper()
    for s, d in [("É","E"),("È","E"),("Ê","E"),("Ë","E"),("À","A"),("Â","A"),
                 ("Ä","A"),("Î","I"),("Ï","I"),("Ô","O"),("Ö","O"),("Ù","U"),
                 ("Û","U"),("Ü","U"),("Ç","C"),("Œ","OE"),("Æ","AE")]:
        t = t.replace(s, d)
    return re.sub(r'\s+', ' ', t).strip()


# ══════════════════════════════════════════════════════════════════════════════
# ÉTAPE 1 : INGESTION CSV
# ══════════════════════════════════════════════════════════════════════════════

def step1_ingest_csv():
    header("ÉTAPE 1 — INGESTION CSV → DEV.performances_bancaires")

    if not CSV_PATH.exists():
        print(f"❌ Fichier CSV introuvable : {CSV_PATH}")
        return False

    # Lire le CSV (séparateur ;)
    df = pd.read_csv(CSV_PATH, sep=";", encoding="utf-8")
    print(f"  ✅ CSV chargé : {len(df)} lignes × {len(df.columns)} colonnes")
    print(f"  Colonnes : {list(df.columns)}")

    # Supprimer les lignes entièrement vides
    df = df.dropna(how="all")

    # Vérifier colonnes obligatoires
    for col in ["Sigle", "ANNEE"]:
        if col not in df.columns:
            print(f"  ❌ Colonne obligatoire manquante : {col}")
            return False

    # Nettoyer les valeurs texte (Sigle, Goupe_Bancaire)
    df["Sigle"] = df["Sigle"].astype(str).str.strip()
    if "Goupe_Bancaire" in df.columns:
        df["Goupe_Bancaire"] = df["Goupe_Bancaire"].astype(str).str.strip()

    # Convertir ANNEE en int
    df["ANNEE"] = pd.to_numeric(df["ANNEE"], errors="coerce")
    df = df.dropna(subset=["ANNEE"])
    df["ANNEE"] = df["ANNEE"].astype(int)

    # Convertir toutes les colonnes numériques
    for col in CSV_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    print(f"\n  Banques : {sorted(df['Sigle'].unique())}")
    print(f"  Années  : {sorted(df['ANNEE'].unique())}")
    print(f"  Lignes valides : {len(df)}")

    # Insérer dans MongoDB DEV
    mongo = MongoDBConnection(environment='dev')
    if not mongo.connect():
        return False

    coll = mongo.get_collection()  # performances_bancaires

    # Supprimer les anciens docs CSV
    deleted = coll.delete_many({"$or": [
        {"_type": {"$exists": False}},
        {"_type": None},
        {"_type": "csv_historique"},
    ]})
    print(f"\n  → {deleted.deleted_count} anciens documents CSV supprimés")

    records = []
    for _, row in df.iterrows():
        r = clean_record(row.to_dict())
        r["_type"] = "csv_historique"
        r["_source_file"] = "base_senegal.csv"
        r["_import_date"] = datetime.now()
        records.append(r)

    if records:
        coll.insert_many(records)
        print(f"  ✅ {len(records)} documents CSV insérés dans DEV.performances_bancaires")

    mongo.close()
    return True


# ══════════════════════════════════════════════════════════════════════════════
# ÉTAPE 2 : OCR PDF
# ══════════════════════════════════════════════════════════════════════════════

def step2_ocr_pdf():
    header("ÉTAPE 2 — OCR PDF → DEV.performances_bancaires")

    try:
        import pdfplumber
    except ImportError:
        print("❌ pdfplumber non installé. Exécutez : pip install pdfplumber")
        return False

    pdf_files = sorted(PDF_DIR.rglob("*.pdf"))
    if not pdf_files:
        print(f"  ⚠️  Aucun PDF trouvé dans {PDF_DIR}")
        print("  → L'étape OCR est ignorée (les données CSV seront utilisées seules)")
        return True

    print(f"  {len(pdf_files)} PDF trouvé(s) :")
    for f in pdf_files:
        print(f"    - {f.name} ({f.stat().st_size / 1_000_000:.1f} MB)")

    # Import du module OCR
    ocr_script = ROOT / "scripts" / "robust_ocr.py"
    if not ocr_script.exists():
        print(f"❌ Script OCR introuvable : {ocr_script}")
        return False

    sys.path.insert(0, str(ROOT / "scripts"))
    from robust_ocr import PDFExtractor
    extractor = PDFExtractor()
    extractor.run()
    return True


# ══════════════════════════════════════════════════════════════════════════════
# ÉTAPE 3 : NORMALISATION & FUSION
# ══════════════════════════════════════════════════════════════════════════════

def step3_normalize_merge():
    header("ÉTAPE 3 — NORMALISATION & FUSION → DEV.performances_bancaires_unified")

    mongo = MongoDBConnection(environment='dev')
    if not mongo.connect():
        return False

    coll = mongo.get_collection()

    # Charger données CSV
    csv_docs = list(coll.find({
        "$or": [
            {"_type": "csv_historique"},
            {"_type": {"$exists": False}},
        ]
    }))
    print(f"\n  Documents CSV : {len(csv_docs)}")

    # Charger données PDF
    pdf_docs = list(coll.find({"_type": "pdf_extraction"}))
    print(f"  Documents PDF : {len(pdf_docs)}")

    mongo.close()

    if not csv_docs and not pdf_docs:
        print("  ❌ Aucune donnée disponible. Exécutez les étapes 1 et 2 d'abord.")
        return False

    dfs = []

    if csv_docs:
        df_csv = pd.DataFrame(csv_docs)
        for col in ["_id", "_import_date", "_source"]:
            if col in df_csv.columns:
                df_csv = df_csv.drop(col, axis=1)
        df_csv["_source_type"] = "csv_historique"
        df_csv["_source_file"] = "base_senegal.csv"
        dfs.append(df_csv)
        print(f"\n  CSV — Années : {sorted(df_csv['ANNEE'].dropna().unique())}")
        print(f"  CSV — Banques: {sorted(df_csv['Sigle'].dropna().unique())}")

    if pdf_docs:
        df_pdf = pd.DataFrame(pdf_docs)
        for col in ["_id", "_import_date", "_type"]:
            if col in df_pdf.columns:
                df_pdf = df_pdf.drop(col, axis=1)
        df_pdf["_source_type"] = "pdf_extraction"
        dfs.append(df_pdf)
        print(f"\n  PDF — Années : {sorted(df_pdf['ANNEE'].dropna().unique())}")
        print(f"  PDF — Banques: {sorted(df_pdf['Sigle'].dropna().unique())}")

    # Harmoniser les colonnes
    all_cols = set()
    for df in dfs:
        all_cols.update(df.columns)

    for i, df in enumerate(dfs):
        for col in all_cols:
            if col not in df.columns:
                dfs[i][col] = None

    # Fusionner
    df_merged = pd.concat(dfs, ignore_index=True)
    df_merged["ANNEE"] = pd.to_numeric(df_merged["ANNEE"], errors="coerce")
    df_merged = df_merged.dropna(subset=["Sigle", "ANNEE"])
    df_merged["ANNEE"] = df_merged["ANNEE"].astype(int)

    print(f"\n  Total fusionné : {len(df_merged)} lignes")
    print(f"  Banques uniques : {df_merged['Sigle'].nunique()}")
    print(f"  Années : {sorted(df_merged['ANNEE'].unique())}")

    # Sauvegarder
    mongo2 = MongoDBConnection(environment='dev')
    if not mongo2.connect():
        return False

    db = mongo2.client[mongo2.db_name]
    coll_u = db["performances_bancaires_unified"]
    coll_u.drop()

    records = []
    for _, row in df_merged.iterrows():
        r = clean_record(row.to_dict())
        r["_unified_date"] = datetime.now()
        records.append(r)

    if records:
        coll_u.insert_many(records)
        coll_u.create_index([("Sigle", 1), ("ANNEE", 1)])
        print(f"  ✅ {len(records)} documents → DEV.performances_bancaires_unified")

    mongo2.close()
    return True


# ══════════════════════════════════════════════════════════════════════════════
# ÉTAPE 4 : NETTOYAGE & VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def step4_clean():
    header("ÉTAPE 4 — NETTOYAGE & VALIDATION → DEV.performances_bancaires_clean")

    mongo = MongoDBConnection(environment='dev')
    if not mongo.connect():
        return False

    db = mongo.client[mongo.db_name]
    docs = list(db["performances_bancaires_unified"].find({}))
    mongo.close()

    if not docs:
        print("  ❌ Aucune donnée dans performances_bancaires_unified")
        return False

    df = pd.DataFrame(docs)
    for col in ["_id", "_unified_date"]:
        if col in df.columns:
            df = df.drop(col, axis=1)

    print(f"\n  Lignes initiales : {len(df)}")
    print(f"  Colonnes : {len(df.columns)}")

    # ── 1. Dédoublonnage INTELLIGENT (Fusion non-nulle) ─────────────────────
    print(f"\n  🔍 Fusion intelligente des doublons (Sigle x ANNEE)... ")
    
    # Stratégie : Fusionner toutes les occurrences en prenant la première valeur non-nulle/non-zéro
    def smart_merge(series):
        valid_vals = series[series.notna() & (series != 0)]
        if not valid_vals.empty:
            return valid_vals.iloc[0]
        return series.iloc[0]

    # Colonnes à ne pas agréger (métadonnées gérées après)
    meta_cols = [c for c in df.columns if c.startswith("_")]
    data_cols = [c for c in df.columns if c not in meta_cols and c not in ["Sigle", "ANNEE"]]
    
    # Fusion des données
    df_data = df.groupby(["Sigle", "ANNEE"])[data_cols].agg(smart_merge).reset_index()
    
    # Récupération des métadonnées (priorité PDF)
    df["_priority"] = df["_source_type"].apply(lambda x: 0 if x == "pdf_extraction" else 1)
    df_meta = df.sort_values("_priority").drop_duplicates(["Sigle", "ANNEE"])[["Sigle", "ANNEE"] + meta_cols]
    
    df = df_data.merge(df_meta, on=["Sigle", "ANNEE"], how="left")
    print(f"  ✅ Fusion terminée : {len(df)} lignes uniques")

    # ── 2. Détection et Correction des Aberrations (Scaling) ────────────────
    print(f"\n  🛠️ Correction des aberrations d'échelle...")
    monetary_cols = ["BILAN", "EMPLOI", "RESSOURCES", "FONDS.PROPRE", "RESULTAT.NET"]
    scaling_count = 0
    for col in monetary_cols:
        if col in df.columns:
            # Calcul de la médiane annuelle
            medians = df.groupby("ANNEE")[col].transform("median")
            # Correction si > 100x la médiane (Units -> Millions)
            mask_high = (df[col] > medians * 100) & (medians > 0)
            if mask_high.any():
                df.loc[mask_high, col] = df.loc[mask_high, col] / 1_000_000
                scaling_count += mask_high.sum()
            # Correction si < 0.01x la médiane (Milliards -> Millions)
            mask_low = (df[col] < medians / 100) & (df[col] > 0) & (medians > 0)
            if mask_low.any():
                df.loc[mask_low, col] = df.loc[mask_low, col] * 1_000
                scaling_count += mask_low.sum()
    
    if scaling_count:
        print(f"  ✅ {scaling_count} valeurs d'échelle corrigées (Millions vs FCFA/Milliards)")

    # ── 3. Nettoyage final (Zeros et Négatifs) ──────────────────────────────
    # Un BILAN de 0 est toujours une erreur OCR
    structural_cols = ["BILAN", "EMPLOI", "RESSOURCES", "FONDS.PROPRE"]
    zero_issues = 0
    for col in structural_cols:
        if col in df.columns:
            zero_mask = (df[col] == 0)
            if zero_mask.any():
                df.loc[zero_mask, col] = None
                zero_issues += zero_mask.sum()

    if zero_issues:
        print(f"  Zeros invalides remplacés par None : {zero_issues}")

    # ── 3. Vérification des valeurs non-négatives ─────────────────────────
    non_neg_cols = ["BILAN", "EMPLOI", "RESSOURCES", "FONDS.PROPRE"]
    for col in non_neg_cols:
        # Certains des noms avec accents existent aussi
        col_accent = col  # ex: COÛT.DU.RISQUE
        if col in df.columns:
            neg_mask = df[col] < 0
            if neg_mask.any():
                print(f"  ⚠️  {col} : {neg_mask.sum()} valeurs négatives (conservées, à vérifier)")

    # ── 4. Assigner Goupe_Bancaire si manquant ────────────────────────────
    if "Goupe_Bancaire" not in df.columns:
        df["Goupe_Bancaire"] = None
    df["Goupe_Bancaire"] = df.apply(
        lambda row: BANK_GROUPS.get(row["Sigle"], row.get("Goupe_Bancaire") or "Non Classifié"),
        axis=1
    )

    # ── 5. Rapport de remplissage ─────────────────────────────────────────
    print(f"\n  Taux de remplissage des colonnes principales :")
    key_cols = ["BILAN", "EMPLOI", "RESSOURCES", "FONDS.PROPRE",
                "PRODUIT.NET.BANCAIRE", "RESULTAT.NET"]
    for col in key_cols:
        if col in df.columns:
            pct = df[col].notna().mean() * 100
            icon = "✅" if pct > 70 else "⚠️ " if pct > 40 else "❌"
            print(f"    {icon} {col:<50} {pct:5.1f}%")

    print(f"\n  Lignes finales : {len(df)}")

    # ── 6. Sauvegarder ───────────────────────────────────────────────────
    mongo2 = MongoDBConnection(environment='dev')
    if not mongo2.connect():
        return False

    db2 = mongo2.client[mongo2.db_name]
    coll_c = db2["performances_bancaires_clean"]
    coll_c.drop()

    records = []
    for _, row in df.iterrows():
        r = clean_record(row.to_dict())
        r["_cleaned_date"] = datetime.now()
        records.append(r)

    if records:
        coll_c.insert_many(records)
        coll_c.create_index([("Sigle", 1), ("ANNEE", 1)], unique=True)
        coll_c.create_index([("ANNEE", 1)])
        print(f"  ✅ {len(records)} documents → DEV.performances_bancaires_clean")

    mongo2.close()
    return True


# ══════════════════════════════════════════════════════════════════════════════
# ÉTAPE 5 : ENRICHISSEMENT & RATIOS
# ══════════════════════════════════════════════════════════════════════════════

def step5_enrich():
    header("ÉTAPE 5 — ENRICHISSEMENT & RATIOS → DEV.performances_bancaires_prod")

    mongo = MongoDBConnection(environment='dev')
    if not mongo.connect():
        return False

    db = mongo.client[mongo.db_name]
    docs = list(db["performances_bancaires_clean"].find({}))
    mongo.close()

    if not docs:
        print("  ❌ Aucune donnée dans performances_bancaires_clean")
        return False

    df = pd.DataFrame(docs)
    for col in ["_id", "_cleaned_date"]:
        if col in df.columns:
            df = df.drop(col, axis=1)

    print(f"\n  {len(df)} documents chargés")

    # ── 1. Métadonnées géographiques ────────────────────────────────────────
    df["meta_Groupe"]    = df["Sigle"].map(lambda s: BANK_METADATA.get(s, DEFAULT_META)["Groupe"])
    df["meta_Type"]      = df["Sigle"].map(lambda s: BANK_METADATA.get(s, DEFAULT_META)["Type"])
    df["meta_Latitude"]  = df["Sigle"].map(lambda s: BANK_METADATA.get(s, DEFAULT_META)["Lat"])
    df["meta_Longitude"] = df["Sigle"].map(lambda s: BANK_METADATA.get(s, DEFAULT_META)["Lon"])
    print("  ✅ Métadonnées géographiques ajoutées")

    # ── 2. Calcul des ratios financiers ─────────────────────────────────────
    # Colonnes avec accents possibles
    bilan_col     = next((c for c in df.columns if "BILAN" in c), None)
    fp_col        = next((c for c in df.columns if "FONDS.PROPRE" in c), None)
    ressources_col= next((c for c in df.columns if "RESSOURCES" in c), None)
    emploi_col    = next((c for c in df.columns if c == "EMPLOI"), None)
    rn_col        = next((c for c in df.columns if "RESULTAT.NET" in c), None)
    pnb_col       = next((c for c in df.columns if "PRODUIT.NET.BANCAIRE" in c), None)
    charges_col   = next((c for c in df.columns if "CHARGES.GENERALES" in c), None)

    def to_num(col):
        if col and col in df.columns:
            return pd.to_numeric(df[col], errors="coerce")
        return pd.Series([np.nan] * len(df))

    BILAN       = to_num(bilan_col).replace(0, np.nan)
    FP          = to_num(fp_col).replace(0, np.nan)
    RESSOURCES  = to_num(ressources_col).replace(0, np.nan)
    RN          = to_num(rn_col)
    PNB         = to_num(pnb_col).replace(0, np.nan)
    CHARGES     = to_num(charges_col)

    df["R_SOLVABILITE"]       = (FP / BILAN * 100).round(2)
    df["R_LEVIER"]            = (FP / RESSOURCES * 100).round(2)
    df["R_ROE"]               = (RN / FP * 100).round(2)
    df["R_ROA"]               = (RN / BILAN * 100).round(2)
    df["R_COEFF_EXPLOITATION"] = (CHARGES / PNB * 100).round(2)

    # Nettoyer les infinis
    ratio_cols = [c for c in df.columns if c.startswith("R_")]
    df[ratio_cols] = df[ratio_cols].replace([np.inf, -np.inf], np.nan)

    print(f"  ✅ {len(ratio_cols)} ratios calculés : {ratio_cols}")

    # ── 3. Ordonner les colonnes ──────────────────────────────────────────
    # Colonnes de base (schéma CSV)
    base_cols = ["Sigle", "Goupe_Bancaire", "ANNEE"]
    data_cols = [c for c in CSV_COLUMNS if c in df.columns]
    meta_cols = ["meta_Groupe", "meta_Type", "meta_Latitude", "meta_Longitude"]
    ratio_cols_ordered = sorted([c for c in df.columns if c.startswith("R_")])
    source_cols = [c for c in df.columns if c.startswith("_")]

    final_order = base_cols + data_cols + meta_cols + ratio_cols_ordered + source_cols
    # Ajouter les colonnes restantes non listées
    remaining = [c for c in df.columns if c not in final_order]
    final_order += remaining

    df = df.reindex(columns=[c for c in final_order if c in df.columns])

    # ── 4. Sauvegarder ───────────────────────────────────────────────────
    mongo2 = MongoDBConnection(environment='dev')
    if not mongo2.connect():
        return False

    db2 = mongo2.client[mongo2.db_name]
    coll_p = db2["performances_bancaires_prod"]
    coll_p.drop()

    records = []
    for _, row in df.iterrows():
        r = clean_record(row.to_dict())
        r["_enriched_date"] = datetime.now()
        r["_app_version"] = "2.0"
        records.append(r)

    if records:
        coll_p.insert_many(records)
        coll_p.create_index([("Sigle", 1)])
        coll_p.create_index([("ANNEE", 1)])
        coll_p.create_index([("Goupe_Bancaire", 1)])
        print(f"  ✅ {len(records)} documents → DEV.performances_bancaires_prod")

    mongo2.close()

    # Rapport final
    print(f"\n  Résumé par banque et année :")
    for sigle in sorted(df["Sigle"].unique()):
        annees = sorted(df[df["Sigle"]==sigle]["ANNEE"].tolist())
        print(f"    {sigle:20s} → {annees}")

    return True


# ══════════════════════════════════════════════════════════════════════════════
# ÉTAPE 6 : MIGRATION DEV → PROD
# ══════════════════════════════════════════════════════════════════════════════

def step6_migrate_to_prod():
    header("ÉTAPE 6 — MIGRATION DEV → PROD")

    # Charger depuis DEV
    mongo_dev = MongoDBConnection(environment='dev')
    if not mongo_dev.connect():
        return False

    db_dev = mongo_dev.client[mongo_dev.db_name]
    data = list(db_dev["performances_bancaires_prod"].find({}))
    mongo_dev.close()

    if not data:
        print("  ❌ Aucune donnée dans DEV.performances_bancaires_prod")
        print("     Exécutez d'abord l'étape 5 (enrichissement)")
        return False

    print(f"\n  {len(data)} documents chargés depuis DEV")

    # Insérer dans PROD
    mongo_prod = MongoDBConnection(environment='prod')
    if not mongo_prod.connect():
        return False

    db_prod = mongo_prod.client[mongo_prod.db_name]
    coll_prod = db_prod["performances_bancaires_prod"]

    # Vider PROD
    deleted = coll_prod.delete_many({})
    print(f"  → {deleted.deleted_count} anciens documents PROD supprimés")

    # Préparer les documents
    for doc in data:
        if "_id" in doc:
            del doc["_id"]
        doc["_migrated_at"] = datetime.now()

    result = coll_prod.insert_many(data)

    # Créer les index PROD
    coll_prod.create_index([("Sigle", 1)])
    coll_prod.create_index([("ANNEE", 1)])
    coll_prod.create_index([("Goupe_Bancaire", 1)])
    coll_prod.create_index([("Sigle", 1), ("ANNEE", 1)])

    print(f"  ✅ {len(result.inserted_ids)} documents → PROD.performances_bancaires_prod")
    mongo_prod.close()

    # Vérification finale
    mongo_verify = MongoDBConnection(environment='prod')
    if mongo_verify.connect():
        db_v = mongo_verify.client[mongo_verify.db_name]
        count_prod = db_v["performances_bancaires_prod"].count_documents({})
        print(f"\n  🔍 Vérification PROD : {count_prod} documents confirmés")

        # Aperçu
        sample = list(db_v["performances_bancaires_prod"].find(
            {}, {"Sigle": 1, "ANNEE": 1, "BILAN": 1, "_id": 0}
        ).limit(5))
        print(f"  Aperçu :")
        for s in sample:
            print(f"    {s}")
        mongo_verify.close()

    return True


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

STEPS = {
    1: ("Ingestion CSV",          step1_ingest_csv),
    2: ("OCR PDF",                step2_ocr_pdf),
    3: ("Normalisation & Fusion", step3_normalize_merge),
    4: ("Nettoyage & Validation", step4_clean),
    5: ("Enrichissement & Ratios",step5_enrich),
    6: ("Migration DEV → PROD",   step6_migrate_to_prod),
}

def main():
    parser = argparse.ArgumentParser(description="Pipeline bancaire BCEAO")
    parser.add_argument("--step", type=int, choices=list(STEPS.keys()),
                        help="Exécuter uniquement une étape précise (1-6)")
    parser.add_argument("--from-step", type=int, choices=list(STEPS.keys()), default=1,
                        help="Démarrer depuis cette étape (défaut=1)")
    args = parser.parse_args()

    print(f"\n{'█'*70}")
    print(f"  PIPELINE BANCAIRE BCEAO — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'█'*70}")

    if args.step:
        steps_to_run = [args.step]
    else:
        steps_to_run = list(range(args.from_step, 7))

    results = {}
    for step_num in steps_to_run:
        name, func = STEPS[step_num]
        try:
            ok = func()
            results[step_num] = ok
            if not ok:
                print(f"\n❌ Étape {step_num} ({name}) échouée. Pipeline arrêté.")
                break
        except Exception as e:
            import traceback
            print(f"\n❌ Erreur dans l'étape {step_num} ({name}) :")
            traceback.print_exc()
            results[step_num] = False
            break

    # Bilan final
    print(f"\n{'█'*70}")
    print("  BILAN DU PIPELINE")
    print(f"{'█'*70}")
    for step_num, ok in results.items():
        name = STEPS[step_num][0]
        icon = "✅" if ok else "❌"
        print(f"  {icon} Étape {step_num} — {name}")

    all_ok = all(results.values())
    if all_ok and len(results) == len(steps_to_run):
        print(f"\n🎉 PIPELINE TERMINÉ AVEC SUCCÈS !")
    else:
        print(f"\n⚠️  PIPELINE TERMINÉ AVEC DES ERREURS")
    print(f"{'█'*70}\n")


if __name__ == "__main__":
    main()
