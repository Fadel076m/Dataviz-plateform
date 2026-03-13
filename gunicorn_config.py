"""
gunicorn_config.py — Configuration Gunicorn pour la production
Référence : https://docs.gunicorn.org/en/stable/configure.html
"""

import os

# ── Serveur ──────────────────────────────────────────────────
bind    = f"0.0.0.0:{os.getenv('PORT', '5000')}"
workers = 1           # Limité à 1 pour économiser la RAM sur le plan Free
threads = 2           # Réduit également pour limiter l'empreinte mémoire

# ── Timeouts ─────────────────────────────────────────────────
timeout       = 120   # 2 min : important pour le chargement du CSV Energy (~3 MB)
keepalive     = 5
graceful_timeout = 30

# ── Performances ─────────────────────────────────────────────
preload_app   = True  # Charger l'app une seule fois, partagée entre workers
worker_class  = "sync"

# ── Logs ─────────────────────────────────────────────────────
loglevel      = "info"
accesslog     = "-"   # stdout
errorlog      = "-"   # stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s'
