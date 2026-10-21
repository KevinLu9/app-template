"""All JSON endpoints live under /api. Authentication is required unless a view is @public."""

from flask import Blueprint, abort, current_app, request

from app.api import examples, health, items, me
from app.auth.identity import get_current_user

api = Blueprint("api", __name__, url_prefix="/api")


@api.before_request
def _require_authentication() -> None:
    view = current_app.view_functions.get(request.endpoint or "")
    if view is None or getattr(view, "is_public", False):
        return
    if get_current_user() is None:
        abort(401, description="Not authenticated.")


for module in (health, me, items, examples):
    api.register_blueprint(module.bp)
