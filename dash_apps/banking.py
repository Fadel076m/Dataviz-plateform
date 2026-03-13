"""
dash_apps/banking.py
Wrapper : Dashboard Bancaire BCEAO — url_base_pathname='/banking/'

Structure du projet source (3_banque_dashboard/) :
  dashboard/app.py
  dashboard/core/layout.py   → create_layout(df)
  dashboard/core/callbacks.py → register_callbacks(app, df)
  dashboard/core/settings.py  → THEME
  dashboard/utils/data.py     → load_data()  [MongoDB Atlas → PROD/DEV]
  config/database.py          → MongoDBConnection
  data/base_senegal.csv       (fallback local si MongoDB offline)
  assets/
"""

import sys
import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_BANKING_DIR = _ROOT / "3_banque_dashboard"
_BANKING_DASHBOARD = _BANKING_DIR / "dashboard"


def create_banking_app():
    """
    Instancie le dashboard bancaire Dash avec url_base_pathname='/banking/'.
    Utilise MongoDB Atlas (prod) avec fallback CSV local.
    """
    # Injecter le projet banque ET son sous-dossier dashboard dans PYTHONPATH
    for p in [str(_BANKING_DIR), str(_BANKING_DASHBOARD)]:
        if p not in sys.path:
            sys.path.insert(0, p)

    # Charger les variables d'environnement du projet banque
    from dotenv import load_dotenv
    load_dotenv(str(_BANKING_DIR / ".env"))

    # ── Imports du projet source ─────────────────────────────
    import dash
    from dash import html

    from dashboard.core.settings import THEME
    from dashboard.utils.data import load_data
    from dashboard.core.layout import create_layout
    from dashboard.core.callbacks import register_callbacks

    # ── Chargement des données (MongoDB ou fallback CSV) ─────
    df = load_data()

    # ── Création de l'app Dash ───────────────────────────────
    app = dash.Dash(
        __name__,
        requests_pathname_prefix="/banking/",
        routes_pathname_prefix="/",
        external_stylesheets=[
            THEME,
            "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css",
        ],
        meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
        suppress_callback_exceptions=True,
        assets_folder=str(_BANKING_DASHBOARD / "assets"),
        title="DataViz | Bancaire — BCEAO",
    )

    # ── Layout avec barre retour hub ─────────────────────────
    base_layout = create_layout(df)

    back_bar = html.Div(
        style={
            "display": "flex", "alignItems": "center", "gap": "12px",
            "padding": "8px 20px",
            "background": "rgba(0,0,0,0.5)",
            "borderBottom": "1px solid rgba(212,175,55,0.2)",
            "position": "fixed", "top": "0", "left": "0", "right": "0", "zIndex": "9999",
        },
        children=[
            html.A("← Hub Analytics", href="/",
                   style={"color": "#D4AF37", "fontWeight": "600", "fontSize": "0.88rem",
                          "textDecoration": "none", "fontFamily": "Inter, sans-serif"}),
            html.Span("›", style={"color": "rgba(255,255,255,0.3)", "fontSize": "1.1rem"}),
            html.Span("Bancaire — BCEAO",
                      style={"color": "rgba(255,255,255,0.7)", "fontSize": "0.88rem",
                             "fontFamily": "Inter, sans-serif"}),
        ],
    )

    app.layout = html.Div(
        [
            back_bar,
            html.Div(base_layout, style={"paddingTop": "40px"}),
        ]
    )

    # ── Callbacks ────────────────────────────────────────────
    register_callbacks(app, df)

    return app
