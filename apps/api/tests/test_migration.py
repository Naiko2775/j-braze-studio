"""Tests pour le module Migration (taches 23-27)."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from services.migration.models import Contact, ContactAttribute
from services.migration.connectors.demo import DemoConnector
from services.migration.connectors.csv_connector import CsvConnector
from services.migration.mappers.brevo_mapper import BrevoMapper
from services.migration.mappers.demo_mapper import DemoMapper
from services.migration.mappers.csv_mapper import CsvMapper
from services.migration.exporters.braze import BrazeExporter, deduplicate_contacts_by_email
from services.migration.engine import MigrationEngine


# ── Task 23: Connectors ──────────────────────────────────────────────


def test_demo_connector_test_connection():
    connector = DemoConnector({})
    assert connector.test_connection() is True


def test_demo_connector_fetch_contacts():
    connector = DemoConnector({"contact_count": 10})
    contacts = connector.fetch_contacts()
    assert len(contacts) == 10
    assert all(isinstance(c, Contact) for c in contacts)


def test_demo_connector_fetch_contacts_with_limit():
    connector = DemoConnector({"contact_count": 100})
    contacts = connector.fetch_contacts(limit=5)
    assert len(contacts) == 5


def test_demo_connector_fetch_segments():
    connector = DemoConnector({})
    segments = connector.fetch_segments()
    assert len(segments) > 0


def test_demo_connector_fetch_templates():
    connector = DemoConnector({})
    templates = connector.fetch_templates()
    assert len(templates) > 0


def test_csv_connector_fetch_contacts():
    csv_data = "id,email,first_name,last_name,phone,city\n1,a@test.com,Alice,Martin,+33600000000,Paris\n2,b@test.com,Bob,Dupont,+33600000001,Lyon"
    connector = CsvConnector({"csv_data": csv_data})
    contacts = connector.fetch_contacts()
    assert len(contacts) == 2
    assert contacts[0].email == "a@test.com"
    assert contacts[0].first_name == "Alice"
    # city should be a custom attribute
    city_attrs = [a for a in contacts[0].custom_attributes if a.key == "city"]
    assert len(city_attrs) == 1
    assert city_attrs[0].value == "Paris"


def test_csv_connector_test_connection():
    csv_data = "id,email,name\n1,a@test.com,Alice"
    connector = CsvConnector({"csv_data": csv_data})
    assert connector.test_connection() is True


def test_csv_connector_invalid_config():
    with pytest.raises(ValueError):
        CsvConnector({})


def test_csv_connector_with_limit():
    csv_data = "id,email\n1,a@test.com\n2,b@test.com\n3,c@test.com"
    connector = CsvConnector({"csv_data": csv_data})
    contacts = connector.fetch_contacts(limit=2)
    assert len(contacts) == 2


def test_csv_connector_empty_segments():
    connector = CsvConnector({"csv_data": "id,email\n1,a@test.com"})
    assert connector.fetch_segments() == []
    assert connector.fetch_templates() == []
    assert connector.fetch_events() == []


# ── Task 24: Mappers ─────────────────────────────────────────────────


def test_brevo_mapper_sms_blacklisted_not_on_push():
    """Bug fix: smsBlacklisted ne doit PAS affecter push_subscribe.
    Le mapping doit cibler un Subscription Group SMS via sms_subscription_status."""
    contact = Contact(
        external_id="test_1",
        email="test@example.com",
        push_subscribe="subscribed",
        custom_attributes=[],
    )
    mapper = BrevoMapper()
    transformed = mapper.transform_contact(contact)
    # push_subscribe ne doit pas etre modifie par smsBlacklisted
    assert transformed.push_subscribe == "subscribed"


def test_brevo_mapper_remap_attributes():
    contact = Contact(
        external_id="test_1",
        custom_attributes=[
            ContactAttribute(key="loyalty_points", value=100, type="number"),
        ],
    )
    mapper = BrevoMapper(field_mapping={"loyalty_points": "braze_loyalty_pts"})
    transformed = mapper.transform_contact(contact)
    assert transformed.custom_attributes[0].key == "braze_loyalty_pts"


def test_demo_mapper_transform_contact():
    contact = Contact(
        external_id="test_1",
        custom_attributes=[
            ContactAttribute(key="lifetime_value", value=500, type="number"),
        ],
    )
    mapper = DemoMapper()
    transformed = mapper.transform_contact(contact)
    assert transformed.custom_attributes[0].key == "lifetime_value"


def test_csv_mapper_passthrough():
    contact = Contact(
        external_id="test_1",
        email="a@test.com",
        custom_attributes=[
            ContactAttribute(key="city", value="Paris", type="string"),
        ],
    )
    mapper = CsvMapper()
    transformed = mapper.transform_contact(contact)
    assert transformed.email == "a@test.com"
    assert transformed.custom_attributes[0].key == "city"


def test_csv_mapper_remap():
    contact = Contact(
        external_id="test_1",
        custom_attributes=[
            ContactAttribute(key="ville", value="Paris", type="string"),
        ],
    )
    mapper = CsvMapper(field_mapping={"ville": "city"})
    transformed = mapper.transform_contact(contact)
    assert transformed.custom_attributes[0].key == "city"


# ── Task 25: BrazeExporter ───────────────────────────────────────────


def test_dry_run_mode():
    exporter = BrazeExporter({"api_key": "test", "dry_run": True})
    contacts = [
        Contact(external_id="1", email="a@test.com"),
        Contact(external_id="2", email="b@test.com"),
    ]
    result = exporter.export_contacts(contacts)
    assert result["success"] == 2
    assert result["failed"] == 0


def test_deduplicate_by_email():
    contacts = [
        Contact(external_id="1", email="a@test.com"),
        Contact(external_id="2", email="b@test.com"),
        Contact(external_id="3", email="a@test.com"),  # doublon
    ]
    deduped = deduplicate_contacts_by_email(contacts)
    assert len(deduped) == 2
    emails = {c.email for c in deduped}
    assert emails == {"a@test.com", "b@test.com"}


def test_deduplicate_preserves_latest():
    """La deduplication doit garder le contact avec l'updated_at le plus recent."""
    contacts = [
        Contact(external_id="1", email="a@test.com", first_name="Old", updated_at=datetime(2024, 1, 1)),
        Contact(external_id="2", email="a@test.com", first_name="New", updated_at=datetime(2025, 1, 1)),
    ]
    deduped = deduplicate_contacts_by_email(contacts)
    assert len(deduped) == 1
    assert deduped[0].first_name == "New"


