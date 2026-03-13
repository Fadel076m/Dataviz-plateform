"""
central_app/home/routes.py
Blueprint Flask — Landing page principale
"""

from flask import Blueprint, render_template, redirect

home_bp = Blueprint("home", __name__, template_folder="../templates")

# ── Redirections vers les dashboards Dash (trailing slash) ────
@home_bp.route("/hospital")
def go_hospital():
    return redirect("/hospital/")

@home_bp.route("/insurance")
def go_insurance():
    return redirect("/insurance/")

@home_bp.route("/banking")
def go_banking():
    return redirect("/banking/")

@home_bp.route("/energy")
def go_energy():
    return redirect("/energy/")


@home_bp.route("/")
def index():
    """Landing page : sélection du secteur."""
    sectors = [
        {
            "id": "hospital",
            "title": "Hospitalier",
            "subtitle": "Healthcare Analytics",
            "description": "Analyse des performances hospitalières : durée de séjour, pathologies, efficacité des départements et profils patients.",
            "icon": "🏥",
            "accent": "#00D4AA",
            "glow": "rgba(0,212,170,0.3)",
            "url": "/hospital/",
            "kpis": ["Durée de séjour", "Taux de réadmission", "Pathologies", "Inefficiences"],
            "gradient": "linear-gradient(135deg, #0d2b24 0%, #0a1a18 100%)",
        },
        {
            "id": "insurance",
            "title": "Assurance",
            "subtitle": "Risk & Portfolio Analytics",
            "description": "Pilotage du portefeuille assurance : fréquence/sévérité des sinistres, segmentation du risque, bonus-malus et rentabilité géographique.",
            "icon": "🛡️",
            "accent": "#6C63FF",
            "glow": "rgba(108,99,255,0.3)",
            "url": "/insurance/",
            "kpis": ["Loss Ratio", "Charge Sinistres", "Segmentation Risque", "Primes Totales"],
            "gradient": "linear-gradient(135deg, #1a1040 0%, #0d0a24 100%)",
        },
        {
            "id": "banking",
            "title": "Bancaire",
            "subtitle": "BCEAO Insight Dashboard",
            "description": "Suivi des performances bancaires au Sénégal : bilans, PNB, ratios de solvabilité, ROE/ROA et analyse comparative des établissements.",
            "icon": "🏦",
            "accent": "#D4AF37",
            "glow": "rgba(212,175,55,0.3)",
            "url": "/banking/",
            "kpis": ["PNB", "Ratio Solvabilité", "ROE / ROA", "Résultat Net"],
            "gradient": "linear-gradient(135deg, #1a1508 0%, #0d0c05 100%)",
        },
        {
            "id": "energy",
            "title": "Énergie Solaire",
            "subtitle": "Solar Park Analytics",
            "description": "Monitoring de la production photovoltaïque : rendement AC/DC, détection d'anomalies, analyse environnementale sur 4 pays.",
            "icon": "☀️",
            "accent": "#FFB800",
            "glow": "rgba(255,184,0,0.3)",
            "url": "/energy/",
            "kpis": ["Production AC/DC", "Taux Anomalies", "Facteur Capacité", "Irradiation Moy."],
            "gradient": "linear-gradient(135deg, #1a1100 0%, #0d0c00 100%)",
        },
    ]
    return render_template("home/index.html", sectors=sectors)
