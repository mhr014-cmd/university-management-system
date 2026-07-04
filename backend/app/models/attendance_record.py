"""
ORM model: attendance_record (see docs/Database_Design.md §6.22).

Note: no created_at/updated_at columns — this matches Database_Design.md
exactly (like `room`/`parent_student_link`), not an oversight. Corrections
via PUT /attendance/{id} mutate `status` in place; no separate audit
timestamp is specified by the schema.
"""

import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

AttendanceStatus = Enum("present", "absent", "late", "excused", name="attendance_status")


class AttendanceRecord(Base):
    __tablename__ = "attendance_record"
    __table_args__ = (
        # Database_Design.md §9: composite unique index on
        # (student_id, class_session_id, attendance_date) — duplicate
        # prevention (VR-005) + GET /attendance/me filtering.
        UniqueConstraint(
            "student_id",
            "class_session_id",
            "attendance_date",
            name="uq_attendance_record_student_class_session_date",
        ),
        # Database_Design.md §9: index on (class_session_id, attendance_date)
        # — teacher marking/report queries.
        Index("ix_attendance_record_class_session_id_date", "class_session_id", "attendance_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student.id", ondelete="RESTRICT"), nullable=False
    )
    class_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class_session.id", ondelete="RESTRICT"), nullable=False
    )
    marked_by_teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teacher.id", ondelete="RESTRICT"), nullable=False
    )
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(AttendanceStatus, nullable=False)
