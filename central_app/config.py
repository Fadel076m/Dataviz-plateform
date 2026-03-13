"""
central_app/config.py
Configuration Flask — Dev / Prod
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration de base pour l'application Flask."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

    # MongoDB (utilisé par le dashboard Banque)
    MONGODB_URI = os.getenv("MONGODB_URI", "")
    DB_DEV = os.getenv("DB_DEV", "banque_dev")
    DB_PROD = os.getenv("DB_PROD", "banque_prod")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "performances_bancaires")

    # Chemins absolus vers chaque projet dashboard (relatifs à la racine Data Viz)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    HOSPITAL_DIR    = os.path.join(BASE_DIR, "1_hospital_dashboard")
    INSURANCE_DIR   = os.path.join(BASE_DIR, "2_assurance_dashboard")
    BANKING_DIR     = os.path.join(BASE_DIR, "3_banque_dashboard")
    ENERGY_DIR      = os.path.join(BASE_DIR, "4_energy_dashboard")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


# Map des configs
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
