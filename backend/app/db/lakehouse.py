"""SQLAlchemy engines for the Lakehouse (Databricks SQL warehouse via Unity Catalog).

sp_engine()       runs queries as the app's service principal. Cached and pooled.
obo_connection()  runs queries as the signed-in user, so Unity Catalog permissions apply
                  to them. A new unpooled engine per request, because the token is per user.

Always use bound parameters (sqlalchemy.text(...) with :params). Never format user input into
SQL, and pick table or column names from an allow-list, never from the request.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from typing import Any

from sqlalchemy import URL, Connection, Engine, create_engine
from sqlalchemy.pool import NullPool

from app.auth.clients import sp_config, user_access_token
from app.config import get_settings


def _url() -> URL:
    settings = get_settings()
    if not settings.databricks_warehouse_id:
        raise RuntimeError(
            "DATABRICKS_WAREHOUSE_ID is not set. Add a sql_warehouse resource to the app "
            "(or set it in .env locally)."
        )
    query = {"http_path": f"/sql/1.0/warehouses/{settings.databricks_warehouse_id}"}
    if settings.lakehouse_catalog:
        query["catalog"] = settings.lakehouse_catalog
    if settings.lakehouse_schema:
        query["schema"] = settings.lakehouse_schema
    hostname = sp_config().host.removeprefix("https://").rstrip("/")
    return URL.create("databricks", host=hostname, query=query)


@lru_cache
def sp_engine() -> Engine:
    cfg = sp_config()
    return create_engine(
        _url(),
        # The SDK supplies (and refreshes) credentials; no token is embedded in the URL.
        connect_args={"credentials_provider": lambda: cfg.authenticate},
        pool_pre_ping=True,
    )


def _obo_engine(token: str) -> Engine:
    return create_engine(_url(), connect_args={"access_token": token}, poolclass=NullPool)


@contextmanager
def obo_connection() -> Iterator[Connection]:
    """A connection acting as the current user. Locally, falls back to your CLI profile."""
    token = user_access_token()
    if token is None:
        with sp_engine().connect() as conn:
            yield conn
        return
    engine = _obo_engine(token)
    try:
        with engine.connect() as conn:
            yield conn
    finally:
        engine.dispose()


def rows_as_dicts(result: Any) -> list[dict[str, Any]]:
    return [dict(row._mapping) for row in result]
