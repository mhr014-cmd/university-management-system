"""
ORM model: teacher (see docs/Database_Design.md §6.3).
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Teacher(Base):
    __tablename__ = "teacher"
    __table_args__ = (UniqueConstraint("user_id", name="uq_teacher_user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="RESTRICT"), nullable=False
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("department.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    profile_photo_url: Mapped[str | None] = mapped_column(String, nullable=True)
    hire_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
