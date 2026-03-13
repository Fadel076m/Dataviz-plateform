# 🏦 Analyse Financière & Dashboard Bancaire — Sénégal

**Projet Data Engineering & Visualisation (Master 2 — ASHOKA)**

Pipeline ETL complet pour collecter, nettoyer et analyser les performances financières des banques au Sénégal (2015-2023), avec un Dashboard Interactif (Dash/Plotly).

---

## 🚀 Fonctionnalités Clés

### 1. Pipeline ETL Robuste (Architecture Médaillon Bronze → Silver → Gold)

- **Ingestion** : Import CSV historique (2015-2020) avec validation stricte des 30 colonnes
- **OCR** : Extraction des rapports triennaux BCEAO (PDF 2019-2021 et 2021-2023) avec détection robuste des banques sénégalaises (27-28 établissements)
- **Fusion Intelligente** : Pour 2021 (présent dans les deux rapports), fusion champ par champ
- **Nettoyage** : Détection outliers (méthode IQR), correction d'unités, validation qualité
- **Enrichissement** : Calcul de 5 ratios financiers (Solvabilité, ROE, ROA, Levier, Coeff. Exploitation), géolocalisation, promotion automatique DEV → PROD

### 2. Dashboard Stratégique (Dash)

- **KPIs Macro** : Bilan, Fonds Propres, Ressources, Réseau d'agences
- **Vue Macro** : Évolution sectorielle, parts de marché (donut), TCAM par groupe
- **Vue Comparative** : Classement des banques, score composite, positionnement TCAM
- **Vue Micro** : Radar ratios, historique, diagnostic vs secteur (pour toute banque)
- **Vue UBA** : Cas d'étude détaillé, jauges, recommandations stratégiques automatiques
- **Rapport PDF** : Export notebook → HTML → PDF

---

## 🗂️ Architecture Technique

```
3_banque_dashboard/
├── config/                     # 🔧 Configuration MongoDB
│   ├── database.py             # Connexion MongoDB Atlas (dev/prod)
│   └── pdf_urls.json           # Chemins des rapports BCEAO triennaux
│
├── data_engineering/           # ⚙️ Pipeline ETL
│   ├── ingestion.py            # Étape 1 : CSV → MongoDB (validation 30 colonnes)
│   ├── scraping.py             # Étape 2 : Téléchargement PDF BCEAO
│   ├── normalisation.py        # Étape 4 : Fusion intelligente CSV + PDF (priorité 3 niveaux)
│   ├── cleaning.py             # Étape 5 : Nettoyage IQR, validation qualité
│   └── enrichment.py          # Étape 6 : Ratios, GPS, promotion DEV → PROD
│
├── scripts/
│   ├── robust_ocr.py           # Étape 3 : OCR PDF BCEAO (27-28 banques, fusion 2021)
│   ├── pipeline_master.py      # Orchestrateur complet
│   └── audit_to_file.py        # Outils de diagnostic
│
├── dashboard/                  # 📊 Application Dash
│   ├── app.py                  # Point d'entrée
│   ├── core/                   # layout.py, callbacks.py, settings.py
│   ├── pages/                  # macro_view, comparative_view, micro_view, uba_focus
│   ├── components/             # cards.py (KPI cards, ratio cards)
│   └── utils/
│       ├── data.py             # Chargement MongoDB PROD (fallback DEV)
│       └── report/             # Génération rapport PDF
│
├── data/
│   ├── base_senegal.csv        # Données historiques 2015-2020 (22 banques, 30 colonnes)
│   ├── pdf/                    # Rapports BCEAO triennaux
│   │   ├── 2019-2021/          # bilans_2019_2021.pdf
│   │   └── 2021-2023/          # bilans_2021_2023.pdf
│   ├── ocr_quality_report.json # Rapport qualité OCR
│   └── pipeline_quality_report.json  # Rapport qualité pipeline final
└── requirements.txt
```

### Flux de Données (Data Lineage)

| Étape | Script | Collection MongoDB | Description |
|-------|--------|--------------------|-------------|
| **1. Bronze CSV** | `ingestion.py` | `performances_bancaires` | 22 banques, 2015-2020, 30 colonnes validées |
| **2. Bronze PDF** | `robust_ocr.py` | `performances_bancaires` | 27-28 banques, 2019-2023, fusion 2021 intelligente |
| **3. Silver** | `normalisation.py` + `cleaning.py` | `performances_bancaires_unified` → `performances_bancaires_clean` | Fusion 3 niveaux, outliers IQR |
| **4. Gold** | `enrichment.py` | `banque_prod.performances_bancaires_prod` | Ratios, GPS, prêt pour le dashboard |

---

## 📌 État d'Avancement

### ✅ Phase 1 : Architecture (Terminé)
- [x] Refonte modulaire du dashboard (4 vues, sidebar, tabs)
- [x] Isolation des vues : `macro`, `comparative`, `micro`, `uba_focus`

