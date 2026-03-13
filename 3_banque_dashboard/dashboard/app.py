
"""
Tableau de Bord Bancaire Avancé - Version 2.0
Visualisation stratégique des performances bancaires au Sénégal.
"""

import sys
import os
from pathlib import Path

# Ajouter le dossier parent (racine du projet) au PYTHONPATH
# Cela permet d'importer 'config' et 'dashboard' comme des modules
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from dash import Dash
# Maintenant on peut importer depuis le package dashboard
from dashboard.core.settings import THEME
from dashboard.utils.data import load_data
from dashboard.core.layout import create_layout
from dashboard.core.callbacks import register_callbacks

# Initialisation de l'application
app = Dash(
    __name__, 
    external_stylesheets=[THEME, "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial_scale=1"}],
    suppress_callback_exceptions=True
)
app.title = "BCEAO Insight | Dashboard"

# Chargement des données
df = load_data()

# Définition du Layout
app.layout = create_layout(df)

# Enregistrement des Callbacks
register_callbacks(app, df)

if __name__ == '__main__':
    # Mode debug activé pour le développement
    app.run(debug=True, port=8050)
