
import os
import sys
import traceback
from pathlib import Path

# Ajouter la racine du projet au path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from dashboard.utils.report.convert_to_html import notebook_to_html
from dashboard.utils.report.convert_to_pdf import html_to_pdf

def main():
    print("START: Generation du rapport...")
    
    # Chemins
    notebook_path = project_root / "dashboard" / "notebooks" / "analyse_approfondie.ipynb"
    output_pdf_path = project_root / "data" / "rapport_analyse_approfondie.pdf"
    
    # Activer le mode rendu statique pour Plotly dans le notebook
    os.environ['GENERATE_REPORT'] = '1'
    print(f"STEP 1: Execution et conversion du notebook : {notebook_path.name}")
    try:
        html_content = notebook_to_html(str(notebook_path))
        print("OK: Notebook converti en HTML avec succes.")
    except Exception as e:
        print("ERROR: Erreur lors de la conversion HTML.")
        traceback.print_exc()
        return

    # 2. Conversion HTML -> PDF
    print(f"STEP 2: Conversion HTML vers PDF : {output_pdf_path.name}")
    try:
        html_to_pdf(html_content, str(output_pdf_path))
        print(f"SUCCESS: Rapport PDF genere avec succes dans : {output_pdf_path}")
    except Exception as e:
        print("ERROR: Erreur lors de la conversion PDF.")
        traceback.print_exc()

if __name__ == "__main__":
    main()
