import logging

import pytest
from pydantic import ValidationError

from app import create_app
from app.config import Settings
from app.log import redact
from tests.conftest import USER


def test_health_is_public_and_hardened(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Request-Id"]


def test_api_requires_identity_headers(client):
    response = client.get("/api/me")
    assert response.status_code == 401
    assert response.json["error"]["code"] == "unauthorized"


def test_me_returns_identity_but_never_the_token(client, monkeypatch):
    # Group lookup calls Databricks as the user; stub it so the test stays offline.
    monkeypatch.setattr("app.api.me.get_user_groups", lambda user: frozenset({"users"}))
    response = client.get("/api/me", headers={**USER, "X-Forwarded-Access-Token": "secret-tok"})
    assert response.status_code == 200
    assert response.json["email"] == "alice@example.com"
    assert "secret-tok" not in response.get_data(as_text=True)


def test_unknown_api_route_is_404_json(client):
    response = client.get("/api/nope", headers=USER)
    assert response.status_code == 404
    assert response.json["error"]["code"] == "not_found"


def test_cross_origin_write_is_rejected(client):
    response = client.post(
        "/api/items", json={"name": "x"}, headers={**USER, "Origin": "https://evil.example"}
    )
    assert response.status_code == 403


def test_non_json_write_is_rejected(client):
    response = client.post("/api/items", data="name=x", headers=USER)
    assert response.status_code == 415


def test_local_stub_refused_in_databricks():
    with pytest.raises(ValidationError):
        Settings(app_env="local", databricks_app_name="my-app", _env_file=None)


def test_production_is_the_default(monkeypatch):
    monkeypatch.delenv("APP_ENV")  # conftest sets APP_ENV=test
    assert Settings(_env_file=None).app_env == "production"


def test_local_stub_only_in_local_mode():
    settings = Settings(app_env="test", local_dev_user_email="dev@example.com", _env_file=None)
    client = create_app(settings).test_client()
    assert client.get("/api/me").status_code == 401

    settings = Settings(app_env="local", local_dev_user_email="dev@example.com", _env_file=None)
    client = create_app(settings).test_client()
    response = client.get("/api/me")
    assert response.status_code == 200
    assert response.json["email"] == "dev@example.com"


def test_tokens_are_redacted_from_logs(caplog):
    jwt = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxIn0.c2lnbmF0dXJl"
    pat = "dapi" + "0123456789abcdef" * 2
    assert redact(f"token={jwt} pat={pat}") == "token=*** pat=***"

    from app.log import RedactingFilter

    record = logging.LogRecord("t", logging.INFO, "", 0, "auth %s", (jwt,), None)
    RedactingFilter().filter(record)
    assert jwt not in record.getMessage()
