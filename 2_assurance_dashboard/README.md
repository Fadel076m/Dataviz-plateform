# 📊 Dash Insurance Analytics Pro

Ce projet est un tableau de bord décisionnel expert conçu sous **Dash (Python)** pour l'analyse de la sinistralité et du profil des assurés. Il permet de transformer des données brutes en insights stratégiques exploitables pour une compagnie d'assurance.

## 🎯 Objectifs Métiers
*   **Identification des Risques :** Segmentation démographique et géographique des sinistres.
*   **Pilotage de Rentabilité :** Suivi en temps réel du Loss Ratio (S/P).
*   **Aide à la Décision :** Recommandations automatisées basées sur l'analyse des données filtrées.

## 🚀 Installation & Lancement

1.  **Cloner le projet** (ou se placer dans le dossier).
2.  **Activer l'environnement virtuel** :
    ```powershell
    # Windows
    .\.venv\Scripts\Activate.ps1
    ```
3.  **Installer les dépendances** :
    ```bash
    pip install -r requirements.txt
    ```
4.  **Lancer l'application** :
    ```bash
    python app.py
    ```
5.  **Accéder au dashboard** via `http://127.0.0.1:8050`.

## 📂 Structure du Projet
```text
2_assurance_dashboard/
├── app.py                 # Entrée principale et Layout
├── components/
│   ├── charts.py          # Logique de génération des graphiques Plotly
│   └── analysis.py        # Moteur d'insights stratégiques
├── utils/
│   └── data_loader.py     # Chargement, Nettoyage et Feature Engineering
├── assets/                # Styles CSS personnalisés
├── data/                  # Source de données CSV
└── .venv/                 # Environnement virtuel Python
```

## 🧠 Axes d'Analyse
*   **Score de Risque :** Calculé dynamiquement selon la fréquence, la sévérité et le bonus-malus.
*   **Segmentation Démographique :** Analyse de l'impact de l'âge et du sexe sur le risque.
*   **Géographie de la Profitabilité :** Visualisation des régions les plus rentables (Primes vs Sinistres).
*   **Contrôle du Bonus/Malus :** Vérification de la corrélation entre les coefficients et les sinistres réels.
*   **Simulation & What-if :** Moteur interactif pour projeter l'impact de changements tarifaires ou de mesures de prévention.

## 🛠️ Stack Technique
*   **Backend/Frontend** : Dash, Plotly, Dash Bootstrap Components.
*   **Data** : Pandas, NumPy.
*   **UI/UX** : Bootstrap Icons, Custom CSS.

---
*Développé pour un usage professionnel de niveau Portfolio / Big 4.*
