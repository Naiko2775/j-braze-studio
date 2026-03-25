"""Endpoints pour le module Migration."""
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, model_validator
from sqlalchemy.orm import Session

from models.db import get_db
from models.migration_job import MigrationJob
from services.migration.engine import MigrationEngine

router = APIRouter(prefix="/api/migration", tags=["migration"])

# Store des jobs en cours pour le stop
_running_jobs: dict[str, dict] = {}


def _default_braze_config() -> dict:
    """Build braze_config from environment variables when not provided."""
    api_key = os.environ.get("BRAZE_API_KEY", "")
    rest_endpoint = os.environ.get("BRAZE_REST_ENDPOINT", "")
    return {"api_key": api_key, "rest_endpoint": rest_endpoint}


class PreviewRequest(BaseModel):
    credentials: dict = {}
    limit: int = 10
    deduplicate_by_email: bool = False


class TestConnectionRequest(BaseModel):
    platform: str
    source_config: dict | None = None
    credentials: dict | None = None
    braze_config: dict | None = None

    @model_validator(mode="after")
    def resolve_aliases(self):
        # Accept credentials as alias for source_config
        if self.source_config is None and self.credentials is not None:
            self.source_config = self.credentials
        elif self.source_config is None:
            self.source_config = {}
        # Default braze_config from env vars if absent
        if self.braze_config is None:
            self.braze_config = _default_braze_config()
        return self


class RunMigrationRequest(BaseModel):
    platform: str
    mode: str = "full"  # full, warmup, dry_run
    source_config: dict | None = None
    credentials: dict | None = None
    braze_config: dict | None = None
    field_mapping: dict | None = None
    contact_limit: int | None = None
    deduplicate_by_email: bool = False
    warmup_stages: list[int] | None = None
    project_name: str | None = None
    project_id: str | None = None

    @model_validator(mode="after")
    def resolve_aliases(self):
        # Accept credentials as alias for source_config
        if self.source_config is None and self.credentials is not None:
            self.source_config = self.credentials
        elif self.source_config is None:
            self.source_config = {}
        # Default braze_config from env vars if absent
        if self.braze_config is None:
            self.braze_config = _default_braze_config()
        return self


@router.get("/platforms")
def list_platforms():
    """Plateformes sources disponibles."""
    return [
        {"id": "brevo", "name": "Brevo", "description": "Brevo (ex-Sendinblue)"},
        {"id": "salesforce_mc", "name": "Salesforce MC", "description": "Salesforce Marketing Cloud"},
        {"id": "csv", "name": "CSV", "description": "Import depuis fichier CSV"},
        {"id": "demo", "name": "Demo", "description": "Donnees de demonstration"},
    ]


@router.post("/test-connection")
def test_connection(req: TestConnectionRequest):
    """Tester la connexion source + Braze."""
    try:
        engine = MigrationEngine(
            source_platform=req.platform,
            source_config=req.source_config,
            braze_config=req.braze_config,
        )
        return engine.test_connections()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/preview/{platform}")
