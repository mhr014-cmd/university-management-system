"""
ORM model: semester (see docs/Database_Design.md §6.20).

Note: like `room`, `semester` has no created_at/updated_at columns per the
documented schema — not an oversight.
"""

import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Semester(Base):
    __tablename__ = "semester"
    __table_args__ = (CheckConstraint("start_date < end_date", name="ck_semester_start_before_end"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
