
"""
Module pour convertir HTML en PDF pour le téléchargement des rapports.
Utilise xhtml2pdf pour la conversion.
"""

import re
import io

def clean_html_for_pdf(html_content):
    """
    Nettoie le HTML pour le rendre compatible avec xhtml2pdf
    
    Args:
        html_content (str): Le contenu HTML à nettoyer
    
    Returns:
        str: Le HTML nettoyé
    """
    # Supprimer les balises <style> contenant du CSS complexe qui pourrait faire planter xhtml2pdf
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
    
    # Ajouter un CSS simple et compatible pour la mise en page PDF
    simple_css = """
    <style>
        @page {
            size: a4 portrait;
            margin: 2cm;
        }
        body { font-family: Arial, sans-serif; font-size: 10pt; line-height: 1.5; color: #333; }
        h1 { color: #1A3E5C; font-size: 24pt; text-align: center; margin-bottom: 20pt; }
        h2 { color: #1A3E5C; font-size: 18pt; border-bottom: 1px solid #1A3E5C; margin-top: 20pt; }
        h3 { color: #D4AF37; font-size: 14pt; margin-top: 15pt; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; font-weight: bold; }
        #toc { background-color: #f9f9f9; padding: 20px; margin-bottom: 30pt; border: 1px solid #eee; }
        #toc ul { list-style-type: none; }
        .footer { text-align: center; font-size: 8pt; color: #999; margin-top: 30pt; }
    </style>
    """
    
    # Insérer le CSS dans le head
    if '</head>' in html_content:
        html_content = html_content.replace('</head>', simple_css + '</head>')
    else:
        html_content = f"<html><head>{simple_css}</head><body>{html_content}</body></html>"
    
    return html_content

def html_to_pdf(html_content, output_path=None):
    """
    Convertit du contenu HTML en PDF
    
    Args:
        html_content (str): Le contenu HTML à convertir
        output_path (str, optional): Chemin où sauvegarder le PDF. Si None, retourne les bytes.
    
    Returns:
        bytes or None: Les bytes du PDF si output_path est None, sinon None
    """
    try:
        from xhtml2pdf import pisa
        
        # Nettoyer le HTML pour le rendre compatible avec xhtml2pdf
        html_content = clean_html_for_pdf(html_content)
        
        # Créer un buffer pour le PDF
        if output_path:
            # Sauvegarder directement dans un fichier
            with open(output_path, 'wb') as output_file:
                pisa_status = pisa.CreatePDF(html_content, dest=output_file)
            
            if pisa_status.err:
                print(f"Erreur lors de la conversion PDF: {pisa_status.err}")
                return None
            return None
        else:
            # Retourner les bytes
            pdf_buffer = io.BytesIO()
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
            
            if pisa_status.err:
                print(f"Erreur lors de la conversion PDF: {pisa_status.err}")
                return None
            
            pdf_buffer.seek(0)
            return pdf_buffer.read()
    
    except ImportError:
        print("Erreur: xhtml2pdf n'est pas installé.")
        print("Installez-le avec: pip install xhtml2pdf")
        return None
    except Exception as e:
        print(f"Erreur lors de la conversion PDF: {e}")
        return None
