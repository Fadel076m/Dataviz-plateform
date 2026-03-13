"""
robust_ocr.py — Extraction PDF BCEAO alignée EXACTEMENT sur le schéma base_senegal.csv

POINTS CLÉS :
- Contexte de 5 pages autour de chaque page pour détecter la banque et le pays
- Détection Sénégal renforcée : via liste explicite des banques sénégalaises
- BANK_MAPPING étendu pour couvrir les 27-28 banques du Sénégal
- Fusion INTELLIGENTE pour 2021 (présent dans 2 PDFs) : champ par champ
- Validation post-extraction : taux de couverture par colonne
- Rapport qualité : quality_report.json dans data/

COLONNES CIBLES (ordre exact du CSV) :
    Sigle, Goupe_Bancaire, ANNEE,
    EMPLOI, BILAN, RESSOURCES, FONDS.PROPRE,
    EFFECTIF, AGENCE, COMPTE,
    INTERETS.ET.PRODUITS.ASSIMILES, NTERETS.ET.CHARGES.ASSIMILEES,
    REVENUS.DES.TITRES.A.REVENU.VARIABLE,
    COMMISSIONS.(PRODUITS), COMMISSIONS.(CHARGES),
    GAINS.OU.PERTES.NETS.SUR.OPERATIONS.DES.PORTEFEUILLES.DE.NEGOCIATION,
    GAINS.OU.PERTES.NETS.SUR.OPERATIONS.DES.PORTEFEUILLES.DE.PLACEMENT.ET.ASSIMILES,
    AUTRES.PRODUITS.D'EXPLOITATION.BANCAIRE, AUTRES.CHARGES.D'EXPLOITATION.BANCAIRE,
    PRODUIT.NET.BANCAIRE, SUBVENTIONS.D'INVESTISSEMENT,
    CHARGES.GENERALES.D'EXPLOITATION,
    DOTATIONS.AUX.AMORTISSEMENTS.ET.AUX.DEPRECIATIONS.DES.IMMOBILISATIONS.INCORPORELLES.ET.CORPORELLES,
    RESULTAT.BRUT.D'EXPLOITATION, COÛT.DU.RISQUE, RESULTAT.D'EXPLOITATION,
    GAINS.OU.PERTES.NETS.SUR.ACTIFS.IMMOBILISES, RESULTAT.AVANT.IMPÔT,
    IMPÔTS.SUR.LES.BENEFICES, RESULTAT.NET
"""

import pdfplumber
import pandas as pd
import numpy as np
import re
import json
import argparse
from pathlib import Path
import sys
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.database import MongoDBConnection

# ── Chemins ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
PDF_DIR  = BASE_DIR / "data" / "pdf"
DATA_DIR = BASE_DIR / "data"

# ── Colonnes finales dans l'ordre EXACT du CSV ────────────────────────────────
CSV_COLUMNS_INTERNAL = [
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
    "RESULTAT.D'EXPLOITATION",
    "GAINS.OU.PERTES.NETS.SUR.ACTIFS.IMMOBILISES",
    "RESULTAT.AVANT.IMPOT",
    "IMPOTS.SUR.LES.BENEFICES",
    "RESULTAT.NET",
]

# Mapping interne → nom exact CSV (avec accents)
COL_RENAME_TO_CSV = {
    "COUT.DU.RISQUE":           "COÛT.DU.RISQUE",
    "RESULTAT.AVANT.IMPOT":    "RESULTAT.AVANT.IMPÔT",
    "IMPOTS.SUR.LES.BENEFICES": "IMPÔTS.SUR.LES.BENEFICES",
}

