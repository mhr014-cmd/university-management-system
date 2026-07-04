"""
ORM model: payment (see docs/Database_Design.md §6.24).

Immutable once recorded — no update/delete endpoint exists (Milestone 8
Domain Rule 10; no reversal workflow is documented anywhere).
`fee_structure_id` is included directly (denormalized alongside
`invoice`) matching Database_Design.md's own column list exactly.
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Payment(Base):
    __tablename__ = "payment"
    __table_args__ = (
        # Database_Design.md §10: payment.amount > 0 (VR-008).
        CheckConstraint("amount > 0", name="ck_payment_amount_positive"),
        # Database_Design.md §9: index on student_id —
        # GET /fees/payments/{studentId}.
        Index("ix_payment_student_id", "student_id"),
        # Database_Design.md §9: index on fee_structure_id —
        # revenue/overdue reporting.
        Index("ix_payment_fee_structure_id", "fee_structure_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student.id", ondelete="RESTRICT"), nullable=False
    )
    fee_structure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fee_structure.id", ondelete="RESTRICT"), nullable=False
    )
    recorded_by_admin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("admin.id", ondelete="RESTRICT"), nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric, nullable=False)
    payment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payment_method: Mapped[str | None] = mapped_column(String, nullable=True)
