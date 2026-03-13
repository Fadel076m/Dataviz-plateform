# 🏥 Dashboard de Performance Hospitalière

> **Outil d'analyse stratégique** pour optimiser la prise en charge des patients, maîtriser les coûts et piloter la qualité des soins.

**Auteur :** Fadel ADAM | Direction de la Performance Hospitalière  
**Framework :** [Plotly Dash](https://dash.plotly.com/) · **Stack :** Python, Pandas, Plotly  
**Port par défaut :** `http://localhost:8050`

---

## 📋 Table des matières

1. [Aperçu du projet](#aperçu-du-projet)
2. [Fonctionnalités](#fonctionnalités)
3. [Architecture du projet](#architecture-du-projet)
4. [Données](#données)
5. [Installation](#installation)
6. [Lancement](#lancement)
7. [Modules d'analyse](#modules-danalyse)
8. [Palette de couleurs](#palette-de-couleurs)
9. [Recommandations stratégiques](#recommandations-stratégiques)

---

## Aperçu du projet

Ce tableau de bord interactif a été conçu dans le cadre d'un cours de **Data Visualisation (Master 2)** pour simuler un outil de pilotage hospitalier réel. Il permet à une direction médicale d'analyser en un coup d'œil :

- La **durée moyenne des séjours** par pathologie, département et profil patient
- Le **coût moyen et total** des prises en charge
- Les **inefficiences opérationnelles** (séjours trop longs, coûts aberrants)
- Des **recommandations stratégiques** actionnables

Tous les graphiques sont **interactifs** et se mettent à jour dynamiquement via un système de filtres croisés.

---

## Fonctionnalités

| Fonctionnalité | Description |
|---|---|
| 📊 **KPI globaux** | Nombre de patients, durée moyenne/médiane de séjour, coût moyen, coût total |
| 🎛️ **Filtres croisés** | Filtres multi-sélection par département, pathologie, tranche d'âge, et sexe |
| 🔄 **Réinitialisation** | Bouton pour remettre tous les filtres à zéro en un clic |
| 🦠 **Analyse par pathologie** | Durée et coût moyen par maladie (Cancer, Fracture, Alzheimer, etc.) |
| 🏢 **Analyse par département** | Comparaison des performances entre services (Cardiologie, Neurologie, etc.) |
| 👤 **Profil patient** | Segmentation par tranche d'âge et sexe |
| ⚠️ **Détection d'inefficiences** | Identification des cas au-dessus du 95e percentile en coût ou durée |
| 🧠 **Recommandations** | Section de synthèse stratégique fixe pour guider la décision |

---

## Architecture du projet

```
1_hospital_dashboard/
│
├── app.py                    # Point d'entrée principal — initialise Dash et assemble le layout
├── hospital_data.csv         # Jeu de données hospitalier simulé
├── requirements.txt          # Dépendances Python
│
├── assets/
│   └── styles.css            # Feuille de style CSS personnalisée (thème médical)
│
├── data/
│   ├── loader.py             # Chargement et préparation des données (création AgeGroup)
│   └── cleaning.py           # Nettoyage et validation du dataset
│
├── utils/
│   ├── metrics.py            # Calcul des KPIs (global, pathologie, département, profil)
│   └── colors.py             # Palette de couleurs médicales et template Plotly personnalisé
│
├── components/
│   ├── context.py            # Bannière d'en-tête (titre, objectif, auteur)
│   ├── filters.py            # Barre de filtres interactifs (4 dropdowns + reset)
│   ├── kpis.py               # Cartes KPI du niveau 1 (vue stratégique globale)
│   ├── callbacks.py          # Callback principal — mise à jour des KPIs selon les filtres
│   └── conclusion.py         # Section de recommandations stratégiques
│
└── features/
    ├── pathology/            # Module Analyse par Pathologie
    │   ├── layout.py         # Layout de la section
    │   ├── charts.py         # Graphique en barres (durée & coût par maladie)
    │   └── callbacks.py      # Callback de mise à jour
    │
    ├── department/           # Module Analyse par Département
    │   ├── layout.py
    │   ├── charts.py         # Graphique en barres groupées (4 métriques)
    │   └── callbacks.py
    │
    ├── profile/              # Module Profil Patient
    │   ├── layout.py
    │   ├── charts.py         # Graphique par tranche d'âge
    │   └── callbacks.py
    │
    └── inefficiency/         # Module Détection des Inefficiences
        ├── layout.py
        ├── charts.py         # Scatter plot coût vs durée (outliers mis en évidence)
        └── callbacks.py
```

---

## Données

### Fichier source : `hospital_data.csv`

Le fichier contient des données simulées de **patients hospitalisés**. Voici les colonnes clés utilisées :

| Colonne | Type | Description |
|---|---|---|
| `PatientID` | `str` | Identifiant unique du patient |
| `Maladie` | `str` | Pathologie diagnostiquée (Cancer, Infarctus, Fracture, Alzheimer, Pneumonie, Hypertension, Eczéma) |
| `Departement` | `str` | Service hospitalier (Cardiologie, Oncologie, Neurologie, Orthopédie, Pneumologie, Gériatrie, Dermatologie) |
| `Age` | `int` | Âge du patient en années |
| `AgeGroup` | `category` | Tranche d'âge calculée automatiquement : `0-18`, `19-35`, `36-50`, `51-65`, `65+` |
| `Sexe` | `str` | Sexe du patient (`M` / `F`) |
| `DureeSejour` | `int` | Durée du séjour en jours |
| `Cout` | `float` | Coût total du séjour en euros (€) |

> **Note :** La colonne `AgeGroup` est générée automatiquement depuis `Age` lors du chargement si elle n'existe pas dans le CSV.

---

## Installation

### Prérequis

- Python **3.9+**
- `pip` ou un gestionnaire d'environnement virtuel (`venv`, `conda`)

### Étapes

**1. Cloner ou ouvrir le dossier du projet**

```bash
cd 1_hospital_dashboard
```

**2. Créer et activer un environnement virtuel** (recommandé)

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

**3. Installer les dépendances**

```bash
pip install -r requirements.txt
```

---

## Lancement

```bash
python app.py
```

Ouvrir ensuite le navigateur à l'adresse : **[http://localhost:8050](http://localhost:8050)**

Le serveur se lance en mode `debug=True` par défaut (rechargement automatique à chaque modification du code).

---

## Modules d'analyse

Le dashboard est organisé en **4 niveaux d'analyse** hiérarchiques :

### Niveau 1 — Vue Globale (KPIs)
Affichage de 6 indicateurs clés en temps réel, mis à jour selon les filtres actifs :
- Nombre total de patients uniques
- Durée moyenne et médiane de séjour (jours)
- Coût moyen par séjour (€)
- Coût moyen par jour (€)
- Coût total cumulé (€)

### Niveau 2 — Analyse par Pathologie
Graphique en barres comparant la **durée moyenne** et le **coût moyen** pour chacune des 7 pathologies disponibles. Permet d'identifier les maladies les plus coûteuses et les plus chronophages.

### Niveau 2 bis — Analyse par Département
Comparaison des 7 départements sur 4 métriques : durée moyenne, coût moyen, coût total et coût par jour. Permet une allocation budgétaire éclairée entre services.

### Niveau 3 — Profil Patient
Segmentation des patients par **tranche d'âge** avec durée et coût associés. Aide à adapter les protocoles de soins selon les profils démographiques.

### Niveau 4 — Détection des Inefficiences
Scatter plot **Coût vs Durée de Séjour** : les patients au-delà du **95e percentile** en coût (`HighCost`) ou en durée (`LongStay`) sont mis en évidence comme cas aberrants à investiguer en priorité.

---

## Palette de couleurs

Le projet utilise une palette **médicale professionnelle** définie dans `utils/colors.py` :

| Couleur | Code Hex | Usage |
|---|---|---|
| Bleu médical | `#3498db` | Couleur principale, Alzheimer |
| Vert santé | `#2ecc71` | Positif, Pneumonie |
| Rouge alerte | `#e74c3c` | Attention critique, Cancer |
| Orange attention | `#f39c12` | Vigilance, Infarctus |
| Violet innovation | `#9b59b6` | Fracture, Neurologie |
| Turquoise succès | `#1abc9c` | Succès, Eczéma |
| Gris foncé | `#2c3e50` | Textes, Hypertension |

Un **template Plotly personnalisé** (`CUSTOM_TEMPLATE`) est appliqué à tous les graphiques pour garantir une cohérence visuelle (police Segoe UI, fond blanc, hover uniforme).

---

## Recommandations stratégiques

La section de conclusion du dashboard synthétise 3 axes d'amélioration :

1. **🎯 Optimisation des coûts** — Les pathologies *Cancer* et *Fracture* représentent ~45% du budget total. Une analyse détaillée des traitements associés est recommandée.

2. **⏱️ Réduction des durées de séjour** — Le département *Cardiologie* présente une durée moyenne élevée. La mise en place d'un parcours de soins optimisé est préconisée.

3. **📊 Surveillance continue** — Déploiement d'un tableau de bord opérationnel pour suivre en temps réel les indicateurs clés de performance.

---

*Analyse réalisée par **Fadel ADAM** | Direction de la Performance Hospitalière*
