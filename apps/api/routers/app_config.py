"""Endpoints pour la configuration applicative (app_config)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.db import get_db
from models.app_config import AppConfig

router = APIRouter(prefix="/api/app-config", tags=["app-config"])


class AppConfigPayload(BaseModel):
    key: str
    value: str | None = None


@router.get("")
def get_all_config(db: Session = Depends(get_db)):
    """Retourne toutes les entrees de la table app_config."""
    rows = db.query(AppConfig).all()
    return [
        {
            "key": row.key,
            "value": row.value,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }
        for row in rows
    ]


@router.post("")
def upsert_config(payload: AppConfigPayload, db: Session = Depends(get_db)):
    """Upsert une entree dans la table app_config."""
    existing = db.query(AppConfig).filter(AppConfig.key == payload.key).first()
    if existing:
        existing.value = payload.value
    else:
        existing = AppConfig(key=payload.key, value=payload.value)
        db.add(existing)
    db.commit()
    db.refresh(existing)
    return {
        "key": existing.key,
        "value": existing.value,
        "updated_at": existing.updated_at.isoformat() if existing.updated_at else None,
    }
