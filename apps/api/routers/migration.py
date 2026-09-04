"""Endpoints pour le module Migration."""
import logging
import os
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, model_validator
from sqlalchemy.orm import Session

from models.db import get_db
from models.migration_job import MigrationJob
from services.migration.engine import MigrationEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/migration", tags=["migration"])

# Store des jobs en cours pour le stop
_running_jobs: dict[str, dict] = {}

# Plateformes de demonstration : donnees fictives, jamais d'ecriture reelle vers Braze
DEMO_PLATFORMS = {"demo", "sfmc_demo"}

# Alias envoyes par le frontend -> identifiant de connecteur
PLATFORM_ALIASES = {"sfmc": "salesforce_mc"}


def _resolve_platform(platform: str) -> str:
    """Resout les alias de plateforme (ex: sfmc -> salesforce_mc)."""
    return PLATFORM_ALIASES.get(platform, platform)


def _is_demo_platform(platform: str) -> bool:
    return _resolve_platform(platform) in DEMO_PLATFORMS


def _safe_fetch(fetcher, label: str) -> list:
    """Recupere une collection optionnelle sans casser l'apercu.

    Une source peut n'exposer que les contacts : dans ce cas segments et
    templates remontent vides plutot que de faire echouer tout l'apercu.
    """
    try:
        return fetcher() or []
    except Exception as e:
        logger.warning(f"Preview: impossible de recuperer {label}: {e}")
        return []


def _contact_sample(contact) -> dict:
    """Serialise un contact pour le tableau d'apercu."""
    data = contact.model_dump(mode="json")
    data["custom_attributes_count"] = len(contact.custom_attributes)
    return data


def _default_braze_config() -> dict:
    """Build braze_config from environment variables when not provided."""
    api_key = os.environ.get("BRAZE_API_KEY", "")
    rest_endpoint = os.environ.get("BRAZE_REST_ENDPOINT", "")
    return {"api_key": api_key, "rest_endpoint": rest_endpoint}


class PreviewRequest(BaseModel):
    credentials: dict = {}
    # Apercu volontairement large : le but est de montrer la volumetrie reelle
    limit: int = 500
    sample_size: int = 8
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
        {
            "id": "sfmc_demo",
            "name": "Salesforce MC (demo)",
            "description": "Jeu de demonstration SFMC : donnees fictives, dry run force",
            "is_demo": True,
        },
    ]


@router.post("/test-connection")
def test_connection(req: TestConnectionRequest):
    """Tester la connexion source + Braze."""
    from services.migration.engine import CONNECTOR_REGISTRY

    resolved_platform = _resolve_platform(req.platform)
    if resolved_platform not in CONNECTOR_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {req.platform}")

    if resolved_platform in DEMO_PLATFORMS:
        # Pas d'appel reseau : les donnees sont locales et rien n'est ecrit dans Braze
        connector = CONNECTOR_REGISTRY[resolved_platform](dict(req.source_config or {}))
        return {
            "source": connector.test_connection(),
            "braze": True,
            "is_demo": True,
            "message": "Mode demonstration : donnees fictives, dry run force",
        }

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
    """Apercu des donnees avant migration : contacts, segments, templates."""
    from services.migration.engine import CONNECTOR_REGISTRY

    if req is None:
        req = PreviewRequest()

    resolved_platform = _resolve_platform(platform)
    if resolved_platform not in CONNECTOR_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform}")

    limit = max(1, req.limit)
    sample_size = max(1, req.sample_size)

    config = dict(req.credentials or {})
    if resolved_platform == "demo":
        # Le connecteur demo genere autant de contacts que demande
        config["contact_count"] = limit

    try:
        connector = CONNECTOR_REGISTRY[resolved_platform](config)
        contacts = connector.fetch_contacts(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    segments = _safe_fetch(connector.fetch_segments, "segments")
    templates = _safe_fetch(connector.fetch_templates, "templates")

    total_attributes = sum(len(c.custom_attributes) for c in contacts)
    avg_attributes = round(total_attributes / len(contacts), 1) if contacts else 0

    response = {
        "platform": resolved_platform,
        "contacts_count": len(contacts),
        "segment_count": len(segments),
        "template_count": len(templates),
        "avg_attributes": avg_attributes,
        "unsubscribed_count": sum(
            1 for c in contacts if c.email_subscribe != "subscribed"
        ),
        "is_demo": resolved_platform in DEMO_PLATFORMS,
        "sample": [_contact_sample(c) for c in contacts[:sample_size]],
    }

    if req.deduplicate_by_email:
        from services.migration.exporters.braze import deduplicate_contacts_by_email
        unique_count = len(deduplicate_contacts_by_email(contacts))
        response["deduplicated_count"] = unique_count
        response["duplicates_removed"] = len(contacts) - unique_count

    # Metadonnees optionnelles exposees par certains connecteurs (Data Extensions...)
    describe = getattr(connector, "describe_source", None)
    if callable(describe):
        try:
            response["source_details"] = describe()
        except Exception as e:
            logger.warning(f"Preview: describe_source a echoue: {e}")

    return response


@router.post("/run")
def run_migration(req: RunMigrationRequest, db: Session = Depends(get_db)):
    """Lancer une migration."""
    is_demo = _is_demo_platform(req.platform)

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
            "forced_dry_run": is_demo,
        },
        status="running",
        progress={"stage": "initializing"},
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        braze_config = dict(req.braze_config or {})
        if req.mode == "dry_run":
            braze_config["dry_run"] = True
        # SECURITE : une plateforme de demonstration ne doit jamais ecrire dans
        # Braze, meme si BRAZE_API_KEY pointe vers un workspace reel.
        if is_demo:
            braze_config["dry_run"] = True

        started = time.monotonic()

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
                "stopped_at_stage": result.stopped_at_stage,
                "stop_reason": result.stop_reason,
                "stages": [
                    {
                        "stage_index": s.stage_index,
                        "stage_percent": s.stage_percent,
                        "contacts": s.contacts_in_stage,
                        "success": s.success,
                        "failed": s.failed,
                        "error_rate": s.error_rate,
                        "duration_seconds": s.duration_seconds,
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

        # Metadonnees communes aux deux modes, lues par le frontend
        job_result["mode"] = req.mode
        job_result["dry_run"] = bool(braze_config.get("dry_run"))
        job_result["forced_dry_run"] = is_demo
        job_result["elapsed_seconds"] = round(time.monotonic() - started, 2)

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
