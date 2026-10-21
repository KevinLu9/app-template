"""Application settings, read from environment variables (and `.env` locally).

In Databricks Apps, the platform injects DATABRICKS_* variables and the Lakebase resource
injects PG* variables; app.yaml sets the rest. Locally, `.env` provides them.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    # "production" is the default so that a missing variable never weakens security.
    app_env: Literal["local", "test", "production"] = "production"
    log_level: str = "INFO"

    # Injected by Databricks Apps. DATABRICKS_APP_NAME being set means "running in Databricks".
    databricks_app_name: str | None = None
    databricks_host: str | None = None
    databricks_config_profile: str | None = None

    # Lakebase / Postgres. Locally DATABASE_URL points at `npm run db:up`; in Databricks the
    # PG* variables come from the database resource and the password is an OAuth token.
    database_url: str | None = None
    db_schema: str = Field(default="app", pattern=r"^[a-z_][a-z0-9_]*$")
    pghost: str | None = None
    pgport: int = 5432
    pgdatabase: str | None = None
    pguser: str | None = None
    pgsslmode: str = "require"
    run_migrations_on_start: bool = False

    # Lakehouse (SQL warehouse). The ID comes from the sql_warehouse app resource.
    databricks_warehouse_id: str | None = None
    lakehouse_catalog: str | None = None
    lakehouse_schema: str | None = None

    # Local identity stub (see auth/identity.py). Ignored unless app_env == "local".
    local_dev_user_email: str | None = None
    local_dev_user_name: str = "Local Developer"
    local_dev_user_groups: str = ""

    frontend_dist: Path = PROJECT_ROOT / "frontend" / "dist"
    max_request_bytes: int = 1 * 1024 * 1024

    @property
    def is_databricks(self) -> bool:
        return bool(self.databricks_app_name)

    @property
    def local_auth_enabled(self) -> bool:
        return self.app_env == "local" and bool(self.local_dev_user_email)

    @model_validator(mode="after")
    def _refuse_dev_modes_in_databricks(self) -> "Settings":
        # Fail closed: a deployed app must never trust a local identity stub.
        if self.is_databricks and self.app_env != "production":
            raise ValueError(
                f"APP_ENV={self.app_env!r} is not allowed when running in Databricks Apps."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
