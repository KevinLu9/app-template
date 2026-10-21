from alembic import context
from sqlalchemy import text

from app.config import get_settings
from app.db.base import Base
from app.db.lakebase import get_engine
from app.models import *  # noqa: F403 - register all models on Base.metadata

target_metadata = Base.metadata


def run_migrations() -> None:
    schema = get_settings().db_schema
    with get_engine().connect() as connection:
        # Each app owns one schema. In Lakebase the app service principal creates it, so it
        # is the owner and needs no further grants.
        connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=schema,
            include_schemas=False,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    raise SystemExit("Offline migrations are not supported; run against a database.")
run_migrations()
