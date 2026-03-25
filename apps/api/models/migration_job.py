"""Modele SQLAlchemy pour les jobs de migration."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String

from models.analysis import JSONB
from models.db import Base


class MigrationJob(Base):
    __tablename__ = "migration_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    platform = Column(String(30), nullable=False)
    mode = Column(String(10), nullable=False)
    config = Column(JSONB, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    progress = Column(JSONB, nullable=True)
    result = Column(JSONB, nullable=True)
    error_log = Column(JSONB, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
