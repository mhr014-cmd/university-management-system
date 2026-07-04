"""
ORM model: exam_submission (see docs/Database_Design.md §6.17).

`started_at` is set once, from the server clock only, by
`POST /exams/{id}/start` (Derived Engineering Addition — see
API_Contract.md §3.6) and is never updated afterward — no repository
method mutates it. `POST /exams/{id}/submit` reads this stored value to
enforce VR-004's time limit server-side.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

ExamSubmissionStatus = Enum("in_progress", "submitted", "graded", name="exam_submission_status")


class ExamSubmission(Base):
    __tablename__ = "exam_submission"
    __table_args__ = (
        # Database_Design.md §9/§10: composite unique index on
        # (exam_id, student_id) — one submission per student per exam;
        # also supports grading queries.
        UniqueConstraint("exam_id", "student_id", name="uq_exam_submission_exam_student"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exam.id", ondelete="RESTRICT"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student.id", ondelete="RESTRICT"), nullable=False
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(ExamSubmissionStatus, nullable=False, server_default="in_progress")
