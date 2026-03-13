"""
dash_apps/hospital.py
Wrapper : Dashboard Hospitalier — url_base_pathname='/hospital/'

Utilise importlib.util pour charger les modules par chemin absolu
et éviter les conflits de noms (utils/, components/, features/).
"""

import sys
import importlib
import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_HOSPITAL_DIR = _ROOT / "1_hospital_dashboard"


def _load(alias: str, rel_path: str):
    """Charge un module .py depuis un chemin relatif au projet hospital."""
    if alias in sys.modules:
        return sys.modules[alias]
    full_path = _HOSPITAL_DIR / rel_path
    spec = importlib.util.spec_from_file_location(alias, str(full_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Impossible de charger le module {alias} depuis {full_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)
    return mod


def create_hospital_app():
    """
    Instancie le dashboard hospitalier Dash avec url_base_pathname='/hospital/'.
    """
    # Injecter hospital dans sys.path pour les imports relatifs des features/
    hospital_str = str(_HOSPITAL_DIR)
    if hospital_str not in sys.path:
        sys.path.insert(0, hospital_str)

    import dash
    import dash_bootstrap_components as dbc
    from dash import html

    # ── Modules core via importlib (évite conflits avec insurance) ──
    loader_mod  = _load("hosp.data.loader",    "data/loader.py")
    metrics_mod = _load("hosp.utils.metrics",  "utils/metrics.py")
    filters_mod = _load("hosp.components.filters",    "components/filters.py")
    context_mod = _load("hosp.components.context",    "components/context.py")
    kpis_mod    = _load("hosp.components.kpis",       "components/kpis.py")
    conclu_mod  = _load("hosp.components.conclusion", "components/conclusion.py")
    cbacks_mod  = _load("hosp.components.callbacks",  "components/callbacks.py")

    # Features (utilisent des imports relatifs — sys.path géré ci-dessus)
    from features.pathology.layout    import pathology_section
    from features.pathology.charts    import pathology_bar_chart
    from features.pathology.callbacks import register_pathology_callbacks
    from features.department.layout    import department_section
    from features.department.charts    import department_bar_chart
    from features.department.callbacks import register_department_callbacks
    from features.profile.layout    import profile_section
    from features.profile.charts    import profile_bar_chart
    from features.profile.callbacks import register_profile_callbacks
    from features.inefficiency.layout    import inefficiency_section
    from features.inefficiency.charts    import scatter_inefficiencies
    from features.inefficiency.callbacks import register_inefficiency_callbacks

    load_data   = loader_mod.load_data
    global_kpis    = metrics_mod.global_kpis
    pathology_kpis = metrics_mod.pathology_kpis
    department_kpis = metrics_mod.department_kpis
    profile_kpis   = metrics_mod.profile_kpis
    filters_layout = filters_mod.filters_layout
    context_section_fn = context_mod.context_section
    kpi_cards      = kpis_mod.kpi_cards
    conclusion_section_fn = conclu_mod.conclusion_section
    register_component_callbacks = cbacks_mod.register_component_callbacks

    # ── Chargement des données ───────────────────────────────
    csv_path = str(_HOSPITAL_DIR / "hospital_data.csv")
    df = load_data(csv_path)

    # ── KPIs et graphiques initiaux ──────────────────────────
    kpis           = global_kpis(df)
    fig_pathology  = pathology_bar_chart(df, pathology_kpis)
    fig_department = department_bar_chart(df, department_kpis)
    fig_profile    = profile_bar_chart(df, profile_kpis)
    fig_ineff      = scatter_inefficiencies(df)

    # ── Création de l'app Dash ───────────────────────────────
    app = dash.Dash(
        __name__,
        requests_pathname_prefix="/hospital/",
        routes_pathname_prefix="/",
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True,
        assets_folder=str(_HOSPITAL_DIR / "assets"),
        title="DataViz | Hospitalier",
        meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    )

    # Barre retour hub
    back_bar = html.Div(
        style={
            "display": "flex", "alignItems": "center", "gap": "12px",
            "padding": "10px 20px", "marginBottom": "16px",
            "background": "rgba(0,212,170,0.06)",
            "borderRadius": "10px",
            "border": "1px solid rgba(0,212,170,0.2)",
        },
        children=[
            html.A("← Hub Analytics", href="/",
                   style={"color": "#00D4AA", "fontWeight": "600", "fontSize": "0.88rem",
                          "textDecoration": "none", "fontFamily": "Inter, sans-serif"}),
            html.Span("›", style={"color": "rgba(0,0,0,0.3)", "fontSize": "1.1rem"}),
            html.Span("Hospitalier", style={"color": "rgba(0,0,0,0.6)",
                                            "fontSize": "0.88rem", "fontFamily": "Inter, sans-serif"}),
        ],
    )

    # ── Layout ───────────────────────────────────────────────
    app.layout = dbc.Container(
        fluid=True,
        className="p-4",
        children=[
            back_bar,
            context_section_fn(),
            filters_layout(df),
            html.Div(id="kpi-container", children=kpi_cards(kpis)),
            pathology_section(fig_pathology),
            department_section(fig_department),
            profile_section(fig_profile),
            inefficiency_section(fig_ineff),
            conclusion_section_fn(),
        ],
    )

    # ── Callbacks ────────────────────────────────────────────
    register_component_callbacks(app, df)
    register_pathology_callbacks(app, df)
    register_department_callbacks(app, df)
    register_profile_callbacks(app, df)
    register_inefficiency_callbacks(app, df)

    return app
