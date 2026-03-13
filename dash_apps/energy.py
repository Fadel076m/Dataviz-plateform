"""
dash_apps/energy.py
Wrapper : Dashboard Énergie Solaire — url_base_pathname='/energy/'

Structure du projet source (4_energy_dashboard/) :
  app.py
  src/__init__.py
  src/layout.py         → create_layout()    [charge les données au module-level]
  src/callbacks.py      → register_callbacks(app)
  src/data_processing.py → load_data(), filter_data(), etc.
  data/salar_data.csv   (~3 MB — chargé une seule fois via lru_cache dans src)
  assets/style.css
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_ENERGY_DIR = _ROOT / "4_energy_dashboard"


def create_energy_app():
    """
    Instancie le dashboard énergie solaire Dash avec url_base_pathname='/energy/'.
    Le CSV (~3 MB) est chargé une seule fois : data_processing.py charge au niveau module.
    """
    energy_str = str(_ENERGY_DIR)
    if energy_str not in sys.path:
        sys.path.insert(0, energy_str)

    # ── Imports du projet source ─────────────────────────────
    import dash
    from dash import html

    # Ces imports déclenchent le chargement du CSV (au niveau module dans src/)
    from src.layout import create_layout
    from src.callbacks import register_callbacks

    # ── Création de l'app Dash ───────────────────────────────
    app = dash.Dash(
        __name__,
        requests_pathname_prefix="/energy/",
        routes_pathname_prefix="/",
        title="DataViz | Solar Park Analytics",
        update_title="Chargement...",
        suppress_callback_exceptions=True,
        assets_folder=str(_ENERGY_DIR / "assets"),
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
            {"name": "description", "content": "Dashboard analytique de production d'énergie solaire photovoltaïque"},
        ],
    )

    # ── Layout avec barre retour hub ─────────────────────────
    back_bar = html.Div(
        style={
            "display": "flex", "alignItems": "center", "gap": "12px",
            "padding": "10px 24px",
            "background": "rgba(15,15,35,0.95)",
            "borderBottom": "1px solid rgba(255,184,0,0.2)",
            "position": "fixed", "top": "0", "left": "0", "right": "0", "zIndex": "9999",
        },
        children=[
            html.A("← Hub Analytics", href="/",
                   style={"color": "#FFB800", "fontWeight": "600", "fontSize": "0.88rem",
                          "textDecoration": "none", "fontFamily": "Inter, sans-serif"}),
            html.Span("›", style={"color": "rgba(255,255,255,0.3)", "fontSize": "1.1rem"}),
            html.Span("Énergie Solaire",
                      style={"color": "rgba(255,255,255,0.7)", "fontSize": "0.88rem",
                             "fontFamily": "Inter, sans-serif"}),
        ],
    )

    original_layout = create_layout()

    app.layout = html.Div(
        [
            back_bar,
            html.Div(original_layout, style={"paddingTop": "44px"}),
        ]
    )

    # ── Callbacks ────────────────────────────────────────────
    register_callbacks(app)

    return app
