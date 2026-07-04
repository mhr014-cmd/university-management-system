"""
ORM model: invoice (see docs/Database_Design.md §6.25).

`(student_id, fee_structure_id)` is unique — one invoice per student per
fee structure, created automatically when the fee_structure is created
(see the §6.25 Milestone 8 design note for eligibility criteria), never
via a separate invoice-creation endpoint. `status` is written by the
service layer immediately on every payment; `overdue` is never stored —
it is computed at read time from `due_date` (same "computed on demand"
philosophy as attendance percentage/GPA, resolving NFR-016). `pdf_url`
stays permanently null — invoice PDFs are generated on demand via
reportlab, same as Milestone 7's transcript generation.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

InvoiceStatus = Enum("unpaid", "partially_paid", "paid", "overdue", name="invoice_status")


class Invoice(Base):
    __tablename__ = "invoice"
    __table_args__ = (
        UniqueConstraint("student_id", "fee_structure_id", name="uq_invoice_student_fee_structure"),
        # Database_Design.md §9: index on (student_id, status) —
        # GET /fees/overdue, fee centre queries.
        Index("ix_invoice_student_id_status", "student_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student.id", ondelete="RESTRICT"), nullable=False
    )
    fee_structure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fee_structure.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(InvoiceStatus, nullable=False, server_default="unpaid")
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pdf_url: Mapped[str | None] = mapped_column(String, nullable=True)
