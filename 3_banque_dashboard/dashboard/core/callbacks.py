
from dash import Input, Output, State, dcc, html
import dash_bootstrap_components as dbc
from dashboard.pages.macro_view import render_macro_view
from dashboard.pages.comparative_view import render_comparative_view
from dashboard.pages.micro_view import render_micro_view
from dashboard.pages.uba_focus import render_uba_focus

def register_callbacks(app, df):
    
    # CALLBACK 1 : Navigation par Onglets (Dispatching)
    @app.callback(
        Output('tab-content', 'children'),
        [Input('main-tabs', 'active_tab'),
         Input('year-selector', 'value'),
         Input('bank-selector', 'value'),
         Input('group-selector', 'value')]
    )
    def render_tab_content(active_tab, selected_year, selected_bank, selected_group):
        if df.empty:
            return dbc.Alert("Aucune donnée disponible dans la base MongoDB.", color="danger", className="mt-5")
            
        if not selected_year:
            return dbc.Alert("Veuillez sélectionner une année pour charger les données.", color="warning", className="mt-5")

        try:
            if active_tab == "tab-macro":
                return render_macro_view(df, selected_year, selected_group)

            elif active_tab == "tab-comparative":
                return render_comparative_view(df, selected_year, selected_bank, selected_group)

            elif active_tab == "tab-micro":
                if not selected_bank:
                    return dbc.Alert("Veuillez sélectionner une banque.", color="info", className="mt-5")
                return render_micro_view(df, selected_year, selected_bank)
            elif active_tab == "tab-uba":
                return render_uba_focus(df, selected_year)
        except Exception as e:
            import traceback
            print(f"Erreur rendu onglet {active_tab}: {e}")
            print(traceback.format_exc())
            return dbc.Alert([
                html.H4("⚠️ Erreur lors du rendu de la vue", className="alert-heading"),
                html.P(f"Un problème est survenu lors du chargement de l'onglet : {str(e)}"),
                html.Hr(),
                html.P("Vérifiez la structure de vos données dans MongoDB ou contactez l'administrateur.", className="mb-0 small")
            ], color="danger", className="mt-5 shadow-sm")
            
        return html.Div("Sélectionnez un onglet pour commencer l'analyse.")


    # CALLBACK 2 : Génération du Rapport (Phase 5)
    @app.callback(
        [Output("download-report-pdf", "data"),
         Output("report-loading-status", "children")],
        [Input('btn-generate-report', 'n_clicks')],
        prevent_initial_call=True
    )
    def generate_strategic_report(n_clicks):
        import os
        from pathlib import Path
        from dash import dcc
        import time

        if not n_clicks:
            return None, ""

        try:
            # Chemins
            notebook_dir = Path(__file__).resolve().parent.parent / "notebooks"
            notebook_path = notebook_dir / "analyse_approfondie.ipynb"
            pdf_path = notebook_dir / "analyse_approfondie.pdf"
            
            # --- STRATÉGIE DE VITESSE ---
            # Si le PDF existe déjà et a été modifié il y a moins de 10 minutes, on le sert directement.
            if pdf_path.exists():
                file_age = time.time() - os.path.getmtime(pdf_path)
                if file_age < 600: # 10 minutes
                    print(f"Service du PDF existant (âge: {int(file_age)}s)")
                    return dcc.send_file(str(pdf_path)), "✅ Téléchargement immédiat"

            # Sinon, on génère un nouveau PDF de haute qualité (WebPDF)
            # On évite l'exécution complète si le notebook a déjà des résultats pour gagner du temps
            print(f"Génération d'un nouveau rapport PDF via WebPDF...")
            import nbformat
            from nbconvert import WebPDFExporter
            
            with open(notebook_path, "r", encoding="utf-8") as f:
                nb = nbformat.read(f, as_version=4)
            
            # Initialisation de l'exportateur moderne (Playwright)
            exporter = WebPDFExporter()
            # On désactive l'exécution ici pour la rapidité, car le notebook est déjà préparé
            (body, resources) = exporter.from_notebook_node(nb)
            
            # Sauvegarder pour la prochaine fois
            with open(pdf_path, "wb") as f:
                f.write(body)
                
            return dcc.send_bytes(body, "Rapport_Stratégique_Bancaire.pdf"), "✅ Rapport généré !"
                
        except Exception as e:
            print(f"Erreur reporting: {e}")
            # Fallback : Si erreur génération mais fichier existant, on le sert quand même
            if 'pdf_path' in locals() and Path(pdf_path).exists():
                return dcc.send_file(str(pdf_path)), "✅ Servi depuis cache (Erreur REFRESH)"
            return None, f"⚠️ Erreur: {str(e)[:20]}..."

