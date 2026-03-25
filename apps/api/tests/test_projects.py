"""Tests pour le CRUD projets et les relations avec les autres entites."""
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models.db import Base
from models.project import Project
from models.analysis import Analysis
from models.generation import Generation
from models.migration_job import MigrationJob


def get_test_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

def test_project_create():
    engine = get_test_engine()
    with Session(engine) as session:
        project = Project(
            name="Migration Carrefour",
            client_name="Carrefour",
            description="Migration CRM vers Braze",
            braze_instance="EU-01",
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        assert project.id is not None
        assert len(project.id) == 36
        assert project.name == "Migration Carrefour"
        assert project.client_name == "Carrefour"
        assert project.description == "Migration CRM vers Braze"
        assert project.braze_instance == "EU-01"
        assert project.status == "active"
        assert project.created_at is not None
        assert project.updated_at is not None


def test_project_default_status():
    engine = get_test_engine()
    with Session(engine) as session:
        project = Project(name="Test")
        session.add(project)
        session.commit()
        session.refresh(project)

        assert project.status == "active"


def test_project_update():
    engine = get_test_engine()
    with Session(engine) as session:
        project = Project(name="Initial Name", client_name="Client A")
        session.add(project)
        session.commit()

        project.name = "Updated Name"
        project.status = "completed"
        session.commit()
        session.refresh(project)

        assert project.name == "Updated Name"
        assert project.status == "completed"


def test_project_archive():
    engine = get_test_engine()
    with Session(engine) as session:
        project = Project(name="To Archive")
        session.add(project)
        session.commit()

        project.status = "archived"
        session.commit()
        session.refresh(project)

        assert project.status == "archived"


# ---------------------------------------------------------------------------
# Relation tests
# ---------------------------------------------------------------------------

def test_analysis_with_project_id():
    engine = get_test_engine()
    with Session(engine) as session:
        project = Project(name="Test Project")
        session.add(project)
        session.commit()
        session.refresh(project)

        analysis = Analysis(
            project_id=project.id,
            project_name="Test Project",
            use_case="Campagne bienvenue",
            result={"data": []},
            model_used="demo",
        )
        session.add(analysis)
        session.commit()
        session.refresh(analysis)

        assert analysis.project_id == project.id
        assert analysis.project_name == "Test Project"


def test_generation_with_project_id():
    engine = get_test_engine()
    with Session(engine) as session:
        project = Project(name="Test Project")
        session.add(project)
        session.commit()
        session.refresh(project)

        generation = Generation(
            project_id=project.id,
            project_name="Test Project",
            brief="Hero banner pour soldes",
            template_type="hero_banner",
            channel="email",
            result={"template": "hero_banner"},
            model_used="demo",
        )
        session.add(generation)
        session.commit()
        session.refresh(generation)

        assert generation.project_id == project.id


def test_migration_job_with_project_id():
    engine = get_test_engine()
    with Session(engine) as session:
        project = Project(name="Test Project")
        session.add(project)
        session.commit()
        session.refresh(project)

        job = MigrationJob(
            project_id=project.id,
            platform="demo",
            mode="dry_run",
            config={},
            status="pending",
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        assert job.project_id == project.id


def test_analysis_without_project_id():
    """project_id is nullable for retrocompatibility."""
    engine = get_test_engine()
    with Session(engine) as session:
        analysis = Analysis(
            use_case="Test sans projet",
            result={},
            model_used="demo",
        )
        session.add(analysis)
        session.commit()
        session.refresh(analysis)

        assert analysis.project_id is None


def test_multiple_entities_same_project():
    engine = get_test_engine()
    with Session(engine) as session:
        project = Project(name="Multi-entites")
        session.add(project)
        session.commit()
        session.refresh(project)

        # Create multiple entities linked to same project
        for i in range(3):
            session.add(Analysis(
                project_id=project.id,
                use_case=f"Use case {i}",
                result={},
                model_used="demo",
            ))
        for i in range(2):
            session.add(Generation(
                project_id=project.id,
                brief=f"Brief {i}",
                result={},
                model_used="demo",
            ))
        session.add(MigrationJob(
            project_id=project.id,
            platform="demo",
            mode="dry_run",
            config={},
            status="pending",
        ))
        session.commit()

        # Verify counts
        analyses = session.query(Analysis).filter(
            Analysis.project_id == project.id
        ).all()
        generations = session.query(Generation).filter(
            Generation.project_id == project.id
        ).all()
        migrations = session.query(MigrationJob).filter(
            MigrationJob.project_id == project.id
        ).all()

        assert len(analyses) == 3
        assert len(generations) == 2
        assert len(migrations) == 1


# ---------------------------------------------------------------------------
# Router tests (using FastAPI TestClient)
# ---------------------------------------------------------------------------

def _setup_test_app():
    """Setup test app with in-memory SQLite DB."""
    from models.db import get_db
    # Ensure all models are registered on Base.metadata before creating tables
    import models  # noqa: F401

    # Use a shared in-memory SQLite DB (same DB for all connections)
    test_engine = create_engine(
        "sqlite:///file::memory:?cache=shared&uri=true",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(test_engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Import app after models are registered
    from main import app
    from fastapi.testclient import TestClient

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return app, client, TestSessionLocal


def test_projects_crud_via_api():
    """Test the full CRUD cycle through the API router."""
    app, client, _ = _setup_test_app()

    try:
        # CREATE
        resp = client.post("/api/projects", json={
            "name": "Migration Carrefour",
            "client_name": "Carrefour",
            "description": "Test CRUD",
            "braze_instance": "EU-01",
        })
        assert resp.status_code == 200
        data = resp.json()
        project_id = data["id"]
        assert data["name"] == "Migration Carrefour"
        assert data["status"] == "active"

        # LIST
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        projects = resp.json()
        assert len(projects) == 1
        assert projects[0]["id"] == project_id

        # GET detail
        resp = client.get(f"/api/projects/{project_id}")
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["name"] == "Migration Carrefour"
        assert detail["counts"]["analyses"] == 0
        assert detail["counts"]["generations"] == 0
        assert detail["counts"]["migrations"] == 0

        # UPDATE
        resp = client.put(f"/api/projects/{project_id}", json={
            "name": "Migration Carrefour v2",
            "status": "completed",
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "Migration Carrefour v2"
        assert resp.json()["status"] == "completed"

        # DELETE (archive)
        resp = client.delete(f"/api/projects/{project_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "archived"

        # After archival, project should not appear in default list
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        assert len(resp.json()) == 0

        # But appears with status filter
        resp = client.get("/api/projects?status=archived")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        # 404 for non-existent project
        resp = client.get("/api/projects/nonexistent-id")
        assert resp.status_code == 404

    finally:
        app.dependency_overrides.clear()


def test_project_activity_endpoint():
    """Test the activity timeline endpoint."""
    app, client, TestSessionLocal = _setup_test_app()

    try:
        # Create project
        resp = client.post("/api/projects", json={"name": "Activity Test"})
        project_id = resp.json()["id"]

        # Add entities linked to this project via direct DB insert
        db = TestSessionLocal()
        db.add(Analysis(
            project_id=project_id,
            use_case="Test analysis",
            result={},
            model_used="demo",
        ))
        db.add(Generation(
            project_id=project_id,
            brief="Test generation",
            result={},
            model_used="demo",
        ))
        db.add(MigrationJob(
            project_id=project_id,
            platform="demo",
            mode="dry_run",
            config={},
            status="completed",
        ))
        db.commit()
        db.close()

        # Get activity
        resp = client.get(f"/api/projects/{project_id}/activity")
        assert resp.status_code == 200
        activities = resp.json()
        assert len(activities) == 3

        types = {a["type"] for a in activities}
        assert types == {"analysis", "generation", "migration"}

    finally:
        app.dependency_overrides.clear()
