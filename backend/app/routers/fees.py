"""
API router: fees (see docs/API_Contract.md Section 6).
"""

import uuid

from fastapi import APIRouter, Depends, Query, Response
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.middleware.rbac import require_roles
from app.models.user import User
from app.pdf.invoice_generator import generate_invoice_pdf
from app.schemas.common import PaginatedResponse
from app.schemas.fee import (
    FeesMeResponse,
    FeeStructureCreate,
    FeeStructureRead,
    FeeStructureSummary,
    OverdueNotifyRequest,
    OverdueNotifyResponse,
    OverdueResponse,
    PaymentCreate,
    PaymentHistoryResponse,
    PaymentRead,
)
from app.services.fee_service import FeeService

router = APIRouter(prefix="/fees", tags=["fees"])

fee_service = FeeService()

_require_admin = Depends(require_roles("admin"))
_require_student_or_parent = Depends(require_roles("student", "parent"))
_require_admin_or_parent = Depends(require_roles("admin", "parent"))
_require_student_or_admin = Depends(require_roles("student", "admin"))


# Registered before /me isn't required (distinct literal path), but placed
# ahead of "" for readability — no path-matching ambiguity here since
# "/structures" doesn't overlap with any other fees route pattern.
@router.get("/structures", response_model=PaginatedResponse[FeeStructureSummary], dependencies=[_require_admin])
def list_fee_structures(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = fee_service.list_fee_structures(db, page, page_size)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/me", response_model=FeesMeResponse, dependencies=[_require_student_or_parent])
def get_my_fees(
    semester_id: uuid.UUID | None = Query(default=None),
    student_id: uuid.UUID | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return fee_service.get_my_fees(db, current_user, semester_id=semester_id, student_id=student_id)


@router.post("", response_model=FeeStructureRead, status_code=201, dependencies=[_require_admin])
def create_fee_structure(
    payload: FeeStructureCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return fee_service.create_fee_structure(db, current_user, payload)


@router.post("/payments", response_model=PaymentRead, status_code=201, dependencies=[_require_admin])
def record_payment(
    payload: PaymentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return fee_service.record_payment(db, current_user, payload)


@router.get(
    "/payments/{student_id}", response_model=PaymentHistoryResponse, dependencies=[_require_admin_or_parent]
)
def get_payment_history(
    student_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return fee_service.get_payment_history(db, current_user, student_id)


@router.get("/overdue", response_model=OverdueResponse, dependencies=[_require_admin])
def get_overdue_accounts(
    department_id: uuid.UUID | None = Query(default=None),
    semester_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return fee_service.get_overdue_accounts(db, department_id, semester_id)


@router.post("/overdue/notify", response_model=OverdueNotifyResponse, dependencies=[_require_admin])
def notify_overdue_accounts(payload: OverdueNotifyRequest, db: Session = Depends(get_db)):
    return fee_service.notify_overdue_accounts(db, payload)


@router.get("/invoices/{invoice_id}", dependencies=[_require_student_or_admin])
async def get_invoice(
    invoice_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    invoice_data = fee_service.get_invoice_data(db, current_user, invoice_id)
    pdf_bytes = await run_in_threadpool(generate_invoice_pdf, invoice_data)
    return Response(content=pdf_bytes, media_type="application/pdf")