# ── BANK_MAPPING complet (27-28 banques Sénégal) ─────────────────────────────
# Toutes les variantes de noms rencontrées dans les PDF BCEAO → Sigle unifié
BANK_MAPPING = {
    # CBAO / Attijariwafa
    "COMPAGNIE BANCAIRE DE L'AFRIQUE OCCIDENTALE": "CBAO",
    "C.B.A.O": "CBAO", "CBAO": "CBAO",
    # SGBS / Société Générale
    "SOCIETE GENERALE SENEGAL": "SGBS",
    "SOCIETE GENERALE DE BANQUES AU SENEGAL": "SGBS",
    "SOCIETE GENERALE DE BANQUES": "SGBS",
    "SGBS": "SGBS", "SGSN": "SGBS",
    # BICIS
    "BICIS": "BICIS",
    "BANQUE INTERNATIONALE POUR LE COMMERCE ET L'INDUSTRIE AU SENEGAL": "BICIS",
    # ECOBANK
    "ECOBANK SENEGAL": "ECOBANK", "ECOBANK": "ECOBANK",
    # BOA
    "BANK OF AFRICA SENEGAL": "BOA", "BANK OF AFRICA": "BOA",
    "BOA SENEGAL": "BOA", "BOA": "BOA",
    # BIS — Banque Islamique du Sénégal
    "BANQUE ISLAMIQUE DU SENEGAL": "BIS", "BANQUE ISLAMIQUE": "BIS", "BIS": "BIS",
    # UBA
    "UNITED BANK FOR AFRICA": "UBA", "U.B.A": "UBA",
    "UBA": "UBA", "UBA-SENEGAL": "UBA", "UBA SENEGAL": "UBA",
    # BHS — Banque de l'Habitat du Sénégal
    "BANQUE DE L'HABITAT DU SENEGAL": "BHS", "B.H.S": "BHS", "BHS": "BHS",
    # CDS — Crédit du Sénégal
    "CREDIT DU SENEGAL": "CDS", "CDS": "CDS",
    # BNDE — Banque Nationale pour le Développement Économique
    "BANQUE NATIONALE POUR LE DEVELOPPEMENT ECONOMIQUE": "BNDE",
    "B.N.D.E": "BNDE", "BNDE": "BNDE",
    # CITIBANK
    "CITIBANK SENEGAL": "CITIBANK", "CITIBANK": "CITIBANK",
    # NSIA Banque
    "NSIA BANQUE SENEGAL": "NSIA", "NSIA BANQUE": "NSIA",
    "NSIA": "NSIA",
    # ORABANK
    "ORABANK SENEGAL": "ORABANK", "ORABANK": "ORABANK",
    # BGFI Bank
    "BGFI BANK SENEGAL": "BGFI", "BGFI BANK": "BGFI",
    "BGFIBANK": "BGFI", "BGFI": "BGFI",
    # BDK — Banque De Kédougou / Banque de Développement du Kédougou
    "BDK": "BDK",
    # CBI — Coris Bank International
    "CORIS BANK INTERNATIONAL SENEGAL": "CBI",
    "CORIS BANK": "CBI", "CBI": "CBI",
    # BSIC
    "BANQUE SAHELO-SAHARIENNE POUR L'INVESTISSEMENT ET LE COMMERCE": "BSIC",
    "B.S.I.C": "BSIC", "BSIC": "BSIC",
    # FBNBANK
    "FIRST BANK OF NIGERIA": "FBNBANK",
    "FBN BANK": "FBNBANK", "FBNBANK": "FBNBANK",
    # BRM — Banque Régionale de Marchés
    "BANQUE REGIONALE DE MARCHES": "BRM",
    "B.R.M": "BRM", "BRM": "BRM", "B.R.M.": "BRM",
    # BAS — Banque Atlantique Sénégal
    "BANQUE ATLANTIQUE SENEGAL": "BAS", "BANQUE ATLANTIQUE": "BAS", "BAS": "BAS",
    # LBO
    "LA BANQUE D'OMAN DU SENEGAL": "LBO", "LBO": "LBO",
    # LBA — La Banque Agricole
    "LA BANQUE AGRICOLE": "LBA", "BANQUE AGRICOLE": "LBA", "LBA": "LBA",
    # BCIM
    "BANQUE COMMERCIALE INTERNATIONALE MAROCO-IVOIRIENNE": "BCIM",
    "BCIM": "BCIM",
    # BOP — Banque de l'OMOA
    "BANQUE DE L'OMOA": "BOP", "BOP": "BOP",
    # BOS — Banque de l'Ouest et du Sud
    "BANQUE DE L'OUEST ET DU SUD": "BOS", "BOS": "BOS",
    # BIMAO — Banque Islamique de Mauritanie
    "BIMAO": "BIMAO",
    # CMB — Crédit Mutuel
    "CREDIT MUTUEL SENEGAL": "CMB", "CREDIT MUTUEL DU SENEGAL": "CMB", "CMB": "CMB",
    # LOCAFRIQUE
    "LOCAFRIQUE": "LOCAFRIQUE",
    # ALIOS Finance
    "ALIOS FINANCE SENEGAL": "ALIOS", "ALIOS FINANCE": "ALIOS", "ALIOS": "ALIOS",
    # COFINA
    "COFINA SENEGAL": "COFINA", "COFINA": "COFINA",
    # FINAO / La Finao
    "LA FINAO": "FINAO", "FINAO": "FINAO",
    # DSB — Diamond Bank Sénégal (devient Access Bank)
    "DIAMOND BANK SENEGAL": "DSB", "DSB": "DSB",
    "ACCESS BANK SENEGAL": "ACCESS", "ACCESS BANK": "ACCESS",
}

