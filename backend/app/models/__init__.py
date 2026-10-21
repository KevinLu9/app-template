"""Import every model here so Alembic autogenerate can see it."""

from app.models.item import Item

__all__ = ["Item"]
