"""
ORM model: schedule_change_request (see docs/Database_Design.md §6.13).

`requested_change` uses JSONB (Database_Design.md lists "string/JSON" as
the allowed type) since its content is structured — matching the
`requested_change` object shape in API_Contract.md §7.6's request body
(day_of_week/start_time/end_time/room_id).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

ScheduleChangeRequestStatus = Enum("pending", "approved", "rejected", name="schedule_change_request_status")


class ScheduleChangeRequest(Base):
    __tablename__ = "schedule_change_request"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schedule_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schedule_entry.id", ondelete="RESTRICT"), nullable=False
    )
    requested_by_teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teacher.id", ondelete="RESTRICT"), nullable=False
    )
    confirmed_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("admin.id", ondelete="RESTRICT"), nullable=True
    )
    requested_change: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(
        ScheduleChangeRequestStatus, nullable=False, server_default="pending"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
