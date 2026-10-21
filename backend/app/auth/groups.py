"""Resolve the current user's Databricks groups (cached for the duration of the request)."""

from flask import g

from app.auth.clients import obo_workspace_client
from app.auth.identity import CurrentUser


def get_user_groups(user: CurrentUser) -> frozenset[str]:
    if user.local_groups is not None:
        return user.local_groups
    if "user_groups" not in g:
        me = obo_workspace_client().current_user.me()
        g.user_groups = frozenset(grp.display for grp in (me.groups or []) if grp.display)
    return g.user_groups
