"""
Business logic service: fee (see docs/Requirement_Analysis.md FR-038-FR-043,
VR-008, and the Milestone 8 mandatory Fees Domain Rules).

Calls FeeRepository/UserRepository/reference-data repositories, never the
ORM session directly, per CLAUDE.md §6. Every RBAC/ownership/business-rule
check happens here, before any database write — routers only shape the
request/response and enforce role-only RBAC via dependencies.

Invoice auto-generation (Database_Design.md §6.25's Milestone 8 design
note, confirmed with the user): `create_fee_structure` immediately creates
one `unpaid` invoice for every currently-active student with >=1
Enrollment in a class_session for the fee structure's semester, whose own
department_id matches (or every such student, if department_id is null).
This is the only place `invoice` rows are created.

Outstanding-balance/GPA-style calculations (Domain Rules 15-16): every
amount returned by this service (`outstanding_balance`, invoice `status`,
`amount_due`) is derived at request time from `fee_structure.amount` and
persisted `payment` rows — never trusted from client input, never cached.
"""

import uuid
from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.fee_structure import FeeStructure
from app.models.invoice import Invoice
from app.models.user import User
from app.notifications import dispatcher
from app.repositories.fee_repository import FeeRepository
from app.repositories.reference_data_repository import DepartmentRepository, SemesterRepository
from app.repositories.user_repository import UserRepository
from app.schemas.fee import (
    FeesMeResponse,
    FeeStructureCreate,
    FeeStructureRead,
    InvoiceEntry,
    OverdueAccountEntry,
    OverdueResponse,
    PaymentCreate,
    PaymentEntry,
    PaymentHistoryResponse,
    PaymentRead,
)

