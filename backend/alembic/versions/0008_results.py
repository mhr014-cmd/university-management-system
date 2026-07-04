"""results

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-15

Milestone 7 — see docs/Implementation_Roadmap.md and docs/Database_Design.md
§6.21 for the exact schema this migration implements. Creates result,
including the Milestone 7 Derived `exam_id` column (nullable, see the
§6.21 design note).

Hand-authored, not produced by `alembic revision --autogenerate` — written
to mirror app/models/result.py column-for-column, including
index=True/UniqueConstraint declarations on the model itself (per the
Milestone 2 review finding) so an autogenerate diff-check is expected to
be empty.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

result_status = postgresql.ENUM("submitted", "published", "rejected", name="result_status")


def upgrade() -> None:
    op.create_table(
        "result",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("semester_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("submitted_by_teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approved_by_admin_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("grade_letter", sa.String(), nullable=True),
        sa.Column("grade_point", sa.Numeric(), nullable=True),
        sa.Column("status", result_status, nullable=False, server_default="submitted"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["student.id"], name="fk_result_student_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["course_id"], ["course.id"], name="fk_result_course_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["semester_id"], ["semester.id"], name="fk_result_semester_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["exam_id"], ["exam.id"], name="fk_result_exam_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["submitted_by_teacher_id"],
            ["teacher.id"],
            name="fk_result_submitted_by_teacher_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["approved_by_admin_id"], ["admin.id"], name="fk_result_approved_by_admin_id", ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("student_id", "course_id", "semester_id", name="uq_result_student_course_semester"),
    )
    op.create_index("ix_result_status", "result", ["status"])
    op.create_index("ix_result_exam_id", "result", ["exam_id"])


def downgrade() -> None:
    op.drop_index("ix_result_exam_id", table_name="result")
    op.drop_index("ix_result_status", table_name="result")
    op.drop_table("result")
    # Unlike creation, op.drop_table() does NOT automatically drop enum
    # types it used — confirmed against a real database during Milestone 2.
    # checkfirst=True so this is a no-op if the type is somehow already gone.
    result_status.drop(op.get_bind(), checkfirst=True)
