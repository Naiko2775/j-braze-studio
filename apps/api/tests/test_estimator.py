"""Tests pour l'estimateur de data points Braze."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.data_model.estimator import (
    estimate_data_points,
    _is_free_attribute,
    _get_frequency_multiplier,
)
from services.data_model.demo_data import DEMO_RESULTS
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ── Tests unitaires de l'estimateur ──


def test_free_attributes_are_identified():
    """Les attributs standard Braze doivent etre identifies comme gratuits."""
    free_attrs = [
        "email", "first_name", "last_name", "home_city", "country",
        "date_of_birth", "gender", "language", "phone_number",
        "push_token", "time_zone", "phone", "city",
    ]
    for attr in free_attrs:
        assert _is_free_attribute(attr), f"{attr} devrait etre gratuit"


def test_custom_attributes_are_not_free():
    """Les custom attributes ne doivent PAS etre identifies comme gratuits."""
    custom_attrs = [
        "loyalty_tier", "cart_value", "onboarding_completed",
        "signup_source", "points_to_next_tier",
    ]
    for attr in custom_attrs:
        assert not _is_free_attribute(attr), f"{attr} ne devrait pas etre gratuit"


def test_frequency_multipliers():
    """Les multiplicateurs de frequence doivent etre corrects."""
    assert _get_frequency_multiplier("once") < 1
    assert _get_frequency_multiplier("monthly") == 1
    assert _get_frequency_multiplier("weekly") > 1
    assert _get_frequency_multiplier("daily") == 30


def test_estimate_with_demo_data():
    """Test de l'estimation avec les donnees de demo."""
    result = estimate_data_points(
        analysis_result=DEMO_RESULTS,
        user_volume=100_000,
    )

    # Structure de base
    assert "summary" in result
    assert "breakdown" in result
    assert "recommendations" in result
    assert "cost_estimate" in result

    # Summary
    summary = result["summary"]
    assert summary["custom_attributes_count"] > 0
    assert summary["custom_events_count"] > 0
    assert summary["free_attributes_count"] > 0
    assert summary["total_monthly_data_points"] > 0
    assert summary["total_yearly_data_points"] == summary["total_monthly_data_points"] * 12

    # Breakdown
    breakdown = result["breakdown"]
    assert len(breakdown["custom_attributes"]) > 0
    assert len(breakdown["custom_events"]) > 0

    # Verifier que des attributs gratuits existent dans le breakdown
    free_attrs = [a for a in breakdown["custom_attributes"] if a["is_free"]]
    assert len(free_attrs) > 0, "Devrait avoir des attributs gratuits"

    # Verifier que les attributs gratuits ont 0 data points
    for fa in free_attrs:
        assert fa["monthly_data_points"] == 0

    # Verifier que les attributs payants ont des data points > 0
    paid_attrs = [a for a in breakdown["custom_attributes"] if not a["is_free"]]
    assert len(paid_attrs) > 0, "Devrait avoir des attributs payants"
    for pa in paid_attrs:
        assert pa["monthly_data_points"] > 0


def test_estimate_scales_with_user_volume():
    """Les data points doivent scaler proportionnellement avec le nombre d'utilisateurs."""
    result_small = estimate_data_points(
        analysis_result=DEMO_RESULTS, user_volume=10_000,
    )
    result_large = estimate_data_points(
        analysis_result=DEMO_RESULTS, user_volume=100_000,
    )

    assert (
        result_large["summary"]["total_monthly_data_points"]
        > result_small["summary"]["total_monthly_data_points"]
    )
    # Le ratio devrait etre environ 10x
    ratio = (
        result_large["summary"]["total_monthly_data_points"]
        / result_small["summary"]["total_monthly_data_points"]
    )
    assert 9 <= ratio <= 11, f"Ratio attendu ~10, obtenu {ratio}"


def test_estimate_with_custom_frequencies():
    """Les frequences personnalisees doivent etre prises en compte."""
    result_default = estimate_data_points(
        analysis_result=DEMO_RESULTS,
        user_volume=100_000,
    )
    result_daily = estimate_data_points(
        analysis_result=DEMO_RESULTS,
        user_volume=100_000,
        update_frequency={"profile": "daily", "behavior": "daily", "purchase": "daily"},
    )

    # Tout en daily devrait couter plus cher
    assert (
        result_daily["summary"]["total_monthly_data_points"]
        >= result_default["summary"]["total_monthly_data_points"]
    )


def test_recommendations_generated():
    """Des recommandations doivent etre generees."""
    result = estimate_data_points(
        analysis_result=DEMO_RESULTS,
        user_volume=100_000,
    )
    assert len(result["recommendations"]) > 0


def test_cost_estimate_present():
    """L'estimation de cout doit etre presente et coherente."""
    result = estimate_data_points(
        analysis_result=DEMO_RESULTS,
        user_volume=100_000,
    )
    cost = result["cost_estimate"]
    assert "tier" in cost
    assert "estimated_monthly_cost_range" in cost
    assert "note" in cost


def test_empty_analysis_returns_zeros():
    """Une analyse vide doit retourner des zeros."""
    result = estimate_data_points(
        analysis_result={"use_case_analysis": []},
        user_volume=100_000,
    )
    assert result["summary"]["total_monthly_data_points"] == 0
    assert result["summary"]["custom_attributes_count"] == 0
    assert result["summary"]["custom_events_count"] == 0


# ── Tests de l'endpoint ──


def test_estimate_endpoint_with_analysis_result():
    """L'endpoint doit accepter un analysis_result inline."""
    response = client.post(
        "/api/data-model/estimate-data-points",
        json={
            "analysis_result": DEMO_RESULTS,
            "user_volume": 100_000,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "breakdown" in data
    assert data["summary"]["total_monthly_data_points"] > 0


def test_estimate_endpoint_missing_data():
    """L'endpoint doit retourner 400 si aucune donnee n'est fournie."""
    response = client.post(
        "/api/data-model/estimate-data-points",
        json={"user_volume": 100_000},
    )
    assert response.status_code == 400


def test_estimate_endpoint_invalid_volume():
    """L'endpoint doit rejeter un volume utilisateur invalide."""
    response = client.post(
        "/api/data-model/estimate-data-points",
        json={
            "analysis_result": DEMO_RESULTS,
            "user_volume": 0,
        },
    )
    assert response.status_code == 400
