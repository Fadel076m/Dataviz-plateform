# 📊 DataViz Analytics Platform

Une plateforme d'analyse de données centralisée regroupant 4 tableaux de bord interactifs spécialisés, propulsée par **Flask** et **Dash (Plotly)**.

## 🚀 Fonctionnalités

Cette plateforme intègre une application web centrale (Hub) qui permet d'accéder à quatre univers analytiques distincts :

1.  **🏥 Hospital Dashboard** (`/hospital`) : Analyse des données hospitalières et flux de patients.
2.  **🛡️ Insurance Dashboard** (`/insurance`) : Pilotage des indicateurs de performance en assurance.
3.  **🏦 Banking Dashboard** (`/banking`) : Suivi des transactions et santé financière.
4.  **⚡ Energy Dashboard** (`/energy`) : Analyse de la consommation et de la production d'énergie.

## 🛠️ Installation

### 1. Prérequis
- Python 3.8+
- Un environnement virtuel est recommandé.

### 2. Cloner le projet
```bash
git clone <URL_DU_DEPOT>
cd "Data Viz"
```

### 3. Installer les dépendances
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Configuration
Copiez le fichier `.env.example` en `.env` et ajustez les variables si nécessaire.
```bash
cp .env.example .env
```

## 🏃 Lancement

### Mode Développement
Pour lancer le serveur avec le rechargement automatique :
```bash
python run.py
```
L'application sera accessible sur `http://localhost:5000`.

### Mode Production
Le projet est configuré pour être déployé sur **Render** ou **Heroku** via Gunicorn :
```bash
gunicorn run:application --config gunicorn_config.py
```

## 📁 Structure du Projet

- `central_app/` : Application Flask principale (Hub).
- `dash_apps/` : Dossier contenant les wrappers pour les 4 applications Dash.
- `1_hospital_dashboard/`, `2_assurance_dashboard/`, etc. : Code source spécifique à chaque dashboard.
- `run.py` : Point d'entrée de l'application (DispatcherMiddleware).
- `render.yaml` : Fichier de configuration pour le déploiement sur Render.

---
*Développé avec ❤️ pour le Master 2 Data Viz.*