# Liste des sigles CONNUS comme banques sénégalaises
# → Si la page contient ce sigle, elle est forcément sénégalaise
SIGLES_SENEGAL = set(BANK_MAPPING.values())

# ── Mapping libellés PDF → colonnes internes ──────────────────────────────────
LABEL_TO_COLUMN = {
    # Bilan
    "TOTAL DE L'ACTIF": "BILAN", "TOTAL DU PASSIF": "BILAN",
    "TOTAL ACTIF": "BILAN", "TOTAL BILAN": "BILAN",
    "TOTAL PASSIF": "BILAN", "TOTAL GENERAL ACTIF": "BILAN",
    "TOTAL GENERAL PASSIF": "BILAN",
    # Emplois / Ressources
    "CREANCES SUR LA CLIENTELE": "EMPLOI",
    "CREDITS A LA CLIENTELE": "EMPLOI",
    "PRETS ET CREANCES SUR LA CLIENTELE": "EMPLOI",
    "DETTES ENVERS LA CLIENTELE": "RESSOURCES",
    "DEPOTS DE LA CLIENTELE": "RESSOURCES",
    "DETTES A L'EGARD DE LA CLIENTELE": "RESSOURCES",
    "DETTES A L EGARD DE LA CLIENTELE": "RESSOURCES",
    "RESSOURCES CLIENTELE": "RESSOURCES",
    # Fonds propres
    "CAPITAUX PROPRES": "FONDS.PROPRE",
    "FONDS PROPRES": "FONDS.PROPRE",
    "TOTAL FONDS PROPRES": "FONDS.PROPRE",
    "TOTAL DES CAPITAUX PROPRES": "FONDS.PROPRE",
    "CAPITAUX PROPRES ET RESSOURCES ASSIMILEES": "FONDS.PROPRE",
    # Réseau
    "NOMBRE D'AGENCES": "AGENCE", "NOMBRE AGENCE": "AGENCE",
    "AGENCES": "AGENCE", "GUICHETS": "AGENCE", "POINTS DE VENTE": "AGENCE",
    "EFFECTIF": "EFFECTIF", "EMPLOYES": "EFFECTIF",
    "NOMBRE D'EMPLOYES": "EFFECTIF", "NOMBRE DE SALARIES": "EFFECTIF",
    "PERSONNEL": "EFFECTIF",
    "NOMBRE DE COMPTES": "COMPTE", "COMPTES OUVERTS": "COMPTE",
    "COMPTES CLIENTS": "COMPTE",
    # Compte de résultat
    "INTERETS ET PRODUITS ASSIMILES": "INTERETS.ET.PRODUITS.ASSIMILES",
    "PRODUITS D'INTERETS ET ASSIMILES": "INTERETS.ET.PRODUITS.ASSIMILES",
    "INTERETS ET CHARGES ASSIMILES": "NTERETS.ET.CHARGES.ASSIMILEES",
    "CHARGES D'INTERETS ET ASSIMILEES": "NTERETS.ET.CHARGES.ASSIMILEES",
    "REVENUS DES TITRES A REVENU VARIABLE": "REVENUS.DES.TITRES.A.REVENU.VARIABLE",
    "DIVIDENDES ET REVENUS ASSIMILES": "REVENUS.DES.TITRES.A.REVENU.VARIABLE",
    "COMMISSIONS PRODUITS": "COMMISSIONS.(PRODUITS)",
    "COMMISSIONS SUR PRESTATIONS DE SERVICES PRODUITS": "COMMISSIONS.(PRODUITS)",
    "COMMISSIONS CHARGES": "COMMISSIONS.(CHARGES)",
    "COMMISSIONS SUR PRESTATIONS DE SERVICES CHARGES": "COMMISSIONS.(CHARGES)",
    "GAINS NETS SUR PORTEFEUILLES DE NEGOCIATION": "GAINS.OU.PERTES.NETS.SUR.OPERATIONS.DES.PORTEFEUILLES.DE.NEGOCIATION",
    "GAINS OU PERTES NETS SUR PORTEFEUILLE DE NEGOCIATION": "GAINS.OU.PERTES.NETS.SUR.OPERATIONS.DES.PORTEFEUILLES.DE.NEGOCIATION",
    "GAINS OU PERTES NETS SUR OPERATIONS DES PORTEFEUILLES DE NEGOCIATION": "GAINS.OU.PERTES.NETS.SUR.OPERATIONS.DES.PORTEFEUILLES.DE.NEGOCIATION",
    "GAINS NETS SUR PORTEFEUILLES DE PLACEMENT": "GAINS.OU.PERTES.NETS.SUR.OPERATIONS.DES.PORTEFEUILLES.DE.PLACEMENT.ET.ASSIMILES",
    "GAINS OU PERTES NETS SUR PORTEFEUILLE DE PLACEMENT": "GAINS.OU.PERTES.NETS.SUR.OPERATIONS.DES.PORTEFEUILLES.DE.PLACEMENT.ET.ASSIMILES",
    "GAINS OU PERTES NETS SUR OPERATIONS DES PORTEFEUILLES DE PLACEMENT": "GAINS.OU.PERTES.NETS.SUR.OPERATIONS.DES.PORTEFEUILLES.DE.PLACEMENT.ET.ASSIMILES",
    "AUTRES PRODUITS D'EXPLOITATION BANCAIRE": "AUTRES.PRODUITS.D'EXPLOITATION.BANCAIRE",
    "AUTRES CHARGES D'EXPLOITATION BANCAIRE": "AUTRES.CHARGES.D'EXPLOITATION.BANCAIRE",
    "PRODUIT NET BANCAIRE": "PRODUIT.NET.BANCAIRE",
    "PNB": "PRODUIT.NET.BANCAIRE",
    "PRODUITS NET BANCAIRE": "PRODUIT.NET.BANCAIRE",
    "SUBVENTIONS D'INVESTISSEMENT": "SUBVENTIONS.D'INVESTISSEMENT",
    "CHARGES GENERALES D'EXPLOITATION": "CHARGES.GENERALES.D'EXPLOITATION",
    "FRAIS GENERAUX": "CHARGES.GENERALES.D'EXPLOITATION",
    "DOTATIONS AUX AMORTISSEMENTS ET AUX DEPRECIATIONS": "DOTATIONS.AUX.AMORTISSEMENTS.ET.AUX.DEPRECIATIONS.DES.IMMOBILISATIONS.INCORPORELLES.ET.CORPORELLES",
    "DOTATIONS AUX AMORTISSEMENTS": "DOTATIONS.AUX.AMORTISSEMENTS.ET.AUX.DEPRECIATIONS.DES.IMMOBILISATIONS.INCORPORELLES.ET.CORPORELLES",
    "DEPRECIATIONS DES IMMOBILISATIONS": "DOTATIONS.AUX.AMORTISSEMENTS.ET.AUX.DEPRECIATIONS.DES.IMMOBILISATIONS.INCORPORELLES.ET.CORPORELLES",
    "RESULTAT BRUT D'EXPLOITATION": "RESULTAT.BRUT.D'EXPLOITATION",
    "COUT DU RISQUE": "COUT.DU.RISQUE", "COÛT DU RISQUE": "COUT.DU.RISQUE",
    "RESULTAT D'EXPLOITATION": "RESULTAT.D'EXPLOITATION",
    "GAINS OU PERTES SUR ACTIFS IMMOBILISES": "GAINS.OU.PERTES.NETS.SUR.ACTIFS.IMMOBILISES",
    "GAINS NETS SUR ACTIFS IMMOBILISES": "GAINS.OU.PERTES.NETS.SUR.ACTIFS.IMMOBILISES",
    "RESULTAT AVANT IMPOT": "RESULTAT.AVANT.IMPOT",
    "RESULTAT AVANT IMPOTS": "RESULTAT.AVANT.IMPOT",
    "RESULTAT NET AVANT IMPOTS": "RESULTAT.AVANT.IMPOT",
    "IMPOTS SUR LES BENEFICES": "IMPOTS.SUR.LES.BENEFICES",
    "IMPOT SUR LES SOCIETES": "IMPOTS.SUR.LES.BENEFICES",
    "IMPOTS SUR LE BENEFICE": "IMPOTS.SUR.LES.BENEFICES",
    "RESULTAT NET": "RESULTAT.NET",
    "BENEFICE NET": "RESULTAT.NET",
    "RESULTAT DE L'EXERCICE": "RESULTAT.NET",
}


