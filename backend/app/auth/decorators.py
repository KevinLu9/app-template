"""Route-level access control.

Every /api route requires an authenticated user by default (enforced in app/api/__init__.py).
Use @public to opt a route out, and @require_group for app-level authorization.
"""

from collections.abc import Callable
from functools import wraps
from typing import TypeVar

from flask import abort

from app.auth.groups import get_user_groups
from app.auth.identity import current_user

F = TypeVar("F", bound=Callable)


def public(view: F) -> F:
    """Mark a route as reachable without an identity (e.g. health checks)."""
    view.is_public = True  # type: ignore[attr-defined]
    return view


def require_group(*groups: str) -> Callable[[F], F]:
    """Allow the request only if the user belongs to at least one of `groups`.

    Group membership is looked up as the user (OBO), so it needs the
    `iam.current-user:read` scope, which Databricks grants by default.
    """

    def decorator(view: F) -> F:
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not set(groups) & get_user_groups(user):
                abort(403, description="You do not have access to this resource.")
            return view(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
