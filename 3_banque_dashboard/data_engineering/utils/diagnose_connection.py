"""
Script de diagnostic de connexion MongoDB
Objectif : Isoler la cause de l'échec de connexion (DNS, Réseau, Auth)
"""
import socket
import sys
import os
import time
from pathlib import Path
from urllib.parse import urlparse
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, ConfigurationError
from dotenv import load_dotenv

# Charger l'environnement
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
print(f"📂 Chargement .env depuis : {env_path}")
load_dotenv(env_path)

def diagnose():
    print("=" * 60)
    print("🕵️ DIAGNOSTIC CONNEXION MONGODB")
    print("=" * 60)
    
    uri = os.getenv('MONGODB_URI')
    if not uri:
        print("❌ CRITIQUE : Variable MONGODB_URI manquante !")
        return

    # 1. Analyse de l'URI (sans afficher mot de passe)
    try:
        parsed = urlparse(uri)
        masked_netloc = parsed.netloc.split('@')[-1] if '@' in parsed.netloc else parsed.netloc
        print(f"🔗 Cible : {masked_netloc}")
        print(f"   Scheme : {parsed.scheme}")
    except Exception as e:
        print(f"⚠️ Erreur parsing URI : {e}")

    # 2. Test DNS
    print("\n🌍 Test Résolution DNS...")
    if '+' in parsed.scheme: # ex: mongodb+srv://
        print("   Mode SRV détecté, saut du test DNS simple (compliqué à scripter rapidement)")
    else:
        host = parsed.hostname
        port = parsed.port or 27017
        try:
            ip = socket.gethostbyname(host)
            print(f"   ✅ OK : {host} -> {ip}")
            
            # 3. Test TCP
            print(f"\n🔌 Test Connexion TCP ({host}:{port})...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            if result == 0:
                print("   ✅ Port ouvert")
            else:
                print(f"   ❌ Port fermé ou bloqué (Code {result})")
            sock.close()
        except Exception as e:
            print(f"   ❌ Erreur DNS/TCP : {e}")

    # 4. Test PyMongo
    print("\n🐍 Test Client PyMongo...")
    try:
        # Timeout très court pour voir vite l'erreur
        client = MongoClient(uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
        start = time.time()
        info = client.server_info() # Force la connexion
        ping = (time.time() - start) * 1000
        print(f"   ✅ Connexion RÉUSSIE en {ping:.2f}ms")
        print(f"   Version Serveur : {info.get('version')}")
        
    except ServerSelectionTimeoutError as e:
        print("   ❌ TIMEOUT : Le serveur ne répond pas.")
        print("   Causes possibles :")
        print("   - IP non autorisée (Allowlist Atlas)")
        print("   - Pare-feu entreprise/VPN bloquant le port 27017")
        print("   - Connexion internet instable")
        print(f"   Détail : {e}")
    except ConnectionFailure as e:
        print(f"   ❌ ECHEC AUTH/CONNEXION : {e}")
    except ConfigurationError as e:
        print(f"   ❌ ERREUR CONFIG : {e}")
    except Exception as e:
        print(f"   ❌ ERREUR INCONNUE : {type(e).__name__} - {e}")

if __name__ == "__main__":
    diagnose()
