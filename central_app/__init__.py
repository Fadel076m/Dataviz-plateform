"""
central_app/__init__.py
Flask Application Factory — Hub central des dashboards Data Viz
"""

from flask import Flask
from .config import Config


def create_app(config_class=Config):
    """
    Crée et configure l'application Flask centrale.
    Pattern Application Factory pour faciliter les tests et le déploiement.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ── Blueprints ────────────────────────────────────────────
    from .home.routes import home_bp
    app.register_blueprint(home_bp)

    return app
