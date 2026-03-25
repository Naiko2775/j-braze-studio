"""Tests pour le module Liquid Generator (templates, generator, router)."""
import json
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.db import Base, get_db
from main import app


# ---------------------------------------------------------------------------
# Test DB setup -- in-memory SQLite shared across this module
# Using StaticPool ensures all connections share the same in-memory DB.
# ---------------------------------------------------------------------------

_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(_test_engine)
_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


def _override_get_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


def _reset_tables():
    """Drop and recreate all tables between tests that write to DB."""
    Base.metadata.drop_all(_test_engine)
    Base.metadata.create_all(_test_engine)


def _remove_api_key():
    """Remove ANTHROPIC_API_KEY from env, return old value."""
    return os.environ.pop("ANTHROPIC_API_KEY", None)


def _restore_api_key(old_key):
    """Restore ANTHROPIC_API_KEY if it was set."""
    if old_key is not None:
        os.environ["ANTHROPIC_API_KEY"] = old_key


def _make_claude_mock(response_json: dict):
    """Build a mock Anthropic client that returns the given JSON."""
    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = json.dumps(response_json)

    mock_response = MagicMock()
    mock_response.content = [mock_block]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    return mock_client


SAMPLE_CLAUDE_RESULT = {
    "template": "hero_banner",
    "params": {
        "headline": "Test headline",
        "cta_text": "Click",
        "cta_url": "/test",
        "bg_color": "#040066",
        "text_color": "#ffffff",
        "cta_color": "#f00a0a",
    },
    "liquid_code": "<div>test</div>",
    "personalization_notes": "Aucune",
    "ab_variants": [
        {"variant": "A", "headline": "Test A", "rationale": "Reason A"},
        {"variant": "B", "headline": "Test B", "rationale": "Reason B"},
    ],
}


# ---------------------------------------------------------------------------
# Tests services/liquid/templates.py
# ---------------------------------------------------------------------------

