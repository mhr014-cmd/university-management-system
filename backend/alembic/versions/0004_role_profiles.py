"""role_profiles

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-05

Milestone 3 — see docs/Implementation_Roadmap.md and docs/Database_Design.md
§6.2-6.6 for the exact schema this migration implements. Creates the
student, teacher, parent, admin, and parent_student_link tables.

Note: Implementation_Roadmap.md originally named this file
0003_role_profiles.py; corrected to 0004 in the same change, since
revision 0003 was already consumed by Milestone 2's 0003_user.py (the same
class of stale-reference issue found and fixed once before for M2's own
migration filename).

Hand-authored, not produced by `alembic revision --autogenerate` — written
to mirror app/models/student.py, teacher.py, parent.py, admin.py, and
parent_student_link.py column-for-column, including index=True/
UniqueConstraint declarations on the models themselves (per the Milestone 2
review finding) so an autogenerate diff-check is expected to be empty.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("profile_photo_url", sa.String(), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("enrollment_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name="fk_student_user_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["department_id"], ["department.id"], name="fk_student_department_id", ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("user_id", name="uq_student_user_id"),
    )
    op.create_index("ix_student_department_id", "student", ["department_id"])

    op.create_table(
        "teacher",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("profile_photo_url", sa.String(), nullable=True),
        sa.Column("hire_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name="fk_teacher_user_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["department_id"], ["department.id"], name="fk_teacher_department_id", ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("user_id", name="uq_teacher_user_id"),
    )
    op.create_index("ix_teacher_department_id", "teacher", ["department_id"])

    op.create_table(
        "parent",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("phone_number", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name="fk_parent_user_id", ondelete="RESTRICT"),
        sa.UniqueConstraint("user_id", name="uq_parent_user_id"),
    )

    op.create_table(
        "admin",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name="fk_admin_user_id", ondelete="RESTRICT"),
        sa.UniqueConstraint("user_id", name="uq_admin_user_id"),
    )

    op.create_table(
        "parent_student_link",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relationship_type", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_id"], ["parent.id"], name="fk_parent_student_link_parent_id", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["student_id"], ["student.id"], name="fk_parent_student_link_student_id", ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("parent_id", "student_id", name="uq_parent_student_link_parent_student"),
    )
    # Database_Design.md §9: standalone index on student_id (reverse lookup),
    # separate from the composite unique index above.
    op.create_index("ix_parent_student_link_student_id", "parent_student_link", ["student_id"])


def downgrade() -> None:
    op.drop_index("ix_parent_student_link_student_id", table_name="parent_student_link")
    op.drop_table("parent_student_link")
    op.drop_table("admin")
    op.drop_table("parent")
    op.drop_index("ix_teacher_department_id", table_name="teacher")
    op.drop_table("teacher")
    op.drop_index("ix_student_department_id", table_name="student")
    op.drop_table("student")
