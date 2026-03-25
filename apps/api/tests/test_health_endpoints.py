"""Tests pour les endpoints health specifiques (claude, braze, database) et app-config."""
import os

from fastapi.testclient import TestClient

from models.db import get_db
from models.app_config import AppConfig
from main import app

client = TestClient(app)


def _get_test_db():
    """Recupere une session DB via le dependency override actif."""
    gen = app.dependency_overrides.get(get_db, get_db)()
    db = next(gen)
    return db, gen


def _clear_app_config():
    """Supprime toutes les entrees app_config via la session de test active."""
    db, gen = _get_test_db()
    try:
        db.query(AppConfig).delete()
        db.commit()
    finally:
        try:
            next(gen)
        except StopIteration:
            pass


# ---------------------------------------------------------------------------
# /api/health/claude
# ---------------------------------------------------------------------------

class TestHealthClaude:

    def test_health_claude_ok_when_key_set(self):
        old = os.environ.get("ANTHROPIC_API_KEY")
        os.environ["ANTHROPIC_API_KEY"] = "sk-test-fake"
        try:
            resp = client.get("/api/health/claude")
            assert resp.status_code == 200
            body = resp.json()
            assert body["status"] == "ok"
            assert body["service"] == "claude"
        finally:
            if old is not None:
                os.environ["ANTHROPIC_API_KEY"] = old
            else:
                os.environ.pop("ANTHROPIC_API_KEY", None)

    def test_health_claude_error_when_key_missing(self):
        old = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            resp = client.get("/api/health/claude")
            assert resp.status_code == 200
            body = resp.json()
            assert body["status"] == "error"
            assert body["service"] == "claude"
            assert "ANTHROPIC_API_KEY" in body["detail"]
        finally:
            if old is not None:
                os.environ["ANTHROPIC_API_KEY"] = old


# ---------------------------------------------------------------------------
# /api/health/braze
# ---------------------------------------------------------------------------

class TestHealthBraze:

    def test_health_braze_ok_when_keys_set(self):
        old_key = os.environ.get("BRAZE_API_KEY")
        old_url = os.environ.get("BRAZE_API_URL")
        os.environ["BRAZE_API_KEY"] = "fake-braze-key"
        os.environ["BRAZE_API_URL"] = "https://rest.iad-01.braze.com"
        try:
            resp = client.get("/api/health/braze")
            assert resp.status_code == 200
            body = resp.json()
            assert body["status"] == "ok"
            assert body["service"] == "braze"
        finally:
            if old_key is not None:
                os.environ["BRAZE_API_KEY"] = old_key
            else:
                os.environ.pop("BRAZE_API_KEY", None)
            if old_url is not None:
                os.environ["BRAZE_API_URL"] = old_url
            else:
                os.environ.pop("BRAZE_API_URL", None)

    def test_health_braze_error_when_keys_missing(self):
        old_key = os.environ.pop("BRAZE_API_KEY", None)
        old_url = os.environ.pop("BRAZE_API_URL", None)
        try:
            resp = client.get("/api/health/braze")
            assert resp.status_code == 200
            body = resp.json()
            assert body["status"] == "error"
            assert body["service"] == "braze"
            assert "BRAZE_API_KEY" in body["detail"]
            assert "BRAZE_API_URL" in body["detail"]
        finally:
            if old_key is not None:
                os.environ["BRAZE_API_KEY"] = old_key
            if old_url is not None:
                os.environ["BRAZE_API_URL"] = old_url


# ---------------------------------------------------------------------------
# /api/health/database
# ---------------------------------------------------------------------------

class TestHealthDatabase:

    def test_health_database_ok(self):
        resp = client.get("/api/health/database")
        assert resp.status_code == 200
        body = resp.json()
        assert body["service"] == "database"
        assert body["status"] in ("ok", "error")


# ---------------------------------------------------------------------------
# /api/app-config
# ---------------------------------------------------------------------------

class TestAppConfig:

    def test_get_empty_config(self):
        _clear_app_config()
        resp = client.get("/api/app-config")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_post_creates_config(self):
        _clear_app_config()
        resp = client.post("/api/app-config", json={"key": "theme", "value": "dark"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["key"] == "theme"
        assert body["value"] == "dark"
        assert "updated_at" in body

    def test_get_returns_created_config(self):
        _clear_app_config()
        client.post("/api/app-config", json={"key": "lang", "value": "fr"})
        resp = client.get("/api/app-config")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 1
        assert items[0]["key"] == "lang"
        assert items[0]["value"] == "fr"

    def test_post_upserts_existing_config(self):
        _clear_app_config()
        client.post("/api/app-config", json={"key": "model", "value": "v1"})
        resp = client.post("/api/app-config", json={"key": "model", "value": "v2"})
        assert resp.status_code == 200
        assert resp.json()["value"] == "v2"

        items = client.get("/api/app-config").json()
        assert len(items) == 1
        assert items[0]["value"] == "v2"

    def test_post_multiple_keys(self):
        _clear_app_config()
        client.post("/api/app-config", json={"key": "a", "value": "1"})
        client.post("/api/app-config", json={"key": "b", "value": "2"})
        items = client.get("/api/app-config").json()
        assert len(items) == 2
        keys = {item["key"] for item in items}
        assert keys == {"a", "b"}
