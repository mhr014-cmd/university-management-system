"""scheduling

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-06

Milestone 4 — see docs/Implementation_Roadmap.md and docs/Database_Design.md
§6.9-6.13 for the exact schema this migration implements. Creates
class_session, enrollment, schedule_entry, and schedule_change_request.

Note: Implementation_Roadmap.md originally named this file
0004_scheduling.py; corrected to 0005 during the Milestone 4
pre-implementation review, since revision 0004 was already consumed by
Milestone 3's 0004_role_profiles.py (the same class of stale-reference
issue fixed once before for M2's and M3's own migration filenames — see
that same review's roadmap-wide numbering fix).

Hand-authored, not produced by `alembic revision --autogenerate` — written
to mirror app/models/class_session.py, enrollment.py, schedule_entry.py,
and schedule_change_request.py column-for-column, including index=True/
UniqueConstraint/Index declarations on the models themselves (per the
Milestone 2 review finding) so an autogenerate diff-check is expected to
be empty.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

day_of_week = postgresql.ENUM("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun", name="day_of_week")
schedule_change_request_status = postgresql.ENUM(
    "pending", "approved", "rejected", name="schedule_change_request_status"
)


def upgrade() -> None:
    op.create_table(
        "class_session",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("semester_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("section_label", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["course.id"], name="fk_class_session_course_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["teacher_id"], ["teacher.id"], name="fk_class_session_teacher_id", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["semester_id"], ["semester.id"], name="fk_class_session_semester_id", ondelete="RESTRICT"
        ),
    )
    # Mirrored on the model: ClassSession.teacher_id's index=True and the
    # composite Index below — see app/models/class_session.py.
    op.create_index("ix_class_session_teacher_id", "class_session", ["teacher_id"])
    op.create_index(
        "ix_class_session_course_id_semester_id", "class_session", ["course_id", "semester_id"]
    )

    op.create_table(
        "enrollment",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["student.id"], name="fk_enrollment_student_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["class_session_id"], ["class_session.id"], name="fk_enrollment_class_session_id", ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "student_id", "class_session_id", name="uq_enrollment_student_class_session"
        ),
    )

    op.create_table(
        "schedule_entry",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("class_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("day_of_week", day_of_week, nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["class_session_id"], ["class_session.id"], name="fk_schedule_entry_class_session_id", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["room_id"], ["room.id"], name="fk_schedule_entry_room_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["teacher_id"], ["teacher.id"], name="fk_schedule_entry_teacher_id", ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "room_id", "day_of_week", "start_time", name="uq_schedule_entry_room_day_start"
        ),
        sa.UniqueConstraint(
            "teacher_id", "day_of_week", "start_time", name="uq_schedule_entry_teacher_day_start"
        ),
    )

    op.create_table(
        "schedule_change_request",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("schedule_entry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_by_teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("confirmed_by_admin_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("requested_change", postgresql.JSONB(), nullable=False),
        sa.Column("status", schedule_change_request_status, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["schedule_entry_id"],
            ["schedule_entry.id"],
            name="fk_schedule_change_request_schedule_entry_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_teacher_id"],
            ["teacher.id"],
            name="fk_schedule_change_request_requested_by_teacher_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["confirmed_by_admin_id"],
            ["admin.id"],
            name="fk_schedule_change_request_confirmed_by_admin_id",
            ondelete="RESTRICT",
        ),
    )


def downgrade() -> None:
    op.drop_table("schedule_change_request")
    op.drop_table("schedule_entry")
    op.drop_table("enrollment")
    op.drop_index("ix_class_session_course_id_semester_id", table_name="class_session")
    op.drop_index("ix_class_session_teacher_id", table_name="class_session")
    op.drop_table("class_session")
    # Unlike creation, op.drop_table() does NOT automatically drop enum
    # types it used — confirmed against a real database during Milestone 2.
    # checkfirst=True so this is a no-op if the type is somehow already gone.
    schedule_change_request_status.drop(op.get_bind(), checkfirst=True)
    day_of_week.drop(op.get_bind(), checkfirst=True)