def test_deduplicate_no_email():
    """Les contacts sans email sont gardes tels quels."""
    contacts = [
        Contact(external_id="1", email=None),
        Contact(external_id="2", email=None),
        Contact(external_id="3", email="a@test.com"),
    ]
    deduped = deduplicate_contacts_by_email(contacts)
    assert len(deduped) == 3


def test_exporter_filters_sms_opt_out():
    """Le marker _sms_opt_out ne doit pas etre envoye comme attribut Braze."""
    exporter = BrazeExporter({"api_key": "test", "dry_run": True})
    contact = Contact(
        external_id="1",
        email="a@test.com",
        custom_attributes=[
            ContactAttribute(key="_sms_opt_out", value=True, type="boolean"),
            ContactAttribute(key="city", value="Paris", type="string"),
        ],
    )
    attrs = exporter._contact_to_braze_attributes(contact)
    assert "_sms_opt_out" not in attrs
    assert attrs["city"] == "Paris"


# ── Task 26: Engine ──────────────────────────────────────────────────


def test_engine_init_demo():
    engine = MigrationEngine(
        source_platform="demo",
        source_config={"contact_count": 10},
        braze_config={"api_key": "test", "dry_run": True},
    )
    assert engine.source_platform == "demo"


def test_engine_test_connections_demo():
    engine = MigrationEngine(
        source_platform="demo",
        source_config={"contact_count": 10},
        braze_config={"api_key": "test", "dry_run": True},
    )
    result = engine.test_connections()
    assert result["source"] is True


