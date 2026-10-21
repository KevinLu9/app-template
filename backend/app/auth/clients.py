"""Databricks SDK clients for the two ways an app can call Databricks.

SERVICE PRINCIPAL (app authorization)
    The app's own identity. Databricks injects DATABRICKS_CLIENT_ID / DATABRICKS_CLIENT_SECRET /
    DATABRICKS_HOST and the SDK picks them up. Use it for app-owned data and background work.
    Everyone using the app sees the same data, so YOU must enforce who may see what.

ON-BEHALF-OF USER (user authorization)
    The signed-in user's identity, via the X-Forwarded-Access-Token header. Unity Catalog
    permissions apply to the real user. Requires `user_api_scopes` on the app.

Locally there is no service principal or forwarded token: both clients use your
~/.databrickscfg profile (DATABRICKS_CONFIG_PROFILE), i.e. everything runs as you.
"""

from functools import lru_cache

from databricks.sdk import WorkspaceClient
from databricks.sdk.core import Config
from flask import abort, current_app

from app.auth.identity import current_user


@lru_cache
def sp_config() -> Config:
    """SDK config for the app's service principal (or your CLI profile locally)."""
    return Config()


@lru_cache
def sp_workspace_client() -> WorkspaceClient:
    return WorkspaceClient(config=sp_config())


def obo_workspace_client() -> WorkspaceClient:
    """A client acting as the current user. Build one per request; never cache it."""
    token = user_access_token()
    if token is None:
        return sp_workspace_client()  # local development only, see user_access_token()
    return WorkspaceClient(host=sp_config().host, token=token, auth_type="pat")


def user_access_token() -> str | None:
    """The forwarded user token. None (meaning "use your profile") only in local development."""
    user = current_user()
    if user.access_token:
        return user.access_token
    if current_app.config["SETTINGS"].app_env == "local":
        return None
    abort(403, description="User authorization is not enabled for this app.")