class TestTemplatesService:

    def test_get_templates_returns_all(self):
        from services.liquid.templates import get_templates
        templates = get_templates()
        # 5 banners + 5 emails + 1 push + 1 sms = 12
        assert len(templates) == 12

    def test_get_templates_banner_keys(self):
        from services.liquid.templates import get_templates
        templates = get_templates(category="banner")
        keys = {t["key"] for t in templates}
        assert keys == {"hero_banner", "product_card", "countdown", "cta_simple", "testimonial"}

    def test_get_templates_email_keys(self):
        from services.liquid.templates import get_templates
        templates = get_templates(category="email")
        keys = {t["key"] for t in templates}
        assert keys == {
            "welcome_email",
            "abandoned_cart_email",
            "loyalty_email",
            "post_purchase_email",
            "winback_email",
        }

    def test_get_templates_push_keys(self):
        from services.liquid.templates import get_templates
        templates = get_templates(category="push")
        assert len(templates) == 1
        assert templates[0]["key"] == "push_notification"

    def test_get_templates_sms_keys(self):
        from services.liquid.templates import get_templates
        templates = get_templates(category="sms")
        assert len(templates) == 1
        assert templates[0]["key"] == "sms_message"

    def test_get_templates_filter_banner(self):
        from services.liquid.templates import get_templates
        templates = get_templates(category="banner")
        assert len(templates) == 5
        for t in templates:
            assert t["category"] == "banner"

    def test_get_templates_filter_email(self):
        from services.liquid.templates import get_templates
        templates = get_templates(category="email")
        assert len(templates) == 5
        for t in templates:
            assert t["category"] == "email"

    def test_get_templates_filter_nonexistent_category(self):
        from services.liquid.templates import get_templates
        templates = get_templates(category="nonexistent")
        assert templates == []

    def test_get_template_existing(self):
        from services.liquid.templates import get_template
        tpl = get_template("hero_banner")
        assert tpl is not None
        assert tpl["key"] == "hero_banner"
        assert tpl["name"] == "Hero Banner"
        assert "structure" in tpl
        assert "required" in tpl["structure"]

    def test_get_template_nonexistent(self):
        from services.liquid.templates import get_template
        assert get_template("nonexistent") is None

    def test_template_has_example_brief(self):
        from services.liquid.templates import get_templates
        for tpl in get_templates():
            assert "example_brief" in tpl, f"Template {tpl['key']} missing example_brief"
            assert len(tpl["example_brief"]) > 10

    def test_each_template_has_structure_fields(self):
        from services.liquid.templates import get_templates
        for tpl in get_templates():
            assert "structure" in tpl
            assert "required" in tpl["structure"]
            assert "optional" in tpl["structure"]
            assert isinstance(tpl["structure"]["required"], list)
            assert len(tpl["structure"]["required"]) > 0

    def test_each_template_has_category(self):
        from services.liquid.templates import get_templates
        for tpl in get_templates():
            assert "category" in tpl, f"Template {tpl['key']} missing category"
            assert tpl["category"] in {"banner", "email", "push", "sms"}

    def test_email_templates_have_html_skeleton(self):
        from services.liquid.templates import get_templates
        for tpl in get_templates(category="email"):
            assert "html_skeleton" in tpl, f"Email template {tpl['key']} missing html_skeleton"
            assert len(tpl["html_skeleton"]) > 100
            # Must use tables for email compatibility
            assert "<table" in tpl["html_skeleton"], f"{tpl['key']} should use HTML tables"
            # Must have unsubscribe link
            assert "subscription_management_url" in tpl["html_skeleton"], (
                f"{tpl['key']} should have unsubscribe link"
            )

    def test_email_templates_use_tables_not_flex(self):
        from services.liquid.templates import get_templates
        for tpl in get_templates(category="email"):
            skeleton = tpl["html_skeleton"]
            assert "display:flex" not in skeleton and "display: flex" not in skeleton, (
                f"{tpl['key']} should NOT use flex layout in emails"
            )

    def test_email_templates_have_responsive_media_queries(self):
        from services.liquid.templates import get_templates
        for tpl in get_templates(category="email"):
            assert "@media" in tpl["html_skeleton"], (
                f"{tpl['key']} should have responsive media queries"
            )

    def test_email_templates_have_valid_liquid_syntax(self):
        from services.liquid.templates import get_templates
        for tpl in get_templates(category="email"):
            skeleton = tpl["html_skeleton"]
            # Check balanced Liquid tags
            assert skeleton.count("{% if") == skeleton.count("{% endif %}"), (
                f"{tpl['key']} has unbalanced if/endif"
            )
            assert skeleton.count("{% for") == skeleton.count("{% endfor %}"), (
                f"{tpl['key']} has unbalanced for/endfor"
            )

    def test_push_template_has_html_skeleton(self):
        from services.liquid.templates import get_template
        tpl = get_template("push_notification")
        assert tpl is not None
        assert "html_skeleton" in tpl
        assert "title" in tpl["html_skeleton"]
        assert "deep_link" in tpl["html_skeleton"]

    def test_sms_template_has_html_skeleton(self):
        from services.liquid.templates import get_template
        tpl = get_template("sms_message")
        assert tpl is not None
        assert "html_skeleton" in tpl
        assert "STOP" in tpl["html_skeleton"]

    def test_welcome_email_has_liquid_personalization(self):
        from services.liquid.templates import get_template
        tpl = get_template("welcome_email")
        assert tpl is not None
        skeleton = tpl["html_skeleton"]
        assert "${first_name}" in skeleton
        assert "default:" in skeleton
        assert "gender" in skeleton

    def test_abandoned_cart_email_has_product_loop(self):
        from services.liquid.templates import get_template
        tpl = get_template("abandoned_cart_email")
        assert tpl is not None
        skeleton = tpl["html_skeleton"]
        assert "{% for item in" in skeleton
        assert "connected_content" in skeleton

    def test_loyalty_email_has_tier_conditions(self):
        from services.liquid.templates import get_template
        tpl = get_template("loyalty_email")
        assert tpl is not None
        skeleton = tpl["html_skeleton"]
        assert "loyalty_tier" in skeleton
        assert "Gold" in skeleton
        assert "Silver" in skeleton
        assert "Bronze" in skeleton

    def test_winback_email_has_promo_and_expiry(self):
        from services.liquid.templates import get_template
        tpl = get_template("winback_email")
        assert tpl is not None
        skeleton = tpl["html_skeleton"]
        assert "promo_code" in skeleton
        assert "last_purchase_date" in skeleton
        assert "-20%" in skeleton

    def test_post_purchase_email_has_order_and_nps(self):
        from services.liquid.templates import get_template
        tpl = get_template("post_purchase_email")
        assert tpl is not None
        skeleton = tpl["html_skeleton"]
        assert "order_id" in skeleton
        assert "nps_url" in skeleton
        assert "cross_sell" in skeleton or "Vous aimerez aussi" in skeleton


# ---------------------------------------------------------------------------
# Tests services/liquid/generator.py
# ---------------------------------------------------------------------------

