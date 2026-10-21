"""Business logic for items. Routes stay thin; rules and data access live here."""

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from werkzeug.exceptions import Forbidden, NotFound

from app.auth.identity import CurrentUser
from app.models import Item


class ItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class ItemUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


def list_items(session: Session) -> list[Item]:
    return list(session.scalars(select(Item).order_by(Item.created_at.desc()).limit(500)))


def get_item(session: Session, item_id: int) -> Item:
    item = session.get(Item, item_id)
    if item is None:
        raise NotFound("Item not found.")
    return item


def create_item(session: Session, data: ItemCreate, user: CurrentUser) -> Item:
    # created_by comes from the trusted identity, never from the request body.
    item = Item(name=data.name, description=data.description, created_by=user.email)
    session.add(item)
    session.commit()
    return item


def update_item(session: Session, item_id: int, data: ItemUpdate, user: CurrentUser) -> Item:
    item = _owned_item(session, item_id, user)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    session.commit()
    session.refresh(item)
    return item


def delete_item(session: Session, item_id: int, user: CurrentUser) -> None:
    item = _owned_item(session, item_id, user)
    session.delete(item)
    session.commit()


def _owned_item(session: Session, item_id: int, user: CurrentUser) -> Item:
    # The app reads Lakebase as its service principal, so row-level rules are enforced here.
    item = get_item(session, item_id)
    if item.created_by != user.email:
        raise Forbidden("Only the creator can change this item.")
    return item
