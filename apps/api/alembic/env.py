import os
import sys
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

load_dotenv()

# Ajouter le repertoire api au path
sys.path.insert(0, os.path.dirname(__file__) + "/..")

# Doit preceder l'import de `models` : son __init__ appelle ensure_tables(),
# qui creerait le schema avant les migrations et ferait echouer upgrade head.
os.environ["JBRAZE_SKIP_AUTO_CREATE"] = "1"

from models.db import Base, build_connect_args, normalize_database_url
from models.analysis import Analysis
from models.generation import Generation
from models.migration_job import MigrationJob
from models.app_config import AppConfig

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url():
    """Meme normalisation que l'application (driver pg8000 inclus).

    Sans cela, une URL Neon standard "postgresql://" ferait tomber Alembic
    sur psycopg2, absent de requirements.txt.
    """
    return normalize_database_url(os.getenv("DATABASE_URL"))


def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    configuration = config.get_section(config.config_ini_section, {})
    url = get_url()
    configuration["sqlalchemy.url"] = url
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=build_connect_args(url),
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