def test_engine_run_dry_run():
    engine = MigrationEngine(
        source_platform="demo",
        source_config={"contact_count": 5},
        braze_config={"api_key": "test", "dry_run": True},
    )
    result = engine.run(contact_limit=5)
    assert "contacts" in result
    assert result["contacts"]["success"] == 5


def test_engine_run_with_deduplication():
    engine = MigrationEngine(
        source_platform="demo",
        source_config={"contact_count": 10},
        braze_config={"api_key": "test", "dry_run": True},
    )
    result = engine.run(contact_limit=10, deduplicate_by_email=True)
    assert "contacts" in result
    assert result["contacts"]["success"] >= 1


def test_engine_invalid_platform():
    with pytest.raises(ValueError):
        MigrationEngine(
            source_platform="unknown",
            source_config={},
            braze_config={"api_key": "test"},
        )


def test_engine_csv_platform():
    csv_data = "id,email,first_name\n1,a@test.com,Alice\n2,b@test.com,Bob"
    engine = MigrationEngine(
        source_platform="csv",
        source_config={"csv_data": csv_data},
        braze_config={"api_key": "test", "dry_run": True},
    )
    result = engine.run()
    assert result["contacts"]["success"] == 2


def test_engine_warmup_dry_run():
    engine = MigrationEngine(
        source_platform="demo",
        source_config={"contact_count": 20},
        braze_config={"api_key": "test", "dry_run": True},
    )
    result = engine.run_warmup(stages=[50, 100])
    assert result.total_contacts == 20
    assert result.total_success == 20
    assert len(result.stages) == 2


def test_engine_warmup_should_stop():
    engine = MigrationEngine(
        source_platform="demo",
        source_config={"contact_count": 20},
        braze_config={"api_key": "test", "dry_run": True},
    )
    call_count = {"n": 0}

    def should_stop():
        call_count["n"] += 1
        return call_count["n"] >= 2  # Stop after second stage

    result = engine.run_warmup(stages=[10, 50, 100], should_stop=should_stop)
    assert result.stop_reason == "Arret manuel demande"


# ── Task 27: Router ──────────────────────────────────────────────────


def test_get_platforms():
    from main import app
    client = TestClient(app)
    response = client.get("/api/migration/platforms")
    assert response.status_code == 200
    data = response.json()
    assert "demo" in [p["id"] for p in data]
    assert "csv" in [p["id"] for p in data]
    assert "brevo" in [p["id"] for p in data]
    assert "salesforce_mc" in [p["id"] for p in data]


def test_test_connection_demo():
    from main import app
    client = TestClient(app)
    response = client.post("/api/migration/test-connection", json={
        "platform": "demo",
        "source_config": {},
        "braze_config": {"api_key": "test", "dry_run": True},
    })
    assert response.status_code == 200
    data = response.json()
    assert data["source"] is True


