"""
ORM model: result (see docs/Database_Design.md §6.21).

`(student_id, course_id, semester_id)` is the authoritative
one-final-grade-per-course-per-semester business key — not `exam_id`.
`exam_id` (Milestone 7 Derived Engineering Addition, see the §6.21 design
note) is nullable and records only which exam most recently
triggered/updated this row, for the Admin: Result Approval queue's
per-exam display and Domain Rule 6 traceability.

`status` deliberately has no standalone `approved` value — FR-035's
`POST /results/{id}/approve` performs approval and publication as a single
atomic action (see the §6.21 design note carried over from the Project
Readiness Audit).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

ResultStatus = Enum("submitted", "published", "rejected", name="result_status")


class Result(Base):
    __tablename__ = "result"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", "semester_id", name="uq_result_student_course_semester"),
        Index("ix_result_exam_id", "exam_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student.id", ondelete="RESTRICT"), nullable=False
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("course.id", ondelete="RESTRICT"), nullable=False
    )
    semester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("semester.id", ondelete="RESTRICT"), nullable=False
    )
    exam_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exam.id", ondelete="RESTRICT"), nullable=True
    )
    submitted_by_teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teacher.id", ondelete="RESTRICT"), nullable=False
    )
    approved_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("admin.id", ondelete="RESTRICT"), nullable=True
    )
    grade_letter: Mapped[str | None] = mapped_column(String, nullable=True)
    grade_point: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    # index=True: Database_Design.md §9 "index on status" — admin approval
    # queue (GET pending results).
    status: Mapped[str] = mapped_column(ResultStatus, nullable=False, server_default="submitted", index=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
