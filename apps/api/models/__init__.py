from models.db import Base, get_db, ensure_tables
from models.project import Project
from models.analysis import Analysis
from models.generation import Generation
from models.migration_job import MigrationJob
from models.app_config import AppConfig

# Auto-create tables for SQLite (serverless /tmp or local dev)
# Must be called AFTER all models are imported so Base.metadata is populated
ensure_tables()

__all__ = ["Base", "get_db", "Project", "Analysis", "Generation", "MigrationJob", "AppConfig"]
