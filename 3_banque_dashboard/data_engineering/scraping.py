"""
Script de téléchargement automatique des PDF BCEAO
Étape 2 : Scraping des rapports financiers des banques
Projet BCEAO - Data Engineering
"""

import os
import json
import requests
from pathlib import Path
import time
from urllib.parse import quote


class BCEAOPDFDownloader:
    """Classe pour télécharger les PDF des rapports BCEAO"""
    
    def __init__(self, config_path='../config/pdf_urls.json', output_dir='../data/pdf'):
        """
        Initialise le téléchargeur
        
        Args:
            config_path (str): Chemin vers le fichier de configuration JSON
            output_dir (str): Dossier de destination des PDFs
        """
        self.config_path = config_path
        self.output_dir = output_dir
        self.config = None
        
    def load_config(self):
        """
        Charge la configuration depuis le fichier JSON
        
        Returns:
            bool: True si le chargement réussit
        """
        try:
            print(f"\n📂 Chargement de la configuration : {self.config_path}")
            
            if not os.path.exists(self.config_path):
                print(f"❌ Le fichier de configuration n'existe pas : {self.config_path}")
                return False
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            nb_rapports = len(self.config.get('rapports_annuels', []))
            print(f"✅ Configuration chargée : {nb_rapports} rapport(s) à télécharger")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement de la configuration : {e}")
            return False
    
    def create_directories(self):
        """Crée les dossiers nécessaires pour stocker les PDFs"""
        try:
            print(f"\n📁 Création des dossiers...")
            
            # Créer le dossier principal
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
            
            # Créer un dossier par année
            for rapport in self.config.get('rapports_annuels', []):
                annee = rapport.get('annee')
                if annee:
                    year_dir = os.path.join(self.output_dir, str(annee))
                    Path(year_dir).mkdir(parents=True, exist_ok=True)
                    print(f"   ✅ Dossier créé : {year_dir}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la création des dossiers : {e}")
            return False
    
    def download_pdf(self, url, output_path, timeout=120):
        """
        Télécharge un fichier PDF depuis une URL
        
        Args:
            url (str): URL du PDF
            output_path (str): Chemin de destination
            timeout (int): Timeout en secondes
            
        Returns:
            bool: True si le téléchargement réussit
        """
        try:
            print(f"\n⬇️  Téléchargement depuis : {url}")
            
            # Vérifier si le fichier existe déjà
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                if file_size > 1000:  # Si le fichier fait plus de 1KB
                    print(f"   ℹ️  Fichier déjà existant : {output_path} ({file_size:,} octets)")
                    print(f"   ⏭️  Téléchargement ignoré")
                    return True
            
            # Headers pour simuler un navigateur
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Télécharger le fichier
            response = requests.get(url, headers=headers, timeout=timeout, stream=True)
            response.raise_for_status()
            
            # Sauvegarder le fichier
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f:
                if total_size == 0:
                    # Si la taille n'est pas connue
                    f.write(response.content)
                else:
                    # Téléchargement avec affichage de la progression
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            # Affichage simple de la progression
                            percent = (downloaded / total_size) * 100
                            print(f"\r   📥 Progression : {percent:.1f}% ({downloaded:,} / {total_size:,} octets)", end='')
                    print()  # Nouvelle ligne après la progression
            
            file_size = os.path.getsize(output_path)
            print(f"   ✅ Téléchargement réussi : {output_path}")
            print(f"   📊 Taille : {file_size:,} octets ({file_size / 1024 / 1024:.2f} MB)")
            
            return True
            
        except requests.exceptions.Timeout:
            print(f"   ❌ Timeout : Le serveur met trop de temps à répondre")
            return False
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Erreur de téléchargement : {e}")
            return False
        except Exception as e:
            print(f"   ❌ Erreur inattendue : {e}")
            return False
    
    def download_all(self):
        """
        Télécharge tous les rapports configurés
        
        Returns:
            dict: Statistiques de téléchargement
        """
        print("-" * 80)
        print("TÉLÉCHARGEMENT DES PDF BCEAO")
        print("-" * 80)
        
        if not self.load_config():
            return None
        
        if not self.create_directories():
            return None
        
        rapports = self.config.get('rapports_annuels', [])
        
        stats = {
            'total': len(rapports),
            'success': 0,
            'skipped': 0,
            'failed': 0,
            'errors': []
        }
        
        for i, rapport in enumerate(rapports, 1):
            annee = rapport.get('annee')
            titre = rapport.get('titre', 'Sans titre')
            url = rapport.get('url')
            fichier = rapport.get('fichier', f'rapport_{annee}.pdf')
            statut = rapport.get('statut', 'disponible')
            
            print(f"\nDocument {i}/{stats['total']} : {titre}")
            print(f"   Année : {annee}")
            print(f"   Statut : {statut}")
            
            # Ignorer les rapports à vérifier ou indisponibles
            if statut in ['a_verifier', 'indisponible']:
                print(f"   ⚠️  Statut '{statut}' - Téléchargement ignoré")
                print(f"   💡 Conseil : Vérifiez manuellement l'URL ou cherchez le rapport sur bceao.int")
                stats['skipped'] += 1
                continue
            
            if not url:
                print(f"   ❌ Pas d'URL fournie")
                stats['failed'] += 1
                stats['errors'].append(f"Rapport {annee} : pas d'URL")
                continue
            
            # Construire le chemin de destination
            output_path = os.path.join(self.output_dir, str(annee), fichier)
            
            # Télécharger le PDF
            success = self.download_pdf(url, output_path)
            
            if success:
                stats['success'] += 1
            else:
                stats['failed'] += 1
                stats['errors'].append(f"Rapport {annee} : échec du téléchargement")
            
            # Pause entre les téléchargements pour éviter de surcharger le serveur
            if i < stats['total']:
                time.sleep(2)
        
        # Afficher les statistiques finales
        print("\n" + "=" * 80)
        print("RÉSUMÉ DU TÉLÉCHARGEMENT")
        print("=" * 80)
        print(f"   Total de rapports : {stats['total']}")
        print(f"   ✅ Réussis : {stats['success']}")
        print(f"   ⏭️  Ignorés : {stats['skipped']}")
        print(f"   ❌ Échoués : {stats['failed']}")
        
        if stats['errors']:
            print(f"\n⚠️  Erreurs rencontrées :")
            for error in stats['errors']:
                print(f"   - {error}")
        
        if stats['success'] > 0:
            print(f"\n✅ Les PDF téléchargés sont disponibles dans : {self.output_dir}")
        
        print("=" * 80)
        
        return stats


def main():
    """Fonction principale"""
    
    downloader = BCEAOPDFDownloader()
    stats = downloader.download_all()
    
    if stats and stats['success'] > 0:
        print("\nBravo ! Téléchargement terminé !")
        print(f"   Vous pouvez maintenant passer à l'Étape 3 : Extraction OCR")
    elif stats and stats['failed'] > 0:
        print("\n⚠️  Certains téléchargements ont échoué.")
        print(f"   Vérifiez les URLs dans config/pdf_urls.json")
    elif stats and stats['skipped'] == stats['total']:
        print("\n💡 Tous les rapports ont été ignorés (statut 'a_verifier').")
        print(f"   Pour télécharger manuellement :")
        print(f"   1. Allez sur https://www.bceao.int/fr/publications/recherche")
        print(f"   2. Cherchez 'bilans banques UMOA [année]'")
        print(f"   3. Téléchargez les PDF et placez-les dans data/pdf/[année]/")


if __name__ == "__main__":
    main()
