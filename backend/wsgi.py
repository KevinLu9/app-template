"""WSGI entry: `gunicorn wsgi:app` on Databricks; `flask --app backend/wsgi.py run` locally."""

from app import create_app

app = create_app()
