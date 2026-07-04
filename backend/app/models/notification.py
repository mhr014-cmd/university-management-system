"""
ORM model: notification (see docs/Database_Design.md §6.26).

Every row belongs to exactly one `user` (Milestone 9 Domain Rule 1) — for
a Parent-linked event (e.g. `fee_due`), a separate row is created for
each linked Parent's own `user_id`, rather than the Student's own
notification being visible to the Parent. `message` is always populated
by a server-side template (see API_Contract.md §8.3), never accepted
from a client. `created_at` is always server-generated.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

NotificationType = Enum(
    "result_published", "schedule_change", "attendance_warning", "fee_due", "other", name="notification_type"
)


class Notification(Base):
    __tablename__ = "notification"
    __table_args__ = (
        # Database_Design.md §9: composite index on (user_id, is_read) —
        # notification panel unread-count queries.
        Index("ix_notification_user_id_is_read", "user_id", "is_read"),
        # Database_Design.md §9: index on created_at — chronological feed
        # ordering (newest first, per Domain Rule 16).
        Index("ix_notification_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="RESTRICT"), nullable=False
    )
    type: Mapped[str] = mapped_column(NotificationType, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
