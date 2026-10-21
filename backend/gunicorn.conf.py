"""Gunicorn settings for Databricks Apps (see app.yaml)."""

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
chdir = str(BACKEND_DIR)
sys.path.insert(0, str(BACKEND_DIR))

bind = f"0.0.0.0:{os.environ.get('DATABRICKS_APP_PORT', '8000')}"
worker_class = "gthread"
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))
threads = int(os.environ.get("GUNICORN_THREADS", "4"))
timeout = 120  # warehouse queries can be slow to start
graceful_timeout = 30
accesslog = "-"
# Never log request headers: they carry the user's access token.
access_log_format = '%(h)s "%(r)s" %(s)s %(b)s %(L)ss'


def on_starting(server):
    """Runs once in the master process before workers start."""
    from app.config import get_settings

    if get_settings().run_migrations_on_start:
        from app.db.migrate import upgrade_to_head

        server.log.info("Applying database migrations")
        upgrade_to_head()
