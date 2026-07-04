"""attendance

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-07

Milestone 5 — see docs/Implementation_Roadmap.md and docs/Database_Design.md
§6.22 for the exact schema this migration implements. Creates
attendance_record.

Hand-authored, not produced by `alembic revision --autogenerate` — written
to mirror app/models/attendance_record.py column-for-column, including
UniqueConstraint/Index declarations on the model itself (per the
Milestone 2 review finding) so an autogenerate diff-check is expected to
be empty.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

attendance_status = postgresql.ENUM("present", "absent", "late", "excused", name="attendance_status")


def upgrade() -> None:
    op.create_table(
        "attendance_record",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("marked_by_teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attendance_date", sa.Date(), nullable=False),
        sa.Column("status", attendance_status, nullable=False),
        sa.ForeignKeyConstraint(
            ["student_id"], ["student.id"], name="fk_attendance_record_student_id", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["class_session_id"],
            ["class_session.id"],
            name="fk_attendance_record_class_session_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["marked_by_teacher_id"],
            ["teacher.id"],
            name="fk_attendance_record_marked_by_teacher_id",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "student_id",
            "class_session_id",
            "attendance_date",
            name="uq_attendance_record_student_class_session_date",
        ),
    )
    op.create_index(
        "ix_attendance_record_class_session_id_date", "attendance_record", ["class_session_id", "attendance_date"]
    )


def downgrade() -> None:
    op.drop_index("ix_attendance_record_class_session_id_date", table_name="attendance_record")
    op.drop_table("attendance_record")
    attendance_status.drop(op.get_bind(), checkfirst=True)
