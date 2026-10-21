import os

# Configure the environment before the app (and its cached settings) is imported.
os.environ["APP_ENV"] = "test"
os.environ.pop("DATABRICKS_APP_NAME", None)
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://app:app@127.0.0.1:5432/app_test"
)

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

from app import create_app
from app.config import get_settings

USER = {
    "X-Forwarded-Email": "alice@example.com",
    "X-Forwarded-User": "1001",
    "X-Forwarded-Preferred-Username": "Alice",
}
OTHER_USER = {
    "X-Forwarded-Email": "bob@example.com",
    "X-Forwarded-User": "1002",
    "X-Forwarded-Preferred-Username": "Bob",
}


@pytest.fixture
def app():
    return create_app(get_settings())


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def database():
    """Create (if needed) and migrate the test database. Skips if Postgres isn't running."""
    url = make_url(os.environ["DATABASE_URL"])
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            exists = conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": url.database}
            )
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    except OperationalError:
        if os.environ.get("REQUIRE_TEST_DATABASE"):  # set in CI so DB tests can't be skipped
            raise
        pytest.skip("Postgres is not running (npm run db:up)")
    finally:
        admin.dispose()

    from app.db.migrate import upgrade_to_head

    upgrade_to_head()


@pytest.fixture
def db(database):
    from app.db.lakebase import get_engine

    yield
    with get_engine().begin() as conn:
        conn.execute(text(f'TRUNCATE "{get_settings().db_schema}".items RESTART IDENTITY'))
