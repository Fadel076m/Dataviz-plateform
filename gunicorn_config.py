"""
gunicorn_config.py — Configuration Gunicorn pour la production
Référence : https://docs.gunicorn.org/en/stable/configure.html
"""

import os

# ── Serveur ──────────────────────────────────────────────────
bind    = f"0.0.0.0:{os.getenv('PORT', '5000')}"
workers = 2           # 2 workers pour les dashboards multi-datasources
threads = 4           # 4 threads par worker (I/O bound : MongoDB, CSV)

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
