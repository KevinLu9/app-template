"""Request-scoped ORM sessions for Lakebase."""

from flask import Flask, g
from sqlalchemy.orm import Session, sessionmaker

from app.db.lakebase import get_engine

_session_factory = sessionmaker(expire_on_commit=False)


def db_session() -> Session:
    """The Session for the current request. Commit explicitly; it is closed at teardown."""
    if "db_session" not in g:
        g.db_session = _session_factory(bind=get_engine())
    return g.db_session


def init_db_session(app: Flask) -> None:
    @app.teardown_appcontext
    def _close_session(exc: BaseException | None) -> None:
        session = g.pop("db_session", None)
        if session is not None:
            if exc is not None:
                session.rollback()
            session.close()
