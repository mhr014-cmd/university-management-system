"""
ORM model: exam (see docs/Database_Design.md §6.14).

`status` progresses draft -> scheduled -> open -> closed -> published,
transitioned via `PUT /exams/{id}`'s optional `status` field (resolved
during the Milestone 6 pre-implementation review from
`UI_Wireframes.md` §13's "Publish Exam (transitions status...)" wording —
no separate transition endpoint exists). BR-001/FR-025's "results
published" gate for Student mark-visibility means `status = published`
specifically — an exam-level fact, independent of Milestone 7's
per-student-per-course `result` table (same word, different concept; see
this table's own terminology note below and
Requirement_Traceability_Matrix.md's FR-025 correction note).

Terminology note (Database_Design.md §6.14, carried over from the
Project Readiness Audit): the proposal's UI text uses "graded" where this
schema uses `closed` — `closed` is a stored, exam-level fact (no longer
accepting submissions), while "graded" is a derived, submission-level
fact computed by the frontend (`closed` + every submission fully graded),
never a status value stored here.
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

ExamType = Enum("mcq", "written", "practical_coding", "mixed", name="exam_type")
ExamStatus = Enum("draft", "scheduled", "open", "closed", "published", name="exam_status")


class Exam(Base):
    __tablename__ = "exam"
    __table_args__ = (
        # Database_Design.md §10: exam.time_limit_minutes > 0 (VR-004).
        CheckConstraint("time_limit_minutes > 0", name="ck_exam_time_limit_minutes_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # index=True: Database_Design.md §9 "index on class_session_id" — exam
    # list per class.
    class_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class_session.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_by_teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teacher.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    exam_type: Mapped[str] = mapped_column(ExamType, nullable=False)
    time_limit_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    # index=True: Database_Design.md §9 "index on status" — filtering
    # published/unpublished exams.
    status: Mapped[str] = mapped_column(ExamStatus, nullable=False, server_default="draft", index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
