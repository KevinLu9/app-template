import logging

from databricks.sdk.errors import DatabricksError
from flask import Blueprint
from werkzeug.exceptions import Forbidden

from app.auth.groups import get_user_groups
from app.auth.identity import current_user

bp = Blueprint("me", __name__)
log = logging.getLogger(__name__)


@bp.get("/me")
def me():
    user = current_user()
    try:
        groups: list[str] | None = sorted(get_user_groups(user))
    except (DatabricksError, Forbidden) as exc:
        # Group lookup needs user authorization; the app still works without it.
        log.warning("Could not resolve groups for current user: %s", type(exc).__name__)
        groups = None
    return {**user.to_public_dict(), "groups": groups}
