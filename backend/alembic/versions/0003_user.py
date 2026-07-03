"""user

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-04

Milestone 2 — see docs/Implementation_Roadmap.md and docs/Database_Design.md
§6.1 (including the Milestone 2 design note on current_refresh_token_jti /
refresh_token_expires_at) for the exact schema this migration implements.

Hand-authored, not produced by `alembic revision --autogenerate` — same
sandbox limitation as revision 0002 (no known-good live PostgreSQL
credentials available to autogenerate-diff against; see PROJECT_PROGRESS.md
Milestone 1 Known Issues). Written to mirror app/models/user.py
column-for-column; confirm with a live autogenerate diff (expected: no
changes) before trusting this in production.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

user_role = postgresql.ENUM("student", "teacher", "parent", "admin", name="user_role")


def upgrade() -> None:
    user_role.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "user",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("current_refresh_token_jti", sa.String(), nullable=True),
        sa.Column("refresh_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email", name="uq_user_email"),
    )
    # Database_Design.md §9 calls for "unique index on email" — the
    # UniqueConstraint above already creates that unique index automatically
    # in PostgreSQL, so no separate index is created here (would be a
    # redundant duplicate). Only `role` needs its own explicit index.
    op.create_index("ix_user_role", "user", ["role"])


def downgrade() -> None:
    op.drop_index("ix_user_role", table_name="user")
    op.drop_table("user")
    user_role.drop(op.get_bind(), checkfirst=True)
