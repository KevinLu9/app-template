"""Who is calling? Identity comes ONLY from headers set by the Databricks Apps proxy.

The proxy authenticates every request, strips any client-supplied X-Forwarded-* values and
sets its own. The app is not reachable except through the proxy, so these headers can be
trusted in Databricks. Never accept identity from anywhere else (query params, body, cookies).

Locally there is no proxy, so a stub user from LOCAL_DEV_USER_* is used when APP_ENV=local.
"""

from dataclasses import dataclass, field

from flask import abort, current_app, g, request

from app.config import Settings

HEADER_EMAIL = "X-Forwarded-Email"
HEADER_USER_ID = "X-Forwarded-User"
HEADER_USERNAME = "X-Forwarded-Preferred-Username"
# Present only when user authorization (user_api_scopes) is enabled for the app.
HEADER_ACCESS_TOKEN = "X-Forwarded-Access-Token"  # noqa: S105 - header name, not a secret


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    email: str
    display_name: str
    # The user's OAuth token for on-behalf-of calls. repr=False keeps it out of logs and
    # tracebacks. Never return it to the browser, persist it, or share it across requests.
    access_token: str | None = field(default=None, repr=False)
    # Only populated by the local stub; in Databricks use auth.groups.get_user_groups().
    local_groups: frozenset[str] | None = None

    def to_public_dict(self) -> dict:
        return {"user_id": self.user_id, "email": self.email, "display_name": self.display_name}


def _settings() -> Settings:
    return current_app.config["SETTINGS"]


def _from_headers() -> CurrentUser | None:
    email = request.headers.get(HEADER_EMAIL)
    user_id = request.headers.get(HEADER_USER_ID)
    if not email or not user_id:
        return None
    return CurrentUser(
        user_id=user_id,
        email=email,
        display_name=request.headers.get(HEADER_USERNAME) or email,
        access_token=request.headers.get(HEADER_ACCESS_TOKEN) or None,
    )


def _local_stub(settings: Settings) -> CurrentUser:
    groups = {g.strip() for g in settings.local_dev_user_groups.split(",") if g.strip()}
    return CurrentUser(
        user_id=f"local:{settings.local_dev_user_email}",
        email=settings.local_dev_user_email or "",
        display_name=settings.local_dev_user_name,
        access_token=None,
        local_groups=frozenset(groups),
    )


def get_current_user() -> CurrentUser | None:
    """The authenticated user for this request, or None. Cached per request."""
    if "current_user" not in g:
        settings = _settings()
        g.current_user = _local_stub(settings) if settings.local_auth_enabled else _from_headers()
    return g.current_user


def current_user() -> CurrentUser:
    """The authenticated user; aborts with 401 if there is none."""
    user = get_current_user()
    if user is None:
        abort(401, description="Not authenticated.")
    return user
