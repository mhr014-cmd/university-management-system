"""
ORM model: class_session (see docs/Database_Design.md §6.9).

Created via the Derived `POST /schedule/class-sessions` endpoint (see
API_Contract.md §7.8, Proposal_vs_Engineering_Additions.md) — not a
proposal-named entity, but an unavoidable prerequisite for `schedule_entry`
and `enrollment`, both of which reference it.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ClassSession(Base):
    __tablename__ = "class_session"
    __table_args__ = (
        # Database_Design.md §9: composite index on (course_id, semester_id)
        # for timetable/enrollment queries.
        Index("ix_class_session_course_id_semester_id", "course_id", "semester_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("course.id", ondelete="RESTRICT"), nullable=False
    )
    # index=True: Database_Design.md §9's separate "index on teacher_id"
    # entry ("teacher's classes lookup") — distinct from the composite
    # index above.
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teacher.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    semester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("semester.id", ondelete="RESTRICT"), nullable=False
    )
    section_label: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