def preview_data(platform: str, req: PreviewRequest | None = None):
    """Apercu des donnees avant migration."""
    if req is None:
        req = PreviewRequest()
    limit = req.limit
    credentials = req.credentials

    # Resolve sfmc alias
    resolved_platform = "salesforce_mc" if platform == "sfmc" else platform

    if resolved_platform == "demo":
        from services.migration.connectors.demo import DemoConnector
        connector = DemoConnector({"contact_count": limit})
        contacts = connector.fetch_contacts(limit=limit)
        return {
            "contacts_count": len(contacts),
            "sample": [c.model_dump() for c in contacts[:5]],
        }

    # For non-demo platforms, use provided credentials
    from services.migration.engine import CONNECTOR_REGISTRY
    if resolved_platform not in CONNECTOR_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform}")
    try:
        connector = CONNECTOR_REGISTRY[resolved_platform](credentials)
        contacts = connector.fetch_contacts(limit=limit)
        return {
            "contacts_count": len(contacts),
            "sample": [c.model_dump() for c in contacts[:5]],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/run")
def run_migration(req: RunMigrationRequest, db: Session = Depends(get_db)):
    """Lancer une migration."""
    # Creer le job en BDD
    job = MigrationJob(
        project_id=req.project_id,
        platform=req.platform,
        mode=req.mode,
        config={
            "source_config": req.source_config,
            "field_mapping": req.field_mapping,
            "contact_limit": req.contact_limit,
            "deduplicate_by_email": req.deduplicate_by_email,
            "project_name": req.project_name,
        },
        status="running",
        progress={"stage": "initializing"},
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        braze_config = req.braze_config.copy()
        if req.mode == "dry_run":
            braze_config["dry_run"] = True

        engine = MigrationEngine(
            source_platform=req.platform,
            source_config=req.source_config,
            braze_config=braze_config,
            field_mapping=req.field_mapping,
        )

        if req.mode == "warmup":
            stop_flag = {"stop": False}
            _running_jobs[job.id] = stop_flag

            result = engine.run_warmup(
                stages=req.warmup_stages,
                should_stop=lambda: stop_flag["stop"],
                deduplicate_by_email=req.deduplicate_by_email,
            )
            job_result = {
                "total_contacts": result.total_contacts,
                "total_success": result.total_success,
                "total_failed": result.total_failed,
                "stages": [
                    {
                        "stage_percent": s.stage_percent,
                        "contacts": s.contacts_in_stage,
                        "success": s.success,
                        "failed": s.failed,
                        "error_rate": s.error_rate,
                        "status": s.status,
                    }
                    for s in result.stages
                ],
            }
            _running_jobs.pop(job.id, None)
        else:
            result = engine.run(
                contact_limit=req.contact_limit,
                deduplicate_by_email=req.deduplicate_by_email,
            )
            job_result = result

        job.status = "completed"
        job.result = job_result
        job.completed_at = datetime.now(timezone.utc)

    except Exception as e:
        job.status = "failed"
        job.error_log = {"error": str(e)}
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

    db.commit()
    return {"job_id": job.id, "status": job.status, "result": job_result}


@router.get("/status/{job_id}")
def get_status(job_id: str, db: Session = Depends(get_db)):
    """Statut temps reel d'une migration en cours."""
    job = db.query(MigrationJob).filter(MigrationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouve")
    return {
        "id": job.id,
        "status": job.status,
        "progress": job.progress,
        "result": job.result,
        "error_log": job.error_log,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }


@router.post("/{job_id}/stop")
def stop_migration(job_id: str, db: Session = Depends(get_db)):
    """Arreter une migration en cours."""
    job = db.query(MigrationJob).filter(MigrationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouve")

    if job.status != "running":
        raise HTTPException(status_code=400, detail="Le job n'est pas en cours")

    stop_flag = _running_jobs.get(job_id)
    if stop_flag:
        stop_flag["stop"] = True

    job.status = "stopped"
    job.completed_at = datetime.now(timezone.utc)
    db.commit()

    return {"status": "stopped", "job_id": job_id}


@router.get("/history/{job_id}")
def get_job_detail(job_id: str, db: Session = Depends(get_db)):
    """Detail d'un job de migration passe."""
    job = db.query(MigrationJob).filter(MigrationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouve")

    # Resolve project_name via join if needed
    project_name = None
    if job.project_id:
        from models.project import Project
        project = db.query(Project).filter(Project.id == job.project_id).first()
        if project:
            project_name = project.name

    return {
        "id": job.id,
        "project_id": job.project_id,
        "project_name": project_name,
        "platform": job.platform,
        "mode": job.mode,
        "status": job.status,
        "config": job.config,
        "progress": job.progress,
        "result": job.result,
        "error_log": job.error_log,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }


@router.get("/history")
def get_history(db: Session = Depends(get_db), limit: int = 50):
    """Historique des migrations executees."""
    from models.project import Project

    jobs = (
        db.query(MigrationJob)
        .order_by(MigrationJob.created_at.desc())
        .limit(limit)
        .all()
    )

    # Build a map of project_id -> project_name for efficiency
    project_ids = {j.project_id for j in jobs if j.project_id}
    project_map = {}
    if project_ids:
        projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
        project_map = {p.id: p.name for p in projects}

    return [
        {
            "id": j.id,
            "project_id": j.project_id,
            "project_name": project_map.get(j.project_id) or (j.config.get("project_name") if j.config else None),
            "platform": j.platform,
            "mode": j.mode,
            "status": j.status,
            "created_at": j.created_at.isoformat() if j.created_at else None,
            "completed_at": j.completed_at.isoformat() if j.completed_at else None,
        }
        for j in jobs
    ]
