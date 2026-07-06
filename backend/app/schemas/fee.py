"""
Pydantic request/response schemas: fee (see docs/API_Contract.md Section 6).
"""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

InvoiceStatus = Literal["unpaid", "partially_paid", "paid", "overdue"]


class FeeStructureCreate(BaseModel):
    department_id: uuid.UUID | None = None
    semester_id: uuid.UUID
    name: str = Field(min_length=1)
    amount: float = Field(gt=0)
    due_date: date


class FeeStructureRead(BaseModel):
    id: uuid.UUID
    department_id: uuid.UUID | None
    semester_id: uuid.UUID
    name: str
    amount: float
    due_date: date
    created_at: datetime
    invoices_created: int


class FeeStructureSummary(BaseModel):
    """GET /fees/structures (Derived, gap-closure addition): a lightweight
    listing used to populate the Admin Fee Dashboard's Record Payment
    fee-structure dropdown, replacing a raw UUID text field. Deliberately
    excludes invoices_created (only meaningful at creation time)."""

    id: uuid.UUID
    name: str
    amount: float
    due_date: date
    semester_id: uuid.UUID
    department_id: uuid.UUID | None


class InvoiceEntry(BaseModel):
    invoice_id: uuid.UUID
    amount: float
    status: InvoiceStatus
    due_date: date


class PaymentEntry(BaseModel):
    payment_id: uuid.UUID
    amount: float
    payment_date: datetime


class FeesMeResponse(BaseModel):
    student_id: uuid.UUID
    outstanding_balance: float
    invoices: list[InvoiceEntry]
    payments: list[PaymentEntry]


class PaymentCreate(BaseModel):
    student_id: uuid.UUID
    fee_structure_id: uuid.UUID
    amount: float = Field(gt=0)
    payment_date: datetime
    payment_method: str | None = None


class PaymentRead(BaseModel):
    payment_id: uuid.UUID
    amount: float
    payment_date: datetime
    fee_structure_id: uuid.UUID


class PaymentHistoryResponse(BaseModel):
    student_id: uuid.UUID
    payments: list[PaymentRead]


class OverdueAccountEntry(BaseModel):
    student_id: uuid.UUID
    # Additive display field (final-polish pass): the Admin Fee Dashboard
    # previously rendered the raw student_id UUID — see student_name below.
    student_name: str
    invoice_id: uuid.UUID
    amount_due: float
    due_date: date
    days_overdue: int


class OverdueResponse(BaseModel):
    overdue_accounts: list[OverdueAccountEntry]


OverdueNotifyScope = Literal["selected", "all_overdue"]


class OverdueNotifyRequest(BaseModel):
    student_ids: list[uuid.UUID] = Field(default_factory=list)
    scope: OverdueNotifyScope


class OverdueNotifyResponse(BaseModel):
    notified_count: int
