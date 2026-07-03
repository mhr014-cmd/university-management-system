"""initial baseline (no schema yet)

Revision ID: 0001
Revises:
Create Date: 2026-07-03

Empty baseline revision establishing the migration chain for Milestone 0.
No tables exist yet — the first real schema (Department, Course, Room,
Semester) lands in Milestone 1 per docs/Implementation_Roadmap.md.
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
