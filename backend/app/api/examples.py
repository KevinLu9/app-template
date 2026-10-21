"""Side-by-side examples of calling Databricks as the user (OBO) vs the service principal (SP).

Compare the "identity" each one reports: OBO returns the signed-in user, SP returns the app.
"""

from flask import Blueprint, request
from sqlalchemy import text

from app.auth.clients import obo_workspace_client, sp_workspace_client
from app.auth.decorators import require_group
from app.db.lakehouse import obo_connection, rows_as_dicts, sp_engine

bp = Blueprint("examples", __name__, url_prefix="/examples")

WHOAMI_SQL = text("SELECT current_user() AS identity, current_timestamp() AS queried_at")

# Table names come from an allow-list, never from the request.
SAMPLE_TABLE = "samples.nyctaxi.trips"
SAMPLE_SQL = text(
    "SELECT tpep_pickup_datetime, trip_distance, fare_amount, pickup_zip "  # noqa: S608
    f"FROM {SAMPLE_TABLE} WHERE trip_distance >= :min_distance LIMIT :limit"
)


def _whoami(client) -> dict:
    me = client.current_user.me()
    return {"identity": me.user_name, "display_name": me.display_name, "id": me.id}


# --- Workspace API (Databricks SDK) ---------------------------------------------------


@bp.get("/obo/whoami")
def obo_whoami():
    return _whoami(obo_workspace_client())


@bp.get("/sp/whoami")
def sp_whoami():
    return _whoami(sp_workspace_client())


# --- Lakehouse (SQL warehouse via SQLAlchemy) -----------------------------------------


@bp.get("/obo/warehouse")
def obo_warehouse():
    with obo_connection() as conn:
        return {"rows": rows_as_dicts(conn.execute(WHOAMI_SQL))}


@bp.get("/sp/warehouse")
def sp_warehouse():
    with sp_engine().connect() as conn:
        return {"rows": rows_as_dicts(conn.execute(WHOAMI_SQL))}


@bp.get("/obo/sample-trips")
def obo_sample_trips():
    """Parameterized query as the user; they need SELECT on the table in Unity Catalog."""
    limit = min(max(request.args.get("limit", 10, type=int), 1), 100)
    min_distance = request.args.get("min_distance", 0.0, type=float)
    with obo_connection() as conn:
        result = conn.execute(SAMPLE_SQL, {"limit": limit, "min_distance": min_distance})
        return {"rows": rows_as_dicts(result)}


# --- App-level authorization ----------------------------------------------------------


@bp.get("/admin-only")
@require_group("app-admins")
def admin_only():
    return {"message": "You are in the app-admins group."}
