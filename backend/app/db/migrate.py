from alembic import command
from alembic.config import Config

from app.config import BACKEND_DIR


def upgrade_to_head() -> None:
    command.upgrade(Config(str(BACKEND_DIR / "alembic.ini")), "head")