# ── Fonctions utilitaires ─────────────────────────────────────────────────────

def normalize_text(t: str) -> str:
    """Majuscules + suppression accents pour comparaison robuste."""
    if not t:
        return ""
    t = str(t).upper()
    accents = [
        ("É","E"),("È","E"),("Ê","E"),("Ë","E"),
        ("À","A"),("Â","A"),("Ä","A"),
        ("Î","I"),("Ï","I"),("Ô","O"),("Ö","O"),
        ("Ù","U"),("Û","U"),("Ü","U"),
        ("Ç","C"),("Œ","OE"),("Æ","AE"),
    ]
    for src, dst in accents:
        t = t.replace(src, dst)
    return re.sub(r'\s+', ' ', t).strip()


def parse_amount(raw: str):
    """Convertit un texte brut en entier (millions FCFA). Retourne None si non convertible."""
    if not raw:
        return None
    s = str(raw).strip()
    if s in ("", "-", "–", "—", "N/A", "n/a", "None", "nan", "*", "nd", "ND"):
        return None
    # Supprimer espaces insécables
    s = re.sub(r"[\s\xa0\u202f]", "", s)
    # Supprimer séparateurs de milliers
    s = re.sub(r"[,\.](?=\d{3}(\D|$))", "", s)
    # Garder chiffres et signe
    s = re.sub(r"[^0-9\-]", "", s)
    if not s or s == "-":
        return None
    try:
        val = int(s)
        if abs(val) > 10_000_000:
            return None
        return val
    except ValueError:
        return None


