"""
audit_to_file.py - Ecrit l'audit dans un fichier .txt lisible
"""
import sys
import io
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import numpy as np
from config.database import MongoDBConnection

OUT = Path(__file__).resolve().parent.parent / "audit_result.txt"

lines = []

def p(txt=""):
    lines.append(str(txt))

SEP = "=" * 70

def pct_bar(pct):
    filled = int(pct // 10)
    return "#" * filled + "." * (10 - filled)

def audit_env(env):
    p()
    p(SEP)
    p("  BASE : banque_{}".format(env.upper()))
    p(SEP)
    mongo = MongoDBConnection(environment=env)
    if not mongo.connect():
        p("  CONNEXION ECHOUEE")
        return
    db = mongo.client[mongo.db_name]
    collections = sorted(db.list_collection_names())
    p("\n  Collections : {}".format(collections))

    for col_name in collections:
        coll = db[col_name]
        count = coll.count_documents({})
        p("  {:<52} {:5d} docs".format(col_name, count))

    target = "performances_bancaires_prod"
    if target not in collections:
        p("\n  [!] Collection '{}' ABSENTE".format(target))
        mongo.close()
        return

    coll = db[target]
    docs = list(coll.find({}, {"_id": 0}))
    if not docs:
        p("\n  [VIDE] {}".format(target))
        mongo.close()
        return

    df = pd.DataFrame(docs)
    p("\n  Colonnes totales : {}".format(len(df.columns)))
    p("  Lignes totales   : {}".format(len(df)))
    p("  Banques ({})     : {}".format(df["Sigle"].nunique(), sorted(df["Sigle"].unique())))
    p("  Annees           : {}".format(sorted(df["ANNEE"].unique())))

    p("\n  -- Distribution Banque x Annee --")
    try:
        pivot = df.groupby(["Sigle", "ANNEE"]).size().unstack(fill_value=0)
        p(pivot.to_string())
    except Exception as e:
        p("  Erreur pivot: {}".format(e))

    p("\n  -- Taux de remplissage > colonnes CSV cibles --")
    # Colonnes dans l'ordre exact du CSV
    all_csv_cols = [
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
        "COUT.DU.RISQUE",
        "COÛT.DU.RISQUE",
        "RESULTAT.D'EXPLOITATION",
        "GAINS.OU.PERTES.NETS.SUR.ACTIFS.IMMOBILISES",
        "RESULTAT.AVANT.IMPOT",
        "RESULTAT.AVANT.IMPÔT",
        "IMPOTS.SUR.LES.BENEFICES",
        "IMPÔTS.SUR.LES.BENEFICES",
        "RESULTAT.NET",
    ]
    seen = set()
    for col in all_csv_cols:
        if col in seen:
            continue
        seen.add(col)
        if col in df.columns:
            pct = df[col].notna().mean() * 100
            n_ok = int(df[col].notna().sum())
            icon = "[OK]" if pct > 70 else "[!] " if pct > 30 else "[X] "
            p("  {} {:<68} {} {:5.1f}% ({}/{})".format(
                icon, col, pct_bar(pct), pct, n_ok, len(df)))
        else:
            p("  [--] {:<68} ABSENTE".format(col))

    p("\n  -- Ratios calculés --")
    ratio_cols = sorted([c for c in df.columns if c.startswith("R_")])
    if ratio_cols:
        for r in ratio_cols:
            non_null = int(df[r].notna().sum())
            try:
                moy = df[r].mean()
                mx = df[r].max()
                mn = df[r].min()
                p("  {:<30} {:3d} vals  moy={:8.2f}  min={:8.2f}  max={:8.2f}".format(
                    r, non_null,
                    moy if pd.notna(moy) else 0,
                    mn if pd.notna(mn) else 0,
                    mx if pd.notna(mx) else 0
                ))
            except Exception:
                p("  {:<30} {:3d} vals".format(r, non_null))
    else:
        p("  Aucun ratio trouve")

    p("\n  -- Apercu donnees (trie par Sigle, ANNEE) --")
    cols_show = ["Sigle", "ANNEE", "Goupe_Bancaire", "BILAN", "EMPLOI", "RESSOURCES", "FONDS.PROPRE", "RESULTAT.NET"]
    cols_show = [c for c in cols_show if c in df.columns]
    try:
        p(df[cols_show].sort_values(["Sigle","ANNEE"]).to_string(index=False))
    except Exception as e:
        p("  Erreur: {}".format(e))

    p("\n  -- Verification colonnes manquantes vs CSV --")
    expected_cols = [
        "Sigle", "Goupe_Bancaire", "ANNEE",
        "EMPLOI", "BILAN", "RESSOURCES", "FONDS.PROPRE",
        "EFFECTIF", "AGENCE", "COMPTE",
        "INTERETS.ET.PRODUITS.ASSIMILES", "NTERETS.ET.CHARGES.ASSIMILEES",
        "REVENUS.DES.TITRES.A.REVENU.VARIABLE",
        "COMMISSIONS.(PRODUITS)", "COMMISSIONS.(CHARGES)",
        "PRODUIT.NET.BANCAIRE", "RESULTAT.NET",
    ]
    manquantes = [c for c in expected_cols if c not in df.columns]
    if manquantes:
        p("  COLONNES MANQUANTES : {}".format(manquantes))
    else:
        p("  Toutes les colonnes cles sont presentes [OK]")

    p("\n  -- Colonnes presentes dans la collection --")
    for c in sorted(df.columns):
        p("    {}".format(c))

    mongo.close()


audit_env("dev")
audit_env("prod")
p()
p(SEP)
p("  AUDIT COMPLET TERMINE")
p(SEP)

# Ecrire dans le fichier
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("Audit ecrit dans : {}".format(OUT))
