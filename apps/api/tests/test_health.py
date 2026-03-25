"""Tests pour le health check endpoint."""
from fastapi.testclient import TestClient


def test_health_returns_200():
    from main import app
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_health_contains_modules():
    from main import app
    client = TestClient(app)
    response = client.get("/api/health")
    body = response.json()
    assert "modules" in body
    assert "data_model" in body["modules"]
    assert "liquid" in body["modules"]
    assert "migration" in body["modules"]
