"""Tests pour les modeles SQLAlchemy et la resolution de DATABASE_URL."""
import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models.db import (
    Base,
    build_connect_args,
    normalize_database_url,
    resolve_database_url,
)
from models.analysis import Analysis
from models.generation import Generation
from models.migration_job import MigrationJob
from models.app_config import AppConfig


def get_test_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def test_analysis_create():
    engine = get_test_engine()
    with Session(engine) as session:
        analysis = Analysis(
            project_name="Test Project",
            use_case="Campagne bienvenue",
            result={"use_case_analysis": []},
            model_used="claude-opus-5",
        )
        session.add(analysis)
        session.commit()
        session.refresh(analysis)

        assert analysis.id is not None
        assert analysis.project_name == "Test Project"
        assert analysis.use_case == "Campagne bienvenue"
        assert analysis.result == {"use_case_analysis": []}
        assert analysis.created_at is not None


def test_generation_create():
    engine = get_test_engine()
    with Session(engine) as session:
        generation = Generation(
            project_name="Client X",
            brief="Banniere soldes VIP",
            template_type="hero_banner",
            channel="email",
            result={"template": "hero_banner", "params": {}},
            model_used="claude-opus-5",
        )
        session.add(generation)
        session.commit()
        session.refresh(generation)

        assert generation.id is not None
        assert generation.template_type == "hero_banner"
        assert generation.channel == "email"


