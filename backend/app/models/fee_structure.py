"""
ORM model: fee_structure (see docs/Database_Design.md §6.23).

Department/semester-scoped, not student-scoped — creating one (via
POST /fees) is the trigger that auto-generates one `invoice` per eligible
student, per §6.25's Milestone 8 design note. `department_id` nullable
means university-wide.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FeeStructure(Base):
    __tablename__ = "fee_structure"
    __table_args__ = (
        # Database_Design.md §10: fee_structure.amount > 0 (VR-008).
        CheckConstraint("amount > 0", name="ck_fee_structure_amount_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("department.id", ondelete="RESTRICT"), nullable=True
    )
    semester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("semester.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
