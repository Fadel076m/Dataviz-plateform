
"""
Module pour convertir un notebook Jupyter (.ipynb) en HTML.
Gère l'exécution du notebook pour inclure les outputs les plus récents.
"""

import nbformat
from nbconvert import HTMLExporter
from nbconvert.preprocessors import ExecutePreprocessor
import pandas as pd
import os

# Import local du sommaire
from dashboard.utils.report.sommaire import add_toc

def notebook_to_html(notebook_path):
    """
    Convertit un notebook Jupyter (.ipynb) en HTML.

    Paramètre
    ---------
    notebook_path : str
        Chemin complet vers le fichier .ipynb à convertir.

    Retour
    ------
    str
        Code HTML généré à partir du notebook exécuté.
    """

    if not os.path.exists(notebook_path):
        raise FileNotFoundError(f"Le fichier notebook {notebook_path} n'existe pas.")

    # --- 1) Lecture du fichier .ipynb en texte brut ---
    with open(notebook_path, "r", encoding="utf-8") as f:
        notebook_content = f.read()

    # --- 2) Conversion du texte JSON en objet notebook ---
    notebook = nbformat.reads(notebook_content, as_version=4)

    # --- 3) Exécution du notebook cellule par cellule ---
    # timeout=-1 signifie qu'il n’y a pas de limite de temps pour chaque cellule.
    # On définit kernel_name si nécessaire (par défaut utilise celui du notebook)
    executor = ExecutePreprocessor(timeout=-1)

    # preprocess exécute le notebook et ajoute les sorties dans l'objet notebook
    try:
        executor.preprocess(notebook, {'metadata': {'path': os.path.dirname(notebook_path)}})
    except Exception as e:
        print(f"Attention: Une erreur est survenue lors de l'exécution du notebook: {e}")
        # On continue quand même pour tenter l'exportation des cellules déjà exécutées ou des erreurs

    # --- 4) Préparation de l'exportation en HTML ---
    # template_name="classic" → style HTML simple de Jupyter.
    # exclude_input=True     → on n'affiche PAS le code source, seulement les résultats.
    html_exporter = HTMLExporter(template_name="classic", exclude_input=True)

    # embed_widgets=True permet d'inclure les widgets interactifs
    resources = {"embed_widgets": True}

    # --- 5) Conversion du notebook exécuté en HTML ---
    body, _ = html_exporter.from_notebook_node(notebook, resources=resources)

    # --- 6) Ajout du sommaire automatique ---
    body = add_toc(body)

    # --- 7) Retourne le HTML final ---
    return body
