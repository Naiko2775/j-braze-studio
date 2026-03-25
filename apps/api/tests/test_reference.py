"""Tests pour le referentiel Braze Data Model."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.data_model.reference import (
    BRAZE_DATA_MODEL,
    get_all_entity_names,
    get_entity,
    get_entities_by_category,
    build_hierarchy,
    get_data_model_prompt,
    get_full_hierarchy_mermaid,
)


def test_data_model_has_all_entities():
    names = get_all_entity_names()
    assert "User Profile" in names
    assert "Custom Attributes" in names
    assert "Custom Events" in names
    assert "Campaign" in names
    assert "Canvas" in names
    assert "Segment" in names
    assert "Content Block" in names
    assert "Catalog" in names
    # Nouvelles entites ajoutees selon la spec
    assert "Feature Flags" in names
    assert "Preference Center" in names
    assert "Canvas Entry Properties" in names


def test_get_entity_existing():
    entity = get_entity("User Profile")
    assert entity is not None
    assert entity["category"] == "core"
    assert "email" in entity["attributes"]


def test_get_entity_missing():
    entity = get_entity("NonExistent")
    assert entity is None


def test_get_entities_by_category():
    core = get_entities_by_category("core")
    assert "User Profile" in core


def test_build_hierarchy():
    hierarchy = build_hierarchy()
    assert "Braze Data Model" in hierarchy
    roots = hierarchy["Braze Data Model"]
    root_names = [r["name"] for r in roots]
    assert "User Profile" in root_names


def test_get_data_model_prompt():
    prompt = get_data_model_prompt()
    assert "User Profile" in prompt
    assert "Feature Flags" in prompt
    assert "Preference Center" in prompt


def test_get_full_hierarchy_mermaid():
    mermaid = get_full_hierarchy_mermaid()
    assert mermaid.startswith("graph TD")
    assert "User Profile" in mermaid or "User<br/>Profile" in mermaid
