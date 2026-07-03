"""core reference data (department, course, room, semester)

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-04

Milestone 1 — see docs/Implementation_Roadmap.md and docs/Database_Design.md
§6.7, §6.8, §6.11, §6.20 for the exact schema this migration implements.

Hand-authored, not produced by `alembic revision --autogenerate`: this
sandbox has no known-good credentials for a live PostgreSQL instance to
autogenerate-diff against (see PROJECT_PROGRESS.md Milestone 1 Known
Issues). Written to mirror app/models/{department,course,room,semester}.py
column-for-column, constraint-for-constraint — review carefully, and
confirm with `alembic revision --autogenerate` against a real database
produces no diff before relying on this in production.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "department",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", name="uq_department_name"),
        sa.UniqueConstraint("code", name="uq_department_code"),
    )

    op.create_table(
        "course",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("credit_hours", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["department.id"], name="fk_course_department_id", ondelete="RESTRICT"),
        sa.UniqueConstraint("code", name="uq_course_code"),
    )
    # Mirrored on the model as Course.department_id's index=True (Milestone 2
    # review) so `alembic revision --autogenerate` doesn't report this as a
    # removed index — see app/models/course.py.
    op.create_index("ix_course_department_id", "course", ["department_id"])

    op.create_table(
        "room",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("building", sa.String(), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.UniqueConstraint("name", name="uq_room_name"),
    )

    op.create_table(
        "semester",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.UniqueConstraint("name", name="uq_semester_name"),
        sa.CheckConstraint("start_date < end_date", name="ck_semester_start_before_end"),
    )


def downgrade() -> None:
    op.drop_table("semester")
    op.drop_table("room")
    op.drop_index("ix_course_department_id", table_name="course")
    op.drop_table("course")
    op.drop_table("department")
