"""
Module de configuration et de connexion à MongoDB Atlas
Auteur : Fadel ADAM - Projet BCEAO - Data Engineering
Étape 1 : Ingestion
"""

import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()


class MongoDBConnection:
    """Classe pour gérer la connexion à MongoDB Atlas"""
    
    def __init__(self, environment='dev'):
        """
        Initialise la connexion MongoDB
        
        Args:
            environment (str): 'dev' pour banque_dev ou 'prod' pour banque_prod
        """
        self.uri = os.getenv('MONGODB_URI')
        
        if not self.uri:
            raise ValueError("[ERR] MONGODB_URI non trouvé dans le fichier .env")
        
        # Sélectionner la base de données selon l'environnement
        if environment == 'dev':
            self.db_name = os.getenv('DB_DEV', 'banque_dev')
        elif environment == 'prod':
            self.db_name = os.getenv('DB_PROD', 'banque_prod')
        else:
            raise ValueError("[ERR] Environment doit être 'dev' ou 'prod'")
        
        self.collection_name = os.getenv('COLLECTION_NAME', 'performances_bancaires')
        self.client = None
        self.db = None
        self.collection = None
    
    def connect(self):
        """
        Établit la connexion à MongoDB Atlas
        
        Returns:
            bool: True si la connexion réussit, False sinon
        """
        try:
            print(f"[RUN] Connexion à MongoDB Atlas ({self.db_name})...")
            
            # Créer le client MongoDB
            self.client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=5000  # Timeout de 5 secondes
            )
            
            # Tester la connexion
            self.client.admin.command('ping')
            
            # Accéder à la base de données et à la collection
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            
            print(f"[OK] Connexion réussie à {self.db_name}.{self.collection_name}")
            return True
            
        except ConnectionFailure as e:
            print(f"[ERREUR] Echec de la connexion a MongoDB : {e}")
            return False
        except ServerSelectionTimeoutError:
            print("[ERREUR] Timeout : Impossible de joindre MongoDB Atlas")
            print("   Verifiez votre connexion internet et les parametres reseau dans Atlas")
            return False
        except Exception as e:
            print(f"[ERREUR] Erreur inattendue : {e}")
            return False
    
    def get_collection(self, collection_name=None):
        """
        Retourne la collection MongoDB
        
        Args:
            collection_name (str, optional): Nom de la collection à récupérer. 
                                           Si None, utilise la collection par défaut.

        Returns:
            Collection: L'objet collection MongoDB
        """
        if self.client is None:
             raise Exception("[ERR] Pas de connexion active. Appelez d'abord connect()")
             
        if collection_name:
            return self.db[collection_name]
            
        return self.collection
    
    def close(self):
        """Ferme la connexion MongoDB"""
        if self.client:
            self.client.close()
            print("[OK] Connexion MongoDB fermée")
    
    def get_stats(self):
        """
        Affiche les statistiques de la base de données
        
        Returns:
            dict: Statistiques de la collection
        """
        if self.collection is None:
            return None
        
        count = self.collection.count_documents({})
        stats = {
            'database': self.db_name,
            'collection': self.collection_name,
            'nombre_documents': count
        }
        
        print(f"\n[STATS] Statistiques de la base :")
        print(f"   Base : {stats['database']}")
        print(f"   Collection : {stats['collection']}")
        print(f"   Documents : {stats['nombre_documents']}")
        
        return stats


def test_connection():
    """Fonction pour tester la connexion MongoDB"""
    print("=" * 60)
    print("TEST DE CONNEXION MONGODB ATLAS")
    print("=" * 60)
    
    # Tester l'environnement de développement
    mongo = MongoDBConnection(environment='dev')
    
    if mongo.connect():
        mongo.get_stats()
        mongo.close()
        return True
    else:
        print("\n[WARN] Vérifiez :")
        print("   1. Le fichier .env existe et contient MONGODB_URI")
        print("   2. Vos identifiants MongoDB sont corrects")
        print("   3. L'accès réseau est configuré dans MongoDB Atlas")
        return False


if __name__ == "__main__":
    # Exécuter le test si le script est lancé directement
    test_connection()
