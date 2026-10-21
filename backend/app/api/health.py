from flask import Blueprint

from app.auth.decorators import public

bp = Blueprint("health", __name__)


@bp.get("/health")
@public
def health():
    # Liveness only. Do not expose versions, config or dependency details here.
    return {"status": "ok"}
