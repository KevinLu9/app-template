import pytest

from tests.conftest import OTHER_USER, USER

pytestmark = pytest.mark.db


def test_item_lifecycle(client, db):
    created = client.post("/api/items", json={"name": "  First  "}, headers=USER)
    assert created.status_code == 201
    item = created.json
    assert item["name"] == "First"
    assert item["created_by"] == "alice@example.com"

    listed = client.get("/api/items", headers=USER).json["items"]
    assert [i["id"] for i in listed] == [item["id"]]

    updated = client.patch(f"/api/items/{item['id']}", json={"name": "Renamed"}, headers=USER)
    assert updated.status_code == 200
    assert updated.json["name"] == "Renamed"

    assert client.delete(f"/api/items/{item['id']}", headers=USER).status_code == 204
    assert client.get(f"/api/items/{item['id']}", headers=USER).status_code == 404


def test_created_by_cannot_be_spoofed(client, db):
    response = client.post(
        "/api/items", json={"name": "x", "created_by": "mallory@example.com"}, headers=USER
    )
    assert response.status_code == 400


def test_only_creator_can_modify(client, db):
    item = client.post("/api/items", json={"name": "Mine"}, headers=USER).json
    assert client.delete(f"/api/items/{item['id']}", headers=OTHER_USER).status_code == 403
    assert (
        client.patch(f"/api/items/{item['id']}", json={"name": "x"}, headers=OTHER_USER).status_code
        == 403
    )


def test_validation_errors(client, db):
    assert client.post("/api/items", json={"name": ""}, headers=USER).status_code == 400
    assert client.post("/api/items", json=["not", "an", "object"], headers=USER).status_code == 400
