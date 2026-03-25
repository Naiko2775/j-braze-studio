"""Modele SQLAlchemy pour les analyses Data Model."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.types import TypeDecorator
from sqlalchemy import JSON

from models.db import Base


class JSONB(TypeDecorator):
    """Type JSONB compatible SQLite (pour les tests) et PostgreSQL."""
    impl = JSON
    cache_ok = True


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    project_name = Column(String(100), nullable=True)
    use_case = Column(Text, nullable=False)
    result = Column(JSONB, nullable=True)
    model_used = Column(String(50), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
