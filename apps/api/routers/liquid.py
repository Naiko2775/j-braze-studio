"""Endpoints pour le module Liquid Generator."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.db import get_db
from models.generation import Generation
from services.liquid.templates import get_templates as svc_get_templates
from services.liquid.generator import generate_banner


router = APIRouter(prefix="/api/liquid", tags=["liquid"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    brief: str
    template_type: str | None = None
    channel: str | None = None
    project_name: str | None = None
    project_id: str | None = None
    model: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/generate")
def generate(req: GenerateRequest, db: Session = Depends(get_db)):
    """Generer une banniere a partir d'un brief creatif."""
    if not req.brief or not req.brief.strip():
        raise HTTPException(status_code=422, detail="Le brief ne peut pas etre vide")

    try:
        result = generate_banner(
            brief=req.brief,
            template_type=req.template_type,
            channel=req.channel,
            model=req.model,
        )
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # Persister en BDD
    generation = Generation(
        project_id=req.project_id,
        project_name=req.project_name,
        brief=req.brief,
        template_type=req.template_type or result.get("template"),
        channel=req.channel,
        result=result,
        model_used=result.get("model_used", "unknown"),
    )
    db.add(generation)
    db.commit()
    db.refresh(generation)

    return {
        "id": generation.id,
        "result": result,
        "created_at": generation.created_at.isoformat() if generation.created_at else None,
    }


@router.get("/templates")
def list_templates(category: str | None = None):
    """Retourne la liste des templates predefinies.

    Args:
        category: Filtre optionnel par categorie ('banner', 'email', 'push', 'sms').
    """
    return svc_get_templates(category=category)


@router.get("/history")
def get_history(db: Session = Depends(get_db), limit: int = 50):
    """Historique des generations (BDD)."""
    generations = (
        db.query(Generation)
        .order_by(Generation.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": g.id,
            "project_id": g.project_id,
            "project_name": g.project_name,
            "brief": g.brief,
            "template_type": g.template_type,
            "channel": g.channel,
            "model_used": g.model_used,
            "created_at": g.created_at.isoformat() if g.created_at else None,
        }
        for g in generations
    ]


@router.get("/history/{generation_id}")
def get_generation_detail(generation_id: str, db: Session = Depends(get_db)):
    """Detail d'une generation passee."""
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    if not generation:
        raise HTTPException(status_code=404, detail="Generation non trouvee")
    return {
        "id": generation.id,
        "project_name": generation.project_name,
        "brief": generation.brief,
        "template_type": generation.template_type,
        "channel": generation.channel,
        "result": generation.result,
        "model_used": generation.model_used,
        "created_at": generation.created_at.isoformat() if generation.created_at else None,
    }
