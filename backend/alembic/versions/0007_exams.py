"""exams

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-08

Milestone 6 — see docs/Implementation_Roadmap.md and docs/Database_Design.md
§6.14-6.19 for the exact schema this migration implements. Creates exam,
question, question_option, exam_submission, answer, and question_grade.

Hand-authored, not produced by `alembic revision --autogenerate` — written
to mirror app/models/exam.py, question.py, question_option.py,
exam_submission.py, answer.py, and question_grade.py column-for-column,
including index=True/UniqueConstraint/CheckConstraint declarations on the
models themselves (per the Milestone 2 review finding) so an autogenerate
diff-check is expected to be empty.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

exam_type = postgresql.ENUM("mcq", "written", "practical_coding", "mixed", name="exam_type")
exam_status = postgresql.ENUM("draft", "scheduled", "open", "closed", "published", name="exam_status")
question_type = postgresql.ENUM("mcq", "short_answer", "descriptive", "coding", name="question_type")
exam_submission_status = postgresql.ENUM("in_progress", "submitted", "graded", name="exam_submission_status")


def upgrade() -> None:
    op.create_table(
        "exam",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("class_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("exam_type", exam_type, nullable=False),
        sa.Column("time_limit_minutes", sa.Integer(), nullable=False),
        sa.Column("status", exam_status, nullable=False, server_default="draft"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["class_session_id"], ["class_session.id"], name="fk_exam_class_session_id", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_teacher_id"], ["teacher.id"], name="fk_exam_created_by_teacher_id", ondelete="RESTRICT"
        ),
        sa.CheckConstraint("time_limit_minutes > 0", name="ck_exam_time_limit_minutes_positive"),
    )
    op.create_index("ix_exam_class_session_id", "exam", ["class_session_id"])
    op.create_index("ix_exam_status", "exam", ["status"])

    op.create_table(
        "question",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("question_type", question_type, nullable=False),
        sa.Column("marks", sa.Numeric(), nullable=False),
        sa.Column("hint", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exam.id"], name="fk_question_exam_id", ondelete="CASCADE"),
        sa.CheckConstraint("marks > 0", name="ck_question_marks_positive"),
    )
    op.create_index("ix_question_exam_id", "question", ["exam_id"])

    op.create_table(
        "question_option",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("option_text", sa.String(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["question_id"], ["question.id"], name="fk_question_option_question_id", ondelete="CASCADE"
        ),
    )

    op.create_table(
        "exam_submission",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", exam_submission_status, nullable=False, server_default="in_progress"),
        sa.ForeignKeyConstraint(["exam_id"], ["exam.id"], name="fk_exam_submission_exam_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["student_id"], ["student.id"], name="fk_exam_submission_student_id", ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("exam_id", "student_id", name="uq_exam_submission_exam_student"),
    )

    op.create_table(
        "answer",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("submission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column("selected_option_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["submission_id"], ["exam_submission.id"], name="fk_answer_submission_id", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["question_id"], ["question.id"], name="fk_answer_question_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["selected_option_id"],
            ["question_option.id"],
            name="fk_answer_selected_option_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("submission_id", "question_id", name="uq_answer_submission_question"),
    )

    op.create_table(
        "question_grade",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("answer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("graded_by_teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("awarded_marks", sa.Numeric(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("graded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["answer_id"], ["answer.id"], name="fk_question_grade_answer_id", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["graded_by_teacher_id"],
            ["teacher.id"],
            name="fk_question_grade_graded_by_teacher_id",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("answer_id", name="uq_question_grade_answer_id"),
        sa.CheckConstraint("awarded_marks >= 0", name="ck_question_grade_awarded_marks_non_negative"),
    )


def downgrade() -> None:
    op.drop_table("question_grade")
    op.drop_table("answer")
    op.drop_table("exam_submission")
    op.drop_table("question_option")
    op.drop_index("ix_question_exam_id", table_name="question")
    op.drop_table("question")
    op.drop_index("ix_exam_status", table_name="exam")
    op.drop_index("ix_exam_class_session_id", table_name="exam")
    op.drop_table("exam")
    # Unlike creation, op.drop_table() does NOT automatically drop enum
    # types it used — confirmed against a real database during Milestone 2.
    # checkfirst=True so this is a no-op if the type is somehow already gone.
    exam_submission_status.drop(op.get_bind(), checkfirst=True)
    question_type.drop(op.get_bind(), checkfirst=True)
    exam_status.drop(op.get_bind(), checkfirst=True)
    exam_type.drop(op.get_bind(), checkfirst=True)