class TestGeneratorService:

    def test_demo_mode_without_api_key(self):
        """Sans ANTHROPIC_API_KEY, retourne un resultat mock."""
        old_key = _remove_api_key()
        try:
            from services.liquid.generator import generate_banner
            result = generate_banner("Test brief")
            assert result["model_used"] == "demo"
            assert result["template"] == "hero_banner"
            assert "params" in result
            assert "liquid_code" in result
            assert "ab_variants" in result
        finally:
            _restore_api_key(old_key)

    def test_demo_result_has_required_keys(self):
        """Le resultat demo a toutes les cles attendues."""
        old_key = _remove_api_key()
        try:
            from services.liquid.generator import generate_banner
            result = generate_banner("Test brief")
            assert "personalization_notes" in result
            assert isinstance(result["ab_variants"], list)
            assert len(result["ab_variants"]) == 2
        finally:
            _restore_api_key(old_key)

    @patch("services.claude_client.get_default_model", return_value="claude-sonnet-4-20250514")
    @patch("services.claude_client.get_claude_client")
    def test_generate_banner_calls_claude(self, mock_client_fn, mock_model):
        """Avec une cle API, appelle Claude et parse le JSON."""
        mock_client = _make_claude_mock(SAMPLE_CLAUDE_RESULT)
        mock_client_fn.return_value = mock_client

        os.environ["ANTHROPIC_API_KEY"] = "sk-test-fake-key"
        try:
            from services.liquid.generator import generate_banner
            result = generate_banner("Banniere soldes VIP", template_type="hero_banner")

            assert result["template"] == "hero_banner"
            assert result["params"]["headline"] == "Test headline"
            assert result["model_used"] == "claude-sonnet-4-20250514"

            mock_client.messages.create.assert_called_once()
            call_kwargs = mock_client.messages.create.call_args.kwargs
            assert call_kwargs["max_tokens"] == 4000
            assert "hero_banner" in call_kwargs["messages"][0]["content"]
        finally:
            os.environ.pop("ANTHROPIC_API_KEY", None)

    @patch("services.claude_client.get_default_model", return_value="claude-sonnet-4-20250514")
    @patch("services.claude_client.get_claude_client")
    def test_generate_banner_invalid_json_raises(self, mock_client_fn, mock_model):
        """Si Claude retourne du non-JSON, leve une ValueError."""
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = "Ceci n'est pas du JSON"
        mock_response = MagicMock()
        mock_response.content = [mock_block]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_client_fn.return_value = mock_client

        os.environ["ANTHROPIC_API_KEY"] = "sk-test-fake-key"
        try:
            from services.liquid.generator import generate_banner
            with pytest.raises(ValueError, match="JSON valide"):
                generate_banner("Test brief")
        finally:
            os.environ.pop("ANTHROPIC_API_KEY", None)

    @patch("services.claude_client.get_default_model", return_value="claude-sonnet-4-20250514")
    @patch("services.claude_client.get_claude_client")
    def test_generate_with_channel(self, mock_client_fn, mock_model):
        """Le canal est ajoute au message utilisateur."""
        mock_client = _make_claude_mock(SAMPLE_CLAUDE_RESULT)
        mock_client_fn.return_value = mock_client

        os.environ["ANTHROPIC_API_KEY"] = "sk-test-fake-key"
        try:
            from services.liquid.generator import generate_banner
            generate_banner("Brief test", channel="email")
            call_kwargs = mock_client.messages.create.call_args.kwargs
            assert "email" in call_kwargs["messages"][0]["content"]
        finally:
            os.environ.pop("ANTHROPIC_API_KEY", None)

    def test_system_prompt_mentions_email_templates(self):
        """Le SYSTEM_PROMPT mentionne les templates email."""
        from services.liquid.generator import SYSTEM_PROMPT
        assert "welcome_email" in SYSTEM_PROMPT
        assert "abandoned_cart_email" in SYSTEM_PROMPT
        assert "loyalty_email" in SYSTEM_PROMPT
        assert "post_purchase_email" in SYSTEM_PROMPT
        assert "winback_email" in SYSTEM_PROMPT

    def test_system_prompt_mentions_push_sms(self):
        """Le SYSTEM_PROMPT mentionne les templates push et SMS."""
        from services.liquid.generator import SYSTEM_PROMPT
        assert "push_notification" in SYSTEM_PROMPT
        assert "sms_message" in SYSTEM_PROMPT

    def test_system_prompt_email_rules(self):
        """Le SYSTEM_PROMPT contient les regles email (tables, responsive)."""
        from services.liquid.generator import SYSTEM_PROMPT
        assert "TABLES" in SYSTEM_PROMPT or "tables" in SYSTEM_PROMPT
        assert "Outlook" in SYSTEM_PROMPT or "outlook" in SYSTEM_PROMPT
        assert "responsive" in SYSTEM_PROMPT or "media queries" in SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Tests router /api/liquid/*
# ---------------------------------------------------------------------------

class TestLiquidRouter:

    def test_get_templates(self):
        response = client.get("/api/liquid/templates")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 12
        keys = {t["key"] for t in data}
        assert "hero_banner" in keys
        assert "testimonial" in keys
        assert "welcome_email" in keys
        assert "push_notification" in keys
        assert "sms_message" in keys

    def test_get_templates_filter_banner(self):
        response = client.get("/api/liquid/templates?category=banner")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        for t in data:
            assert t["category"] == "banner"

    def test_get_templates_filter_email(self):
        response = client.get("/api/liquid/templates?category=email")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        for t in data:
            assert t["category"] == "email"

    def test_get_templates_filter_push(self):
        response = client.get("/api/liquid/templates?category=push")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == "push"

    def test_get_templates_filter_sms(self):
        response = client.get("/api/liquid/templates?category=sms")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == "sms"

    def test_get_templates_filter_empty(self):
        response = client.get("/api/liquid/templates?category=unknown")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_history_empty(self):
        _reset_tables()
        response = client.get("/api/liquid/history")
        assert response.status_code == 200
        assert response.json() == []

    def test_generate_demo_mode(self):
        """POST /generate en mode demo (pas de cle API)."""
        _reset_tables()
        old_key = _remove_api_key()
        try:
            response = client.post(
                "/api/liquid/generate",
                json={"brief": "Banniere soldes VIP", "project_name": "Test"},
            )
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "result" in data
            assert data["result"]["model_used"] == "demo"
            assert data["result"]["template"] == "hero_banner"
        finally:
            _restore_api_key(old_key)

    def test_generate_persists_to_db(self):
        """POST /generate sauvegarde en BDD et GET /history le retrouve."""
        _reset_tables()
        old_key = _remove_api_key()
        try:
            resp = client.post(
                "/api/liquid/generate",
                json={
                    "brief": "Test persistance",
                    "template_type": "countdown",
                    "channel": "email",
                    "project_name": "Projet X",
                },
            )
            assert resp.status_code == 200
            gen_id = resp.json()["id"]

            resp_history = client.get("/api/liquid/history")
            assert resp_history.status_code == 200
            items = resp_history.json()
            assert len(items) == 1
            assert items[0]["id"] == gen_id
            assert items[0]["brief"] == "Test persistance"
            assert items[0]["project_name"] == "Projet X"

            resp_detail = client.get(f"/api/liquid/history/{gen_id}")
            assert resp_detail.status_code == 200
            detail = resp_detail.json()
            assert detail["id"] == gen_id
            assert detail["result"] is not None
            assert detail["channel"] == "email"
        finally:
            _restore_api_key(old_key)

    def test_generate_empty_brief_422(self):
        response = client.post(
            "/api/liquid/generate",
            json={"brief": "   "},
        )
        assert response.status_code == 422

    def test_history_detail_not_found(self):
        _reset_tables()
        response = client.get("/api/liquid/history/nonexistent-id")
        assert response.status_code == 404

    @patch("services.claude_client.get_default_model", return_value="claude-sonnet-4-20250514")
    @patch("services.claude_client.get_claude_client")
    def test_generate_with_claude_mock(self, mock_client_fn, mock_model):
        """POST /generate avec mock Claude complet."""
        _reset_tables()
        cta_result = {
            "template": "cta_simple",
            "params": {
                "headline": "Offre speciale",
                "cta_text": "En profiter",
                "cta_url": "/promo",
                "bg_color": "#040066",
                "text_color": "#ffffff",
                "cta_color": "#f00a0a",
            },
            "liquid_code": "<div>promo</div>",
            "personalization_notes": "Aucune variable Liquid",
            "ab_variants": [],
        }
        mock_client = _make_claude_mock(cta_result)
        mock_client_fn.return_value = mock_client

        os.environ["ANTHROPIC_API_KEY"] = "sk-test-fake-key"
        try:
            resp = client.post(
                "/api/liquid/generate",
                json={"brief": "Promo flash", "template_type": "cta_simple"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["result"]["template"] == "cta_simple"
            assert data["result"]["params"]["headline"] == "Offre speciale"
        finally:
            os.environ.pop("ANTHROPIC_API_KEY", None)

    def test_history_returns_most_recent_first(self):
        """L'historique est trie par date decroissante."""
        _reset_tables()
        old_key = _remove_api_key()
        try:
            client.post("/api/liquid/generate", json={"brief": "Premier brief"})
            client.post("/api/liquid/generate", json={"brief": "Second brief"})

            resp = client.get("/api/liquid/history")
            items = resp.json()
            assert len(items) == 2
            assert items[0]["brief"] == "Second brief"
            assert items[1]["brief"] == "Premier brief"
        finally:
            _restore_api_key(old_key)