def detect_bank(text: str) -> str | None:
    """Identifie le sigle de la banque depuis le texte brut d'une page."""
    t = normalize_text(text)
    # Tri par longueur décroissante (plus spécifique en premier)
    for pattern in sorted(BANK_MAPPING.keys(), key=len, reverse=True):
        if normalize_text(pattern) in t:
            return BANK_MAPPING[pattern]
    return None


def is_senegal_context(context_text: str, detected_bank: str | None) -> bool:
    """
    Détermine si le contexte de la page concerne le Sénégal.
    Double logique :
    1. Le contexte contient explicitement SENEGAL ou DAKAR
    2. OU la banque détectée est une banque sénégalaise connue
    """
    t = normalize_text(context_text)
    if "SENEGAL" in t or "DAKAR" in t:
        return True
    if detected_bank and detected_bank in SIGLES_SENEGAL:
        return True
    return False


def map_label(raw_label: str) -> str | None:
    """Fait correspondre un libellé PDF à une colonne interne."""
    label = normalize_text(raw_label)
    for key, col in LABEL_TO_COLUMN.items():
        if normalize_text(key) == label:
            return col
    for key, col in LABEL_TO_COLUMN.items():
        if normalize_text(key) in label:
            return col
    return None


def extract_years_from_table(df: pd.DataFrame) -> dict:
    """Cherche les années (20xx) dans les 4 premières lignes. Retourne {col_idx: annee}."""
    found = {}
    for r in range(min(4, len(df))):
        for c in range(len(df.columns)):
            val = str(df.iloc[r, c] or "")
            m = re.search(r"\b(20\d{2})\b", val)
            if m:
                yr = int(m.group(1))
                if 2010 <= yr <= 2030:
                    found[c] = yr
    return found


