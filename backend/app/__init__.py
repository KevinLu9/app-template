"""Flask application factory."""

from pathlib import Path

from flask import Flask, abort, send_from_directory

from app.config import Settings, get_settings
from app.db.session import init_db_session
from app.errors import init_error_handlers
from app.log import configure_logging
from app.security import init_security


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = Flask(__name__, static_folder=None)
    app.config.update(
        SETTINGS=settings,
        MAX_CONTENT_LENGTH=settings.max_request_bytes,
        JSON_SORT_KEYS=False,
    )

    init_security(app)
    init_error_handlers(app)
    init_db_session(app)

    from app.api import api

    app.register_blueprint(api)
    _register_frontend(app, settings.frontend_dist)
    return app


def _register_frontend(app: Flask, dist: Path) -> None:
    """Serve the built React app. Unknown non-API paths return index.html (client routing).

    Locally the Vite dev server serves the frontend instead, so dist/ may not exist.
    """

    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    def frontend(path: str):
        if path.startswith("api/"):
            abort(404)
        if path and (dist / path).is_file():
            response = send_from_directory(dist, path)
            if path.startswith("assets/"):  # content-hashed by Vite, safe to cache forever
                response.cache_control.max_age = 31536000
                response.cache_control.immutable = True
            return response
        if not (dist / "index.html").is_file():
            abort(404, description="Frontend not built. Use the Vite dev server locally.")
        response = send_from_directory(dist, "index.html")
        response.cache_control.no_cache = True
        return response
