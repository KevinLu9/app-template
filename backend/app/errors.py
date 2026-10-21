"""JSON error responses. Clients get a safe message and the request ID; details go to logs."""

import logging

from databricks.sdk.errors import DatabricksError, NotFound, PermissionDenied, Unauthenticated
from flask import Flask, g, request
from werkzeug.exceptions import HTTPException

log = logging.getLogger(__name__)


def _error(status: int, code: str, message: str):
    return {"error": {"code": code, "message": message, "request_id": g.get("request_id")}}, status


def init_error_handlers(app: Flask) -> None:
    @app.errorhandler(HTTPException)
    def _http_error(exc: HTTPException):
        if not request.path.startswith("/api/"):
            return exc
        code = (exc.name or "error").lower().replace(" ", "_")
        return _error(exc.code or 500, code, exc.description or exc.name)

    @app.errorhandler(DatabricksError)
    def _databricks_error(exc: DatabricksError):
        # Map Databricks API failures without leaking their (sometimes detailed) messages.
        log.warning("Databricks API error: %s", exc)
        if isinstance(exc, PermissionDenied | Unauthenticated):
            return _error(403, "forbidden", "Databricks denied access for this identity.")
        if isinstance(exc, NotFound):
            return _error(404, "not_found", "Databricks resource not found.")
        return _error(502, "upstream_error", "A Databricks request failed.")

    @app.errorhandler(Exception)
    def _unhandled(exc: Exception):
        log.exception("Unhandled error on %s %s", request.method, request.path)
        return _error(500, "internal_error", "Something went wrong.")
