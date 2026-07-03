"""
ORM model: schedule_entry (see docs/Database_Design.md §6.12).

The composite unique constraints below (room_id/teacher_id + day_of_week +
start_time) are a DB-level backstop against exact-duplicate bookings, per
Database_Design.md §9 — they do NOT by themselves implement BR-005's
overlap detection (two bookings with different start_time values can still
overlap, e.g. 10:00-11:00 and 10:30-11:30). Real overlap conflict checking
is service-layer logic (app/services/schedule_service.py), consistent with
API_Contract.md §7.2's "conflicting room/teacher booking (409)" being a
business-rule check, not a constraint violation.
"""

import uuid
from datetime import datetime, time

from sqlalchemy import DateTime, Enum, ForeignKey, Time, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

DayOfWeek = Enum("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun", name="day_of_week")


class ScheduleEntry(Base):
    __tablename__ = "schedule_entry"
    __table_args__ = (
        UniqueConstraint(
            "room_id", "day_of_week", "start_time", name="uq_schedule_entry_room_day_start"
        ),
        UniqueConstraint(
            "teacher_id", "day_of_week", "start_time", name="uq_schedule_entry_teacher_day_start"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class_session.id", ondelete="RESTRICT"), nullable=False
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("room.id", ondelete="RESTRICT"), nullable=False
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teacher.id", ondelete="RESTRICT"), nullable=False
    )
    day_of_week: Mapped[str] = mapped_column(DayOfWeek, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
