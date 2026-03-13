"""
run.py — Point d'entrée unique de l'application centralisée
========================================================
Lance Flask + 4 dashboards Dash via DispatcherMiddleware.

Utilisation développement :
    python run.py

Utilisation production (Gunicorn) :
    gunicorn run:application --config gunicorn_config.py
"""

import os
import sys
from pathlib import Path

# ── Assurer que la racine du projet est dans le PYTHONPATH ──
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ── Charger les variables d'environnement (si présentes) ──
from dotenv import load_dotenv
load_dotenv() # Cherche .env par défaut, ne fait rien s'il n'existe pas (Prod)

# ── Flask application factory ────────────────────────────────
from central_app import create_app

flask_app = create_app()

# ── Importer et instancier les 4 apps Dash ──────────────────
# Les wrappers injectent leurs propres sys.path au moment de l'import
print("[*] Initialisation des dashboards Dash...")

print("[*] Chargement Hospital Dashboard...")
from dash_apps.hospital import create_hospital_app
hospital_app = create_hospital_app()
print("[OK] Hospital Dashboard → /hospital/")

print("[*] Chargement Insurance Dashboard...")
from dash_apps.insurance import create_insurance_app
insurance_app = create_insurance_app()
print("[OK] Insurance Dashboard → /insurance/")

print("[*] Chargement Banking Dashboard...")
from dash_apps.banking import create_banking_app
banking_app = create_banking_app()
print("[OK] Banking Dashboard → /banking/")

print("[*] Chargement Energy Dashboard...")
from dash_apps.energy import create_energy_app
energy_app = create_energy_app()
print("[OK] Energy Dashboard → /energy/")

# ── Monter les apps Dash sur Flask via DispatcherMiddleware ──
from werkzeug.middleware.dispatcher import DispatcherMiddleware

application = DispatcherMiddleware(flask_app, {
    "/hospital":  hospital_app.server,
    "/insurance": insurance_app.server,
    "/banking":   banking_app.server,
    "/energy":    energy_app.server,
})

# ── Lancement en mode développement ─────────────────────────
if __name__ == "__main__":
    from werkzeug.serving import run_simple

    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    print("\n" + "=" * 60)
    print("  DataViz Analytics Platform")
    print("  Hub Flask + 4 Dashboards Dash")
    print("=" * 60)
    print(f"\n  Hub Principal   : http://localhost:{port}/")
    print(f"  Hospital        : http://localhost:{port}/hospital/")
    print(f"  Insurance       : http://localhost:{port}/insurance/")
    print(f"  Banking         : http://localhost:{port}/banking/")
    print(f"  Energy          : http://localhost:{port}/energy/")
    print("\n" + "=" * 60 + "\n")

    run_simple(
        "0.0.0.0",
        port,
        application,
        use_reloader=False,   # False car les Dash apps ne supportent pas bien le reloader
        use_debugger=debug,
        threaded=True,
    )
