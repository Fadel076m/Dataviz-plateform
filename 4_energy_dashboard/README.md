# ☀️ Solar Park Analytics — Dashboard PV

Dashboard interactif professionnel pour le suivi et l'analyse de la production d'énergie solaire photovoltaïque.

## 📁 Architecture du projet

```
4_energy_dashboard/
├── app.py                  # Point d'entrée Dash
├── requirements.txt        # Dépendances Python
├── README.md               # Documentation
├── .gitignore              # Fichiers ignorés par Git
│
├── data/                   # Données brutes
│   └── salar_data.csv      # Dataset solaire (35 136 obs.)
│
├── src/                    # Code source (package Python)
│   ├── __init__.py
│   ├── data_processing.py  # Chargement, KPIs, anomalies
│   ├── layout.py           # Mise en page du dashboard
│   └── callbacks.py        # Callbacks interactifs Plotly
│
└── assets/                 # Assets statiques (Dash)
    └── style.css           # Thème sombre solaire premium
```

## 🚀 Lancement

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Lancer le dashboard
python app.py

# 3. Ouvrir dans le navigateur
# http://127.0.0.1:8050
```

## 📊 Fonctionnalités

- **8 KPIs stratégiques** : production totale, rendement AC/DC, facteur de capacité, etc.
- **10 visualisations** : line charts, heatmap, scatter plots, box plots, pie charts
- **Filtres interactifs** : par pays, mois, plage de dates
- **Détection d'anomalies** : 5 règles métier (panne onduleur, surchauffe, etc.)
- **Conclusions et recommandations** : techniques, énergétiques, maintenance, stratégiques

## 🌍 Données

- **4 pays** : Norvège, Brésil, Inde, Australie
- **Année** : 2024
- **Fréquence** : Horaire (24h × 365j × 4 pays)
- **Variables** : DC_Power, AC_Power, Irradiation, Températures, Daily/Total Yield

## 🛠️ Technologies

- **Dash 4.0** — Framework web
- **Plotly 6.5** — Visualisations interactives
- **Pandas** — Traitement des données
- **NumPy** — Calculs numériques
