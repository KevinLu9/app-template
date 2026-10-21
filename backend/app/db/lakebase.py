"""SQLAlchemy engine for Lakebase (Databricks managed Postgres).

Locally: DATABASE_URL points at the embedded Postgres started by `npm run db:up`.
In Databricks: the database app resource injects PGHOST/PGPORT/PGDATABASE/PGUSER/PGSSLMODE.
PGUSER is the app service principal; its password is a short-lived (1h) OAuth token, so a
fresh token is fetched for every new connection and pooled connections are recycled
before the token could expire.
"""

from functools import lru_cache

from sqlalchemy import URL, Engine, create_engine, event

from app.auth.clients import sp_config
from app.config import Settings, get_settings

POOL_RECYCLE_SECONDS = 45 * 60


def _service_principal_token() -> str:
    # The SDK caches the token and refreshes it shortly before expiry.
    return sp_config().oauth_token().access_token


def create_lakebase_engine(settings: Settings) -> Engine:
    if settings.database_url:
        return create_engine(settings.database_url, pool_pre_ping=True)

    if not (settings.pghost and settings.pgdatabase and settings.pguser):
        raise RuntimeError(
            "No database configured: set DATABASE_URL locally, or add a Lakebase database "
            "resource to the app so PGHOST/PGDATABASE/PGUSER are injected."
        )

    url = URL.create(
        "postgresql+psycopg",
        username=settings.pguser,
        host=settings.pghost,
        port=settings.pgport,
        database=settings.pgdatabase,
        query={"sslmode": settings.pgsslmode},
    )
    engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=POOL_RECYCLE_SECONDS,
        pool_size=5,
        max_overflow=5,
    )

    @event.listens_for(engine, "do_connect")
    def _inject_token(dialect, conn_rec, cargs, cparams):
        cparams["password"] = _service_principal_token()

    return engine


@lru_cache
def get_engine() -> Engine:
    """Process-wide engine, created on first use (after gunicorn forks its workers)."""
    return create_lakebase_engine(get_settings())