def test_migration_job_create():
    engine = get_test_engine()
    with Session(engine) as session:
        job = MigrationJob(
            platform="brevo",
            mode="warmup",
            config={"batch_size": 75},
            status="pending",
            progress={},
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        assert job.id is not None
        assert job.platform == "brevo"
        assert job.status == "pending"


def test_app_config_create():
    engine = get_test_engine()
    with Session(engine) as session:
        config = AppConfig(
            key="default_model",
            value="claude-opus-5",
        )
        session.add(config)
        session.commit()
        session.refresh(config)

        assert config.key == "default_model"
        assert config.value == "claude-opus-5"


# ---------------------------------------------------------------------------
# Resolution et normalisation de DATABASE_URL (models/db.py)
#
# Regression de production : l'integration Vercel-Neon prefixe ses variables
# (braze_DATABASE_URL) et ajoute des parametres libpq que pg8000 refuse. Le
# repli silencieux sur SQLite ephemere avait fait disparaitre les donnees.
# ---------------------------------------------------------------------------

_NEON_URL = (
    "postgresql://user:secret@ep-demo-123.eu-central-1.aws.neon.tech/jbraze"
    "?sslmode=require&channel_binding=require"
)


class TestNormalizeDatabaseUrl:

    def test_strips_libpq_only_params(self):
        """sslmode et channel_binding font planter pg8000 des la connexion."""
        url = normalize_database_url(_NEON_URL)
        assert "sslmode" not in url
        assert "channel_binding" not in url

    def test_converts_to_pg8000_driver(self):
        assert normalize_database_url(_NEON_URL).startswith("postgresql+pg8000://")

    def test_converts_legacy_postgres_scheme(self):
        url = normalize_database_url("postgres://user:secret@host/db")
        assert url.startswith("postgresql+pg8000://")
        assert not url.startswith("postgres://")

    def test_does_not_double_prefix_driver(self):
        url = normalize_database_url("postgresql+pg8000://user:secret@host/db")
        assert url.count("+pg8000") == 1

    def test_keeps_other_query_params(self):
        url = normalize_database_url(
            "postgresql://user:secret@host/db?sslmode=require&application_name=jbraze"
        )
        assert "application_name=jbraze" in url
        assert "sslmode" not in url

    def test_preserves_host_and_database(self):
        url = normalize_database_url(_NEON_URL)
        assert "ep-demo-123.eu-central-1.aws.neon.tech" in url
        assert "/jbraze" in url

    def test_invalid_scheme_falls_back_to_ephemeral_sqlite(self):
        """Une valeur parasite (ex: le prefixe 'braze') ne doit pas etre utilisee."""
        url = normalize_database_url("braze")
        assert url == "sqlite:////tmp/jbraze_dev.db"

    def test_empty_value_falls_back_to_sqlite(self):
        assert normalize_database_url(None).startswith("sqlite")
        assert normalize_database_url("   ").startswith("sqlite")

    def test_sqlite_url_is_left_untouched(self):
        assert normalize_database_url("sqlite:////tmp/jbraze_dev.db") == (
            "sqlite:////tmp/jbraze_dev.db"
        )


class TestResolveDatabaseUrl:

    def _env(self, monkeypatch, values):
        """Remplace entierement os.environ par un dict controle."""
        monkeypatch.setattr(os, "environ", dict(values))

    def test_explicit_valid_url_wins(self, monkeypatch):
        self._env(monkeypatch, {
            "DATABASE_URL": "postgresql://user:secret@explicit/db",
            "braze_DATABASE_URL": "postgresql://user:secret@integration/db",
        })
        url, source = resolve_database_url()
        assert source == "DATABASE_URL"
        assert "explicit" in url

    def test_falls_back_to_prefixed_variable(self, monkeypatch):
        """DATABASE_URL contient le prefixe et non l'URL : on prend la prefixee."""
        self._env(monkeypatch, {
            "DATABASE_URL": "braze",
            "braze_DATABASE_URL": "postgresql://user:secret@integration/db",
        })
        url, source = resolve_database_url()
        assert source == "braze_DATABASE_URL"
        assert "integration" in url

    def test_falls_back_when_database_url_absent(self, monkeypatch):
        self._env(monkeypatch, {
            "braze_DATABASE_URL": "postgresql://user:secret@integration/db",
        })
        url, source = resolve_database_url()
        assert source == "braze_DATABASE_URL"
        assert "integration" in url

    def test_never_selects_no_ssl_variant(self, monkeypatch):
        """_POSTGRES_URL_NO_SSL degraderait la connexion en clair."""
        self._env(monkeypatch, {
            "braze_POSTGRES_URL_NO_SSL": "postgresql://user:secret@nossl/db",
            "braze_POSTGRES_URL": "postgresql://user:secret@secure/db",
        })
        url, source = resolve_database_url()
        assert source == "braze_POSTGRES_URL"
        assert "nossl" not in url

    def test_no_ssl_variant_alone_is_ignored(self, monkeypatch):
        self._env(monkeypatch, {
            "braze_POSTGRES_URL_NO_SSL": "postgresql://user:secret@nossl/db",
        })
        url, source = resolve_database_url()
        assert source == "DATABASE_URL"
        assert url is None
        # Le repli reste SQLite plutot qu'une connexion non chiffree
        assert normalize_database_url(url).startswith("sqlite")

    def test_prefers_database_url_suffix_over_postgres_url(self, monkeypatch):
        self._env(monkeypatch, {
            "braze_POSTGRES_URL": "postgresql://user:secret@pgurl/db",
            "braze_DATABASE_URL": "postgresql://user:secret@dburl/db",
        })
        url, source = resolve_database_url()
        assert source == "braze_DATABASE_URL"
        assert "dburl" in url

    def test_no_variable_at_all(self, monkeypatch):
        self._env(monkeypatch, {})
        url, source = resolve_database_url()
        assert url is None
        assert source == "DATABASE_URL"


class TestBuildConnectArgs:

    def test_sqlite_allows_cross_thread_usage(self):
        assert build_connect_args("sqlite:////tmp/jbraze_dev.db") == {
            "check_same_thread": False
        }

    def test_pg8000_gets_verifying_ssl_context(self):
        """Sans ssl_context explicite, pg8000 ne verifie ni hote ni certificat."""
        import ssl

        args = build_connect_args("postgresql+pg8000://user:secret@host/db")
        ctx = args["ssl_context"]
        assert ctx.check_hostname is True
        assert ctx.verify_mode == ssl.CERT_REQUIRED
