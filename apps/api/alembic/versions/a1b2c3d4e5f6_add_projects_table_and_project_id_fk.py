"""add projects table and project_id FK to analyses, generations, migration_jobs

Revision ID: a1b2c3d4e5f6
Revises: 3b7d74a2e524
Create Date: 2026-03-24 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '3b7d74a2e524'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('client_name', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('braze_instance', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Add project_id FK to existing tables
    op.add_column('analyses', sa.Column('project_id', sa.String(length=36), nullable=True))
    op.create_foreign_key('fk_analyses_project_id', 'analyses', 'projects', ['project_id'], ['id'])

    op.add_column('generations', sa.Column('project_id', sa.String(length=36), nullable=True))
    op.create_foreign_key('fk_generations_project_id', 'generations', 'projects', ['project_id'], ['id'])

    op.add_column('migration_jobs', sa.Column('project_id', sa.String(length=36), nullable=True))
    op.create_foreign_key('fk_migration_jobs_project_id', 'migration_jobs', 'projects', ['project_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_migration_jobs_project_id', 'migration_jobs', type_='foreignkey')
    op.drop_column('migration_jobs', 'project_id')

    op.drop_constraint('fk_generations_project_id', 'generations', type_='foreignkey')
    op.drop_column('generations', 'project_id')

    op.drop_constraint('fk_analyses_project_id', 'analyses', type_='foreignkey')
    op.drop_column('analyses', 'project_id')

    op.drop_table('projects')
