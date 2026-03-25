"""Tests pour les modeles SQLAlchemy."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models.db import Base
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
            model_used="claude-sonnet-4-20250514",
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
            model_used="claude-sonnet-4-20250514",
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
            value="claude-sonnet-4-20250514",
        )
        session.add(config)
        session.commit()
        session.refresh(config)

        assert config.key == "default_model"
        assert config.value == "claude-sonnet-4-20250514"
