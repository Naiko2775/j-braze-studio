"""Tests pour les endpoints Data Model."""
from fastapi.testclient import TestClient

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app

client = TestClient(app)


def test_get_entities():
    response = client.get("/api/data-model/entities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 10
    assert any(e["name"] == "User Profile" for e in data)


def test_get_entity_by_name():
    response = client.get("/api/data-model/entities/User Profile")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "User Profile"
    assert "attributes" in data


def test_get_entity_not_found():
    response = client.get("/api/data-model/entities/NonExistent")
    assert response.status_code == 404


def test_get_hierarchy():
    response = client.get("/api/data-model/hierarchy")
    assert response.status_code == 200
    data = response.json()
    assert "mermaid" in data
    assert "tree" in data


def test_analyze_demo_mode():
    response = client.post(
        "/api/data-model/analyze",
        json={"use_cases": ["Campagne bienvenue"], "demo": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "result" in data
    assert "use_case_analysis" in data["result"]
