"""Reference CRUD endpoints on Lakebase. Copy this shape for new resources:
route (HTTP + validation) -> service (rules + data access) -> model."""

from flask import Blueprint, request

from app.auth.identity import current_user
from app.db.session import db_session
from app.services import items as service
from app.validation import parse_body

bp = Blueprint("items", __name__, url_prefix="/items")


@bp.get("")
def list_items():
    return {"items": [item.to_dict() for item in service.list_items(db_session())]}


@bp.post("")
def create_item():
    data = parse_body(service.ItemCreate, request)
    item = service.create_item(db_session(), data, current_user())
    return item.to_dict(), 201


@bp.get("/<int:item_id>")
def get_item(item_id: int):
    return service.get_item(db_session(), item_id).to_dict()


@bp.patch("/<int:item_id>")
def update_item(item_id: int):
    data = parse_body(service.ItemUpdate, request)
    return service.update_item(db_session(), item_id, data, current_user()).to_dict()


@bp.delete("/<int:item_id>")
def delete_item(item_id: int):
    service.delete_item(db_session(), item_id, current_user())
    return "", 204