### ✅ Phase 2 : Pipeline ETL Qualité (Terminé)
- [x] Validation stricte des 30 colonnes du schéma CSV
- [x] OCR robuste couvrant 27-28 banques sénégalaises
- [x] Fusion intelligente champ par champ pour 2021
- [x] Détection outliers méthode IQR
- [x] Promotion automatique DEV → PROD après enrichissement

### ✅ Phase 3 : Dashboard Complet (Terminé)
- [x] Vue Macro (KPIs, donut, évolution, TCAM groupes)
- [x] Vue Comparative (ranking, score composite, TCAM banques)
- [x] Vue Micro générique (radar, historique, ratios)
- [x] Vue UBA Focus (diagnostic automatique, recommandations)

---

## 📋 Instructions d'Installation et Lancement

### 1. Prérequis
- Python 3.10+
- Compte MongoDB Atlas (Gratuit — Cluster0)

### 2. Installation

```bash
# Depuis la racine du projet
python -m venv .venv
.\.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 3. Configuration `.env`

```env
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/
DB_DEV=banque_dev
DB_PROD=banque_prod
COLLECTION_NAME=performances_bancaires
```

### 4. Lancer le Pipeline ETL (dans l'ordre)

```bash
# Depuis la racine du projet

# Étape 1 : Ingestion CSV historique (2015-2020)
python data_engineering/ingestion.py

# Étape 3 : OCR des rapports BCEAO (placer les PDF dans data/pdf/ au préalable)
python scripts/robust_ocr.py
# Options disponibles :
#   --force-senegal   (désactiver filtre pays, traiter toutes les banques)
#   --file <chemin>   (traiter un seul PDF)

# Étape 4 : Fusion intelligente CSV + PDF
python data_engineering/normalisation.py

# Étape 5 : Nettoyage et validation
python data_engineering/cleaning.py

# Étape 6 : Enrichissement + Promotion vers PROD
python data_engineering/enrichment.py
```

> 💡 **Rapports PDF BCEAO** : Déposer les fichiers dans :
> - `data/pdf/2019-2021/bilans_2019_2021.pdf`
> - `data/pdf/2021-2023/bilans_2021_2023.pdf`

### 5. Lancer le Dashboard

```bash
python dashboard/app.py
```

Ouvrir : **http://127.0.0.1:8050/**

---

## 📐 Indicateurs & Ratios Calculés

| Ratio | Formule | Seuil |
|-------|---------|-------|
| **R_SOLVABILITE** | Fonds Propres / Bilan × 100 | > 8% (Bâle III) |
| **R_ROE** | Résultat Net / Fonds Propres × 100 | > 10% recommandé |
| **R_ROA** | Résultat Net / Bilan × 100 | — |
| **R_LEVIER** | Fonds Propres / Ressources × 100 | — |
| **R_COEFF_EXPLOITATION** | Charges Générales / PNB × 100 | < 60% recommandé |

---

## 🗃️ Schéma de Données (30 colonnes CSV de référence)

```
Identifiants    : Sigle, Goupe_Bancaire, ANNEE
Bilan           : EMPLOI, BILAN, RESSOURCES, FONDS.PROPRE
Réseau          : EFFECTIF, AGENCE, COMPTE
Compte Résultat : INTERETS.ET.PRODUITS.ASSIMILES, NTERETS.ET.CHARGES.ASSIMILEES,
                  REVENUS.DES.TITRES.A.REVENU.VARIABLE, COMMISSIONS.(PRODUITS),
                  COMMISSIONS.(CHARGES), GAINS.OU.PERTES.NETS... (NEGOCIATION),
                  GAINS.OU.PERTES.NETS... (PLACEMENT), AUTRES.PRODUITS...,
                  AUTRES.CHARGES..., PRODUIT.NET.BANCAIRE, SUBVENTIONS...,
                  CHARGES.GENERALES..., DOTATIONS.AUX.AMORTISSEMENTS...,
                  RESULTAT.BRUT.D'EXPLOITATION, COÛT.DU.RISQUE,
                  RESULTAT.D'EXPLOITATION, GAINS.OU.PERTES...IMMOBILISES,
                  RESULTAT.AVANT.IMPÔT, IMPÔTS.SUR.LES.BENEFICES, RESULTAT.NET
```

---

## 📦 Sources de Données

- **Historique (2015-2020)** : Fichier Excel/CSV consolidé (`base_senegal.csv`)
- **Récent (2021-2023)** : Rapports Annuels BCEAO triennaux (PDF scrappés/fournis)
- **Géolocalisation** : Coordonnées OpenStreetMap (sièges sociaux Dakar)

---

## Auteur

Projet réalisé par **Fadel ADAM** — M2 Data Engineering & Visualisation  
Encadré par **Dr. Momar Sall Gueye — Group ISM**
