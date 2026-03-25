"""Endpoints pour la gestion des projets clients."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.db import get_db
from models.project import Project
from models.analysis import Analysis
from models.generation import Generation
from models.migration_job import MigrationJob

router = APIRouter(prefix="/api/projects", tags=["projects"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    name: str
    client_name: str | None = None
    description: str | None = None
    braze_instance: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    client_name: str | None = None
    description: str | None = None
    braze_instance: str | None = None
    status: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _project_to_dict(project: Project) -> dict:
    return {
        "id": project.id,
        "name": project.name,
        "client_name": project.client_name,
        "description": project.description,
        "braze_instance": project.braze_instance,
        "status": project.status,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("")
def create_project(req: ProjectCreate, db: Session = Depends(get_db)):
    """Creer un nouveau projet."""
    project = Project(
        name=req.name,
        client_name=req.client_name,
        description=req.description,
        braze_instance=req.braze_instance,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return _project_to_dict(project)


@router.get("")
def list_projects(status: str | None = None, db: Session = Depends(get_db)):
    """Lister les projets (tri par updated_at desc)."""
    query = db.query(Project)
    if status:
        query = query.filter(Project.status == status)
    else:
        # Par defaut, ne pas afficher les archives
        query = query.filter(Project.status != "archived")
    projects = query.order_by(Project.updated_at.desc()).all()
    return [_project_to_dict(p) for p in projects]


@router.get("/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)):
    """Detail d'un projet avec compteurs."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouve")

    # Compteurs
    analyses_count = db.query(func.count(Analysis.id)).filter(
        Analysis.project_id == project_id
    ).scalar()
    generations_count = db.query(func.count(Generation.id)).filter(
        Generation.project_id == project_id
    ).scalar()
    migrations_count = db.query(func.count(MigrationJob.id)).filter(
        MigrationJob.project_id == project_id
    ).scalar()

    result = _project_to_dict(project)
    result["counts"] = {
        "analyses": analyses_count,
        "generations": generations_count,
        "migrations": migrations_count,
    }
    return result


@router.put("/{project_id}")
def update_project(project_id: str, req: ProjectUpdate, db: Session = Depends(get_db)):
    """Modifier un projet."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouve")

    if req.name is not None:
        project.name = req.name
    if req.client_name is not None:
        project.client_name = req.client_name
    if req.description is not None:
        project.description = req.description
    if req.braze_instance is not None:
        project.braze_instance = req.braze_instance
    if req.status is not None:
        project.status = req.status

    project.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(project)
    return _project_to_dict(project)


@router.delete("/{project_id}")
def archive_project(project_id: str, db: Session = Depends(get_db)):
    """Archiver un projet (soft delete)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouve")

    project.status = "archived"
    project.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "archived", "id": project_id}


@router.get("/{project_id}/activity")
def get_project_activity(project_id: str, db: Session = Depends(get_db)):
    """Timeline d'activite d'un projet (analyses + generations + migrations, triees par date)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouve")

    activities = []

    # Analyses
    analyses = db.query(Analysis).filter(Analysis.project_id == project_id).all()
    for a in analyses:
        activities.append({
            "type": "analysis",
            "id": a.id,
            "summary": (a.use_case or "")[:100],
            "project_name": a.project_name,
            "model_used": a.model_used,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })

    # Generations
    generations = db.query(Generation).filter(Generation.project_id == project_id).all()
    for g in generations:
        activities.append({
            "type": "generation",
            "id": g.id,
            "summary": (g.brief or "")[:100],
            "project_name": g.project_name,
            "template_type": g.template_type,
            "channel": g.channel,
            "model_used": g.model_used,
            "created_at": g.created_at.isoformat() if g.created_at else None,
        })

    # Migrations
    migrations = db.query(MigrationJob).filter(MigrationJob.project_id == project_id).all()
    for m in migrations:
        activities.append({
            "type": "migration",
            "id": m.id,
            "summary": f"{m.platform} / {m.mode}",
            "status": m.status,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        })

    # Tri par date decroissante
    activities.sort(key=lambda x: x.get("created_at") or "", reverse=True)

    return activities