fee_repo = FeeRepository()
user_repo = UserRepository()
department_repo = DepartmentRepository()
semester_repo = SemesterRepository()


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def _forbidden(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _invalid(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail)


def _conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def _derived_status(invoice: Invoice, fee_structure: FeeStructure, today: date) -> str:
    # Database_Design.md §6.25: `overdue` is never stored, computed at
    # read time — same "computed on demand" philosophy as attendance
    # percentage/GPA (NFR-016).
    if invoice.status in ("unpaid", "partially_paid") and fee_structure.due_date < today:
        return "overdue"
    return invoice.status


class FeeService:
    # --- POST /fees (FR-039) -------------------------------------------------

    def create_fee_structure(
        self, session: Session, current_user: User, payload: FeeStructureCreate
    ) -> FeeStructureRead:
        if semester_repo.get(session, payload.semester_id) is None:
            raise _invalid("semester_id does not reference an existing semester")
        if payload.department_id is not None and department_repo.get(session, payload.department_id) is None:
            raise _invalid("department_id does not reference an existing department")

        fee_structure = fee_repo.create_fee_structure(
            session,
            department_id=payload.department_id,
            semester_id=payload.semester_id,
            name=payload.name,
            amount=payload.amount,
            due_date=payload.due_date,
        )

        # Invoice auto-generation — all eligible students are resolved by
        # a single query, so there is no partial-failure risk within this
        # batch (Domain Rule 17).
        eligible_students = fee_repo.list_eligible_students(
            session, semester_id=payload.semester_id, department_id=payload.department_id
        )
        now = datetime.now(timezone.utc)
        invoices_created = 0
        newly_invoiced_students = []
        for student in eligible_students:
            # Defensive duplicate check (Domain Rule 5) — practically
            # unreachable since fee_structure.id is brand new, but cheap
            # and keeps this loop safe under future reuse.
            if fee_repo.get_invoice_by_student_fee_structure(session, student.id, fee_structure.id) is not None:
                continue
            fee_repo.create_invoice(session, student_id=student.id, fee_structure_id=fee_structure.id, issued_at=now)
            invoices_created += 1
            newly_invoiced_students.append(student)
        session.commit()
        session.refresh(fee_structure)

        # Domain Rule 4: dispatch only after the invoice-generation batch
        # above has committed. Domain Rule 15: recipients (student.user_id,
        # linked parents) are already resolved from FK-backed queries, so
        # there is no per-recipient validation step that can fail.
        for student in newly_invoiced_students:
            dispatcher.notify_fee_due(
                session,
                student_id=student.id,
                student_user_id=student.user_id,
                amount=float(fee_structure.amount),
                due_date=fee_structure.due_date,
            )

        return FeeStructureRead(
            id=fee_structure.id,
            department_id=fee_structure.department_id,
            semester_id=fee_structure.semester_id,
            name=fee_structure.name,
            amount=float(fee_structure.amount),
            due_date=fee_structure.due_date,
            created_at=fee_structure.created_at,
            invoices_created=invoices_created,
        )

    # --- POST /fees/payments (FR-040) ---------------------------------------

    def record_payment(self, session: Session, current_user: User, payload: PaymentCreate) -> PaymentRead:
        admin = user_repo.get_admin_profile_by_user_id(session, current_user.id)

        student_with_user = user_repo.get_student_with_user(session, payload.student_id)
        if student_with_user is None:
            raise _not_found("Student not found")
        _student, student_user = student_with_user
        # Domain Rule 2: the student must be active.
        if not student_user.is_active:
            raise _invalid("This student is not active.")

        fee_structure = fee_repo.get_fee_structure(session, payload.fee_structure_id)
        if fee_structure is None:
            raise _not_found("Fee structure not found")

        invoice = fee_repo.get_invoice_by_student_fee_structure(session, payload.student_id, payload.fee_structure_id)
        if invoice is None:
            raise _not_found("No invoice exists for this student and fee structure.")
        # Domain Rule 9: fully paid invoices must not accept more payments.
        if invoice.status == "paid":
            raise _conflict("This invoice is already fully paid.")

        paid_so_far = fee_repo.sum_payments(session, payload.student_id, payload.fee_structure_id)
        outstanding = float(fee_structure.amount) - paid_so_far
        # Domain Rules 6/8: payment cannot exceed the remaining balance;
        # outstanding must never go negative.
        if payload.amount > outstanding:
            raise _conflict(
                f"Payment amount {payload.amount} exceeds the outstanding balance {outstanding:.2f}."
            )

        payment = fee_repo.create_payment(
            session,
            student_id=payload.student_id,
            fee_structure_id=payload.fee_structure_id,
            recorded_by_admin_id=admin.id,
            amount=payload.amount,
            payment_date=payload.payment_date,
            payment_method=payload.payment_method,
        )

        new_total_paid = paid_so_far + payload.amount
        new_status = "paid" if new_total_paid >= float(fee_structure.amount) else "partially_paid"
        fee_repo.update_invoice_status(session, invoice, new_status)
        session.commit()
        session.refresh(payment)

        return PaymentRead(
            payment_id=payment.id,
            amount=float(payment.amount),
            payment_date=payment.payment_date,
            fee_structure_id=payment.fee_structure_id,
        )

    # --- GET /fees/me (FR-038, FR-037-style Parent scoping) -----------------

    def get_my_fees(
        self,
        session: Session,
        current_user: User,
        *,
        semester_id: uuid.UUID | None,
        student_id: uuid.UUID | None,
    ) -> FeesMeResponse:
        if current_user.role == "student":
            student = user_repo.get_student_profile_by_user_id(session, current_user.id)
            target_student_id = student.id
        elif current_user.role == "parent":
            parent = user_repo.get_parent_profile_by_user_id(session, current_user.id)
            # Domain Rule 12: Parents may access only linked students.
            if student_id is None or not user_repo.parent_has_linked_student(session, parent.id, student_id):
                raise _forbidden("You may only view fee data for a linked student.")
            target_student_id = student_id
        else:
            raise _forbidden("Only Student or Parent callers may use this endpoint.")

        if semester_id is not None and semester_repo.get(session, semester_id) is None:
            raise _invalid("semester_id does not reference an existing semester")

        invoices = fee_repo.list_invoices_for_student(session, target_student_id, semester_id=semester_id)
        today = date.today()
        invoice_entries = []
        outstanding_balance = 0.0
        fee_structure_ids = set()
        for invoice in invoices:
            fee_structure = fee_repo.get_fee_structure(session, invoice.fee_structure_id)
            if fee_structure is None:
                continue
            fee_structure_ids.add(fee_structure.id)
            paid = fee_repo.sum_payments(session, target_student_id, fee_structure.id)
            remaining = max(0.0, float(fee_structure.amount) - paid)
            outstanding_balance += remaining
            invoice_entries.append(
                InvoiceEntry(
                    invoice_id=invoice.id,
                    amount=float(fee_structure.amount),
                    status=_derived_status(invoice, fee_structure, today),
                    due_date=fee_structure.due_date,
                )
            )

        all_payments = fee_repo.list_payments_for_student(session, target_student_id)
        payment_entries = [
            PaymentEntry(payment_id=p.id, amount=float(p.amount), payment_date=p.payment_date)
            for p in all_payments
            if semester_id is None or p.fee_structure_id in fee_structure_ids
        ]

        return FeesMeResponse(
            student_id=target_student_id,
            outstanding_balance=round(outstanding_balance, 2),
            invoices=invoice_entries,
            payments=payment_entries,
        )

    # --- GET /fees/payments/{studentId} (FR-041) ----------------------------

    def get_payment_history(self, session: Session, current_user: User, student_id: uuid.UUID) -> PaymentHistoryResponse:
        student_with_user = user_repo.get_student_with_user(session, student_id)
        if student_with_user is None:
            raise _not_found("Student not found")

        if current_user.role == "parent":
            parent = user_repo.get_parent_profile_by_user_id(session, current_user.id)
            # Domain Rule 12/BR-007: Parents may access only linked students.
            if not user_repo.parent_has_linked_student(session, parent.id, student_id):
                raise _forbidden("You may only view payment history for a linked student.")

        payments = fee_repo.list_payments_for_student(session, student_id)
        return PaymentHistoryResponse(
            student_id=student_id,
            payments=[
                PaymentRead(
                    payment_id=p.id, amount=float(p.amount), payment_date=p.payment_date,
                    fee_structure_id=p.fee_structure_id,
                )
                for p in payments
            ],
        )

    # --- GET /fees/invoices/{id} (FR-042) ------------------------------------

    def get_invoice_data(self, session: Session, current_user: User, invoice_id: uuid.UUID):
        invoice = fee_repo.get_invoice(session, invoice_id)
        if invoice is None:
            raise _not_found("Invoice not found")

        if current_user.role == "student":
            own_student = user_repo.get_student_profile_by_user_id(session, current_user.id)
            if own_student.id != invoice.student_id:
                raise _forbidden("You may only download your own invoice.")
        elif current_user.role != "admin":
            raise _forbidden("Only the Student themself or an Admin may download this invoice.")

        fee_structure = fee_repo.get_fee_structure(session, invoice.fee_structure_id)
        student_with_user = user_repo.get_student_with_user(session, invoice.student_id)
        student, _user = student_with_user
        paid = fee_repo.sum_payments(session, invoice.student_id, invoice.fee_structure_id)
        today = date.today()

        return {
            "student_name": f"{student.first_name} {student.last_name}",
            "fee_structure_name": fee_structure.name,
            "amount": float(fee_structure.amount),
            "due_date": fee_structure.due_date,
            "status": _derived_status(invoice, fee_structure, today),
            "issued_at": invoice.issued_at,
            "paid": paid,
            "outstanding": max(0.0, float(fee_structure.amount) - paid),
        }

    # --- GET /fees/overdue (FR-043) -----------------------------------------

    def get_overdue_accounts(
        self, session: Session, department_id: uuid.UUID | None, semester_id: uuid.UUID | None
    ) -> OverdueResponse:
        if department_id is not None and department_repo.get(session, department_id) is None:
            raise _invalid("department_id does not reference an existing department")
        if semester_id is not None and semester_repo.get(session, semester_id) is None:
            raise _invalid("semester_id does not reference an existing semester")

        candidates = fee_repo.list_unpaid_or_partial_invoices(
            session, department_id=department_id, semester_id=semester_id
        )
        today = date.today()
        accounts = []
        for invoice, fee_structure in candidates:
            if fee_structure.due_date >= today:
                continue
            paid = fee_repo.sum_payments(session, invoice.student_id, fee_structure.id)
            amount_due = max(0.0, float(fee_structure.amount) - paid)
            accounts.append(
                OverdueAccountEntry(
                    student_id=invoice.student_id,
                    invoice_id=invoice.id,
                    amount_due=round(amount_due, 2),
                    due_date=fee_structure.due_date,
                    days_overdue=(today - fee_structure.due_date).days,
                )
            )
        return OverdueResponse(overdue_accounts=accounts)
