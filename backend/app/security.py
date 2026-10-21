"""HTTP security hardening applied to every response, plus a same-origin check for writes.

There is deliberately no CORS: the frontend is served from the same origin as the API.
"""

import secrets
from urllib.parse import urlsplit

from flask import Flask, abort, g, request

CONTENT_SECURITY_POLICY = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline'",  # Radix/shadcn set inline styles for positioning
        "img-src 'self' data:",
        "font-src 'self' data:",
        "connect-src 'self'",
        "frame-ancestors 'self'",
        "base-uri 'self'",
        "form-action 'self'",
        "object-src 'none'",
    ]
)

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def _request_origin() -> str:
    # Behind the Databricks Apps proxy the public host arrives in X-Forwarded-Host.
    host = request.headers.get("X-Forwarded-Host") or request.host
    return host.lower()


def init_security(app: Flask) -> None:
    @app.before_request
    def _assign_request_id() -> None:
        # X-Request-Id is set by the Databricks proxy; generate one locally.
        g.request_id = request.headers.get("X-Request-Id") or secrets.token_hex(8)

    @app.before_request
    def _same_origin_writes() -> None:
        """Defence in depth against CSRF on state-changing API calls."""
        if request.method in SAFE_METHODS or not request.path.startswith("/api/"):
            return
        origin = request.headers.get("Origin")
        if origin and urlsplit(origin).netloc.lower() != _request_origin():
            abort(403, description="Cross-origin request rejected.")
        if request.content_length and not request.is_json:
            abort(415, description="Expected application/json.")

    @app.after_request
    def _security_headers(response):
        h = response.headers
        h.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY)
        h.setdefault("X-Content-Type-Options", "nosniff")
        h.setdefault("X-Frame-Options", "SAMEORIGIN")
        h.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        h.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        h["X-Request-Id"] = g.get("request_id", "")
        if request.path.startswith("/api/"):
            h["Cache-Control"] = "no-store"
        return response