def smart_merge_field(val_new, val_existing):
    """
    Fusion intelligente champ par champ.
    Préfère la valeur non-nulle et non-zéro.
    En cas de conflit (deux valeurs réelles différentes), on garde la plus récente (val_new).
    """
    if val_new is None or (isinstance(val_new, (int, float)) and val_new == 0):
        return val_existing if val_existing is not None else val_new
    return val_new


# ── Extracteur principal ──────────────────────────────────────────────────────

class PDFExtractor:
    """
    Extrait les données financières des PDF BCEAO.
    Aligne strictement sur le schéma de base_senegal.csv.
    Gère la fusion intelligente pour les années présentes dans plusieurs PDF.
    """

    def __init__(self, environment='dev'):
        self.mongo = MongoDBConnection(environment=environment)

    def extract_file(self, pdf_path: Path, default_years: list,
                     page_range: tuple = None, force_senegal: bool = False) -> dict:
        """
        Extrait toutes les données d'un PDF.
        Utilise une fenêtre de contexte de 5 pages (avant et après) pour la détection.
        Retourne un dict : { (sigle, annee): {col: val} }
        """
        print(f"\n[OCR] {pdf_path.name}")
        bank_year_data: dict[tuple, dict] = {}

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            start_page = max(0, page_range[0]) if page_range else 0
            end_page = min(total_pages, page_range[1]) if page_range else total_pages

            print(f"  -> Pages {start_page + 1} à {end_page} sur {total_pages} total")

            current_bank = None

            for i in range(start_page, end_page):
                if i % 20 == 0:
                    print(f"  ... Page {i+1}/{total_pages}")

                page = pdf.pages[i]

                # ── Contexte : 5 pages autour de la page courante ──────────
                context_window = range(max(0, i - 5), min(total_pages, i + 6))
                context_text = ""
                for idx in context_window:
                    context_text += (pdf.pages[idx].extract_text() or "") + " "

                page_text = page.extract_text() or ""

                # ── Détection de la banque ─────────────────────────────────
                detected = detect_bank(page_text)

                # Mise à jour de la banque courante si on en détecte une
                if detected:
                    ctx_ok = is_senegal_context(context_text, detected) or force_senegal
                    if ctx_ok:
                        if detected != current_bank:
                            print(f"    [Detect] Banque -> {detected} (p.{i+1})")
                        current_bank = detected

                if current_bank is None:
                    continue

                # ── Extraction des tableaux ────────────────────────────────
                tables = page.extract_tables() or []
                for table in tables:
                    if not table or len(table) < 2:
                        continue

                    df = pd.DataFrame(table)
                    if df.empty or len(df.columns) < 2:
                        continue

                    year_map = extract_years_from_table(df)

                    # Colonnes numériques
                    numeric_col_positions = []
                    for c in range(1, len(df.columns)):
                        sample = df.iloc[:, c].dropna().astype(str).tolist()
                        if any(re.search(r"\d+", v) for v in sample[:15]):
                            numeric_col_positions.append(c)

                    if not numeric_col_positions:
                        continue

                    # Mapping colonne → année
                    col_to_year = {}
                    for pos_idx, col_idx in enumerate(numeric_col_positions):
                        if col_idx in year_map:
                            col_to_year[col_idx] = year_map[col_idx]
                        elif pos_idx < len(default_years):
                            col_to_year[col_idx] = default_years[pos_idx]

                    for col_idx, year in col_to_year.items():
                        pending_labels = []
                        for r in range(len(df)):
                            l_cell = str(df.iloc[r, 0] or "").strip()
                            if (not l_cell or l_cell.upper() == "NONE") and len(df.columns) > 1:
                                if col_idx != 1:
                                    maybe_l = str(df.iloc[r, 1] or "").strip()
                                    if maybe_l and parse_amount(maybe_l) is None:
                                        l_cell = maybe_l

                            v_cell = str(df.iloc[r, col_idx] or "").strip()
                            l_lines = l_cell.split("\n")
                            v_lines = v_cell.split("\n")

                            # Cas spécial : distribution horizontale
                            if len(numeric_col_positions) == 1 and len(l_lines) == 1:
                                sub_vals = re.split(r' {2,}', v_cell)
                                if len(sub_vals) >= 2:
                                    col_name = map_label(l_cell)
                                    if col_name:
                                        for sub_idx, sub_val in enumerate(sub_vals):
                                            if sub_idx < len(default_years):
                                                y_sub = default_years[sub_idx]
                                                val = parse_amount(sub_val)
                                                if val is not None:
                                                    key = (current_bank, y_sub)
                                                    existing = bank_year_data.get(key, {}).get(col_name)
                                                    new_val = smart_merge_field(val, existing)
                                                    bank_year_data.setdefault(key, {})[col_name] = new_val
                                    continue

                            pending_labels.extend(l_lines)
                            for v_str in v_lines:
                                if not pending_labels:
                                    break
                                l_str = pending_labels.pop(0).strip()
                                if not l_str:
                                    continue
                                col_name = map_label(l_str)
                                if col_name:
                                    val = parse_amount(v_str)
                                    if val is not None:
                                        key = (current_bank, year)
                                        existing = bank_year_data.get(key, {}).get(col_name)
                                        merged = smart_merge_field(val, existing)
                                        bank_year_data.setdefault(key, {})[col_name] = merged

        return bank_year_data

    def run(self, page_range: tuple = None, save: bool = True,
            target_file: str = None, force_senegal: bool = False):
        """
        Lance l'extraction sur tous les PDF ou un fichier spécifique.
        Fusion intelligente champ par champ pour les années partagées entre PDF.
        """
        if target_file:
            pdf_files = [Path(target_file)]
        else:
            pdf_files = sorted(PDF_DIR.rglob("*.pdf"))

        if not pdf_files:
            print("[ERR] Aucun PDF trouvé dans", PDF_DIR)
            return []

        print(f"\n{'='*70}")
        print(f"EXTRACTION OCR — {len(pdf_files)} fichier(s) PDF")
        print(f"{'='*70}")

        # Traiter les PDF dans l'ordre chronologique (le plus récent en dernier
        # pour que sa valeur écrase les années partagées si elle est plus complète)
        all_data: dict[tuple, dict] = {}

        for pdf_path in pdf_files:
            if not pdf_path.exists():
                print(f"[ERR] Fichier non trouvé : {pdf_path}")
                continue

            name_lower = pdf_path.name.lower()
            parent_lower = str(pdf_path.parent).lower()

            # Déterminer les années par défaut selon le nom / dossier du PDF
            if "2019" in name_lower or "2019" in parent_lower:
                default_years = [2019, 2020, 2021]
                print(f"\n  → PDF identifié : Rapport 2019-2021 (années par défaut : {default_years})")
            elif "2021" in name_lower or "2021" in parent_lower:
                default_years = [2021, 2022, 2023]
                print(f"\n  → PDF identifié : Rapport 2021-2023 (années par défaut : {default_years})")
            else:
                default_years = [2021, 2022, 2023]
                print(f"\n  → PDF non identifié : années par défaut {default_years}")

            file_data = self.extract_file(
                pdf_path, default_years,
                page_range=page_range,
                force_senegal=force_senegal
            )

            # ── Fusion intelligente champ par champ ────────────────────────
            for key, cols in file_data.items():
                if key not in all_data:
                    all_data[key] = dict(cols)
                else:
                    # Fusionner champ par champ : compléter les vides
                    for col, val in cols.items():
                        existing = all_data[key].get(col)
                        all_data[key][col] = smart_merge_field(val, existing)

        if not all_data:
            print("[ERR] Aucune donnée extraite.")
            return []

        # ── Construction du DataFrame final ───────────────────────────────
        rows = []
        for (sigle, annee), cols in all_data.items():
            row = {"Sigle": sigle, "ANNEE": annee}
            row.update(cols)
            rows.append(row)

        df = pd.DataFrame(rows)

        # S'assurer que toutes les colonnes du schéma sont présentes
        for col in CSV_COLUMNS_INTERNAL:
            if col not in df.columns:
                df[col] = None

        # Dédupliquer (sécurité)
        df = df.groupby(["Sigle", "ANNEE"], as_index=False).first()

        # Ordonner colonnes
        ordered_cols = ["Sigle", "ANNEE"] + CSV_COLUMNS_INTERNAL
        df = df.reindex(columns=ordered_cols)

        # Renommer les colonnes avec accents (pour correspondance exacte CSV)
        df = df.rename(columns=COL_RENAME_TO_CSV)

        # ── Rapport de qualité ─────────────────────────────────────────────
        quality_report = self._generate_quality_report(df)

        print(f"\n{'='*70}")
        print(f"RÉSUMÉ DE L'EXTRACTION")
        print(f"  Total lignes    : {len(df)}")
        print(f"  Banques uniques : {df['Sigle'].nunique()}")
        print(f"  Sigles          : {sorted(df['Sigle'].unique())}")
        print(f"  Années          : {sorted(df['ANNEE'].unique())}")
        print(f"  Couverture cols clés : {quality_report['coverage_pct']:.1f}%")

        if df['Sigle'].nunique() < 15:
            print(f"\n  [WARN] ATTENTION : Seulement {df['Sigle'].nunique()} banques détectées (attendu >= 15)")
            print(f"     -> Essayez avec --force-senegal pour désactiver le filtre pays")

        if save:
            self.save_to_mongo(df)

        # Sauvegarder le rapport qualité
        report_path = DATA_DIR / "ocr_quality_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(quality_report, f, indent=2, ensure_ascii=False)
        print(f"\n  Rapport qualité sauvegardé : {report_path}")

        return df.to_dict("records")

    def _generate_quality_report(self, df: pd.DataFrame) -> dict:
        """Génère un rapport de qualité post-extraction."""
        key_cols = ["BILAN", "FONDS.PROPRE", "RESULTAT.NET", "RESSOURCES",
                    "PRODUIT.NET.BANCAIRE", "EMPLOI"]
        coverage = {}
        for col in key_cols:
            if col in df.columns:
                n_valid = df[col].notna().sum() + (df[col] != 0).sum()
                coverage[col] = round(df[col].notna().mean() * 100, 1)
        
        avg_coverage = sum(coverage.values()) / len(coverage) if coverage else 0

        return {
            "date_extraction": datetime.now().isoformat(),
            "nb_lignes": len(df),
            "nb_banques": df['Sigle'].nunique(),
            "sigles": sorted(df['Sigle'].unique()),
            "annees": sorted(df['ANNEE'].unique()),
            "coverage_pct": round(avg_coverage, 1),
            "coverage_par_colonne": coverage,
        }

    def save_to_mongo(self, df: pd.DataFrame):
        """Sauvegarde dans MongoDB DEV via upsert (Sigle, ANNEE, _type)."""
        if not self.mongo.connect():
            print("[ERR] Connexion MongoDB échouée")
            return

        coll = self.mongo.get_collection()
        records = df.to_dict("records")

        upserted, inserted = 0, 0
        for r in records:
            r["_type"] = "pdf_extraction"
            r["_import_date"] = datetime.now()
            # Nettoyer les NaN
            for k, v in list(r.items()):
                if isinstance(v, float) and np.isnan(v):
                    r[k] = None

            result = coll.update_one(
                {"Sigle": r["Sigle"], "ANNEE": r["ANNEE"], "_type": "pdf_extraction"},
                {"$set": r},
                upsert=True
            )
            if result.upserted_id:
                inserted += 1
            else:
                upserted += 1

        print(f"  [OK] {inserted} nouveaux docs insérés, {upserted} mis à jour dans DEV.performances_bancaires")
        self.mongo.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extraction OCR BCEAO — Aligné sur schéma CSV")
    parser.add_argument("--start", type=int, help="Page de début (0-indexed)")
    parser.add_argument("--end",   type=int, help="Page de fin")
    parser.add_argument("--file",  type=str, help="Fichier PDF spécifique")
    parser.add_argument("--force-senegal", action="store_true",
                        help="Désactiver le filtre Sénégal (traiter toutes les banques du PDF)")
    parser.add_argument("--no-save", action="store_true", help="Ne pas sauvegarder en DB")
    args = parser.parse_args()

    extractor = PDFExtractor(environment='dev')
    page_range = None
    if args.start is not None and args.end is not None:
        page_range = (args.start, args.end)

    extractor.run(
        page_range=page_range,
        save=not args.no_save,
        target_file=args.file,
        force_senegal=args.force_senegal
    )
