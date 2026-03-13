"""
app.py — Point d'entrée du Dashboard Solaire Photovoltaïque
Suivi et analyse de la production d'énergie solaire.
"""

from dash import Dash
from src.layout import create_layout
from src.callbacks import register_callbacks

# ──────────────────────────────────────────────
# APPLICATION DASH
# ──────────────────────────────────────────────

app = Dash(
    __name__,
    title="Solar Park Analytics — Dashboard PV",
    update_title="Chargement...",
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
        {"name": "description", "content": "Dashboard analytique de suivi de la production d'énergie solaire photovoltaïque"},
    ],
)

# Layout
app.layout = create_layout()

# Callbacks
register_callbacks(app)

# ──────────────────────────────────────────────
# LANCEMENT
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("\n[*] Solar Park Analytics - Demarrage du serveur...")
    print("[*] http://127.0.0.1:8050\n")
    app.run(debug=True, port=8050)
