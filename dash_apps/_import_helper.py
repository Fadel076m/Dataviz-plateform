"""
dash_apps/_import_helper.py
Utilitaire pour l'import isolé de modules depuis des chemins absolus.
Évite les conflits de noms entre les dossiers (utils/, components/) des différents projets.
"""

import sys
import importlib
import importlib.util
from pathlib import Path


def import_module_from_path(module_name: str, file_path: str):
    """
    Importe un module Python depuis un chemin absolu vers un fichier .py.
    Utilise un nom unique pour éviter les conflits dans sys.modules.

    Args:
        module_name: Nom unique sous lequel enregistrer le module (ex: 'ins_utils_data_loader')
        file_path:   Chemin absolu vers le fichier .py à importer

    Returns:
        Le module importé
    """
    if module_name in sys.modules:
        return sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Impossible de charger le module {module_name} depuis {file_path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def import_package_from_dir(package_name: str, package_dir: str):
    """
    Importe un package Python depuis un répertoire absolu.
    Le package doit contenir un __init__.py.

    Args:
        package_name: Nom unique du package (ex: 'ins_components')
        package_dir:  Chemin absolu du dossier du package

    Returns:
        Le package importé
    """
    package_dir = Path(package_dir)
    init_file = package_dir / "__init__.py"

    if package_name in sys.modules:
        return sys.modules[package_name]

    spec = importlib.util.spec_from_file_location(
        package_name,
        str(init_file),
        submodule_search_locations=[str(package_dir)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Impossible de charger le package {package_name} depuis {package_dir}")
        
    module = importlib.util.module_from_spec(spec)
    sys.modules[package_name] = module
    spec.loader.exec_module(module)
    return module
