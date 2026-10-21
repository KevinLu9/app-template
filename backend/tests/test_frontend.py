from app import create_app
from app.config import Settings


def make_client(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html>spa</html>")
    (tmp_path / "assets" / "app-abc123.js").write_text("console.log(1)")
    settings = Settings(app_env="test", frontend_dist=tmp_path, _env_file=None)
    return create_app(settings).test_client()


def test_spa_fallback_serves_index(tmp_path):
    client = make_client(tmp_path)
    response = client.get("/items/42")
    assert response.status_code == 200
    assert b"spa" in response.data
    assert "no-cache" in response.headers["Cache-Control"]


def test_hashed_assets_are_cached(tmp_path):
    response = make_client(tmp_path).get("/assets/app-abc123.js")
    assert response.status_code == 200
    assert "immutable" in response.headers["Cache-Control"]


def test_path_traversal_is_blocked(tmp_path):
    response = make_client(tmp_path).get("/../../etc/passwd")
    assert b"root:" not in response.data
