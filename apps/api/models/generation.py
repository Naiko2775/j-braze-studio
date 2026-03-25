"""Modele SQLAlchemy pour les generations Liquid."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from models.analysis import JSONB
from models.db import Base


class Generation(Base):
    __tablename__ = "generations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    project_name = Column(String(100), nullable=True)
    brief = Column(Text, nullable=False)
    template_type = Column(String(30), nullable=True)
    channel = Column(String(20), nullable=True)
    result = Column(JSONB, nullable=True)
    model_used = Column(String(50), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
