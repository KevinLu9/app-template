from typing import TypeVar

from flask import Request, abort
from pydantic import BaseModel, ValidationError

M = TypeVar("M", bound=BaseModel)


def parse_body(model: type[M], request: Request) -> M:
    """Validate a JSON request body against a pydantic model (400 on failure)."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        abort(400, description="Request body must be a JSON object.")
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        fields = ", ".join(".".join(map(str, e["loc"])) or "body" for e in exc.errors())
        abort(400, description=f"Invalid fields: {fields}")
