"""
ORM model: enrollment (see docs/Database_Design.md §6.10).

Created via the Derived `POST /schedule/enrollments` endpoint (see
API_Contract.md §7.9, Proposal_vs_Engineering_Additions.md).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Enrollment(Base):
    __tablename__ = "enrollment"
    __table_args__ = (
        # Database_Design.md §9: composite unique index on
        # (student_id, class_session_id) — prevents duplicate enrollment,
        # also serves GET /schedule/me and class roster queries.
        UniqueConstraint("student_id", "class_session_id", name="uq_enrollment_student_class_session"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student.id", ondelete="RESTRICT"), nullable=False
    )
    class_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class_session.id", ondelete="RESTRICT"), nullable=False
    )
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