def test_preview_demo():
    from main import app
    client = TestClient(app)
    response = client.post("/api/migration/preview/demo", json={"limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["contacts_count"] == 5
    assert "sample" in data


def test_preview_demo_with_credentials_body():
    """FAIL #1 fix: preview accepts POST with body (credentials, limit, deduplicate_by_email)."""
    from main import app
    client = TestClient(app)
    response = client.post("/api/migration/preview/demo", json={
        "credentials": {},
        "limit": 3,
        "deduplicate_by_email": False,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["contacts_count"] == 3


def test_preview_invalid_platform():
    from main import app
    client = TestClient(app)
    response = client.post("/api/migration/preview/unknown_platform", json={})
    assert response.status_code == 400


def test_run_migration_dry_run():
    from main import app
    client = TestClient(app)
    response = client.post("/api/migration/run", json={
        "platform": "demo",
        "mode": "dry_run",
        "source_config": {"contact_count": 5},
        "braze_config": {"api_key": "test"},
        "contact_limit": 5,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "job_id" in data
    assert data["result"]["contacts"]["success"] == 5


def test_run_migration_warmup():
    from main import app
    client = TestClient(app)
    response = client.post("/api/migration/run", json={
        "platform": "demo",
        "mode": "warmup",
        "source_config": {"contact_count": 10},
        "braze_config": {"api_key": "test", "dry_run": True},
        "warmup_stages": [50, 100],
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["result"]["total_success"] == 10


def test_run_migration_with_deduplication():
    from main import app
    client = TestClient(app)
    response = client.post("/api/migration/run", json={
        "platform": "demo",
        "mode": "dry_run",
        "source_config": {"contact_count": 10},
        "braze_config": {"api_key": "test"},
        "deduplicate_by_email": True,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"


def test_get_status_not_found():
    from main import app
    client = TestClient(app)
    response = client.get("/api/migration/status/nonexistent-id")
    assert response.status_code == 404


def test_get_history():
    from main import app
    client = TestClient(app)
    response = client.get("/api/migration/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_test_connection_invalid_platform():
    from main import app
    client = TestClient(app)
    response = client.post("/api/migration/test-connection", json={
        "platform": "unknown",
        "source_config": {},
        "braze_config": {"api_key": "test"},
    })
    assert response.status_code == 400


# ── FAIL #2 fix: test-connection accepts credentials alias ──────────


def test_test_connection_with_credentials_alias():
    """Frontend sends { platform, credentials } instead of { platform, source_config, braze_config }."""
    from main import app
    client = TestClient(app)
    response = client.post("/api/migration/test-connection", json={
        "platform": "demo",
        "credentials": {},
    })
    assert response.status_code == 200
    data = response.json()
    assert data["source"] is True


def test_test_connection_braze_config_optional():
    """braze_config should default from env vars when absent."""
    from main import app
    client = TestClient(app)
    response = client.post("/api/migration/test-connection", json={
        "platform": "demo",
        "source_config": {},
    })
    assert response.status_code == 200


# ── FAIL #3 fix: run migration accepts credentials alias ────────────


def test_run_migration_with_credentials_alias():
    """Frontend sends { platform, credentials, mode, deduplicate_by_email }."""
    from main import app
    client = TestClient(app)
    response = client.post("/api/migration/run", json={
        "platform": "demo",
        "credentials": {"contact_count": 5},
        "mode": "dry_run",
        "deduplicate_by_email": False,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"


def test_run_migration_braze_config_optional():
    """braze_config should default from env vars when absent."""
    from main import app
    client = TestClient(app)
    response = client.post("/api/migration/run", json={
        "platform": "demo",
        "mode": "dry_run",
        "source_config": {"contact_count": 3},
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"


# ── FAIL #7 fix: sfmc alias for salesforce_mc ───────────────────────


def test_engine_sfmc_alias():
    """sfmc should be accepted as an alias for salesforce_mc in the engine."""
    engine = MigrationEngine(
        source_platform="sfmc",
        source_config={"client_id": "x", "client_secret": "y", "subdomain": "z"},
        braze_config={"api_key": "test", "dry_run": True},
    )
    assert engine.source_platform == "sfmc"


def test_preview_sfmc_alias():
    """Preview endpoint should accept sfmc as platform id."""
    from main import app
    client = TestClient(app)
    # sfmc with no credentials will likely fail on connection, but should not return 'unknown platform'
    response = client.post("/api/migration/preview/sfmc", json={"credentials": {"client_id": "x", "client_secret": "y", "subdomain": "z"}, "limit": 1})
    # We expect either 200 or 400 (connection error), but NOT an 'unknown platform' error
    assert response.status_code in (200, 400)
    if response.status_code == 400:
        assert "Unknown platform" not in response.json().get("detail", "")
