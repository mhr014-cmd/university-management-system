"""
Data access repository: fee_structure, invoice, payment.

All SQLAlchemy queries for the three fee-domain tables live here, per
CLAUDE.md §6 — the service layer calls this module, never the ORM session
directly. No business logic here (Milestone 8's mandatory Fees Domain
Rules live in app/services/fee_service.py).
"""

import uuid
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.class_session import ClassSession
from app.models.enrollment import Enrollment
from app.models.fee_structure import FeeStructure
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.student import Student
from app.models.user import User


def _paginate(session: Session, stmt, page: int, page_size: int):
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = session.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    return items, total


class FeeRepository:
    # --- fee_structure -------------------------------------------------------

    def get_fee_structure(self, session: Session, fee_structure_id: uuid.UUID) -> FeeStructure | None:
        return session.get(FeeStructure, fee_structure_id)

    def list_fee_structures(self, session: Session, page: int, page_size: int):
        stmt = select(FeeStructure).order_by(FeeStructure.due_date.desc())
        return _paginate(session, stmt, page, page_size)

    def create_fee_structure(
        self,
        session: Session,
        *,
        department_id: uuid.UUID | None,
        semester_id: uuid.UUID,
        name: str,
        amount: float,
        due_date: date,
    ) -> FeeStructure:
        fee_structure = FeeStructure(
            department_id=department_id, semester_id=semester_id, name=name, amount=amount, due_date=due_date
        )
        session.add(fee_structure)
        session.flush()
        return fee_structure

    def list_eligible_students(
        self, session: Session, *, semester_id: uuid.UUID, department_id: uuid.UUID | None
    ) -> list[Student]:
        """Active students with >=1 Enrollment in a class_session for this
        semester, matching department_id if provided (Milestone 8's invoice
        auto-generation eligibility — see Database_Design.md §6.25)."""
        stmt = (
            select(Student)
            .join(User, Student.user_id == User.id)
            .join(Enrollment, Enrollment.student_id == Student.id)
            .join(ClassSession, ClassSession.id == Enrollment.class_session_id)
            .where(ClassSession.semester_id == semester_id, User.is_active.is_(True))
            .distinct()
        )
        if department_id is not None:
            stmt = stmt.where(Student.department_id == department_id)
        return list(session.scalars(stmt))

    # --- invoice ---------------------------------------------------------------

    def get_invoice(self, session: Session, invoice_id: uuid.UUID) -> Invoice | None:
        return session.get(Invoice, invoice_id)

    def get_invoice_by_student_fee_structure(
        self, session: Session, student_id: uuid.UUID, fee_structure_id: uuid.UUID
    ) -> Invoice | None:
        return session.scalar(
            select(Invoice).where(Invoice.student_id == student_id, Invoice.fee_structure_id == fee_structure_id)
        )

    def create_invoice(
        self, session: Session, *, student_id: uuid.UUID, fee_structure_id: uuid.UUID, issued_at: datetime
    ) -> Invoice:
        invoice = Invoice(student_id=student_id, fee_structure_id=fee_structure_id, issued_at=issued_at)
        session.add(invoice)
        session.flush()
        return invoice

    def update_invoice_status(self, session: Session, invoice: Invoice, status: str) -> None:
        invoice.status = status
        session.add(invoice)
        session.flush()

    def list_invoices_for_student(
        self, session: Session, student_id: uuid.UUID, *, semester_id: uuid.UUID | None = None
    ) -> list[Invoice]:
        stmt = select(Invoice).where(Invoice.student_id == student_id)
        if semester_id is not None:
            stmt = stmt.join(FeeStructure, FeeStructure.id == Invoice.fee_structure_id).where(
                FeeStructure.semester_id == semester_id
            )
        return list(session.scalars(stmt))

    def list_unpaid_or_partial_invoices(
        self, session: Session, *, department_id: uuid.UUID | None = None, semester_id: uuid.UUID | None = None
    ) -> list[tuple[Invoice, FeeStructure]]:
        stmt = (
            select(Invoice, FeeStructure)
            .join(FeeStructure, FeeStructure.id == Invoice.fee_structure_id)
            .where(Invoice.status.in_(["unpaid", "partially_paid"]))
        )
        if department_id is not None:
            stmt = stmt.where(FeeStructure.department_id == department_id)
        if semester_id is not None:
            stmt = stmt.where(FeeStructure.semester_id == semester_id)
        return [(row[0], row[1]) for row in session.execute(stmt).all()]

    def list_invoices_for_report(
        self,
        session: Session,
        *,
        department_id: uuid.UUID | None = None,
        semester_id: uuid.UUID | None = None,
        student_id: uuid.UUID | None = None,
    ) -> list[tuple[Invoice, FeeStructure]]:
        """Milestone 10: GET /fees/reports — every invoice (any status)
        matching the given optional filters. `department_id` filters via
        the invoiced student's own department_id."""
        stmt = select(Invoice, FeeStructure).join(FeeStructure, FeeStructure.id == Invoice.fee_structure_id)
        if department_id is not None:
            stmt = stmt.join(Student, Student.id == Invoice.student_id).where(Student.department_id == department_id)
        if semester_id is not None:
            stmt = stmt.where(FeeStructure.semester_id == semester_id)
        if student_id is not None:
            stmt = stmt.where(Invoice.student_id == student_id)
        return [(row[0], row[1]) for row in session.execute(stmt).all()]

    # --- payment ---------------------------------------------------------------

    def create_payment(
        self,
        session: Session,
        *,
        student_id: uuid.UUID,
        fee_structure_id: uuid.UUID,
        recorded_by_admin_id: uuid.UUID,
        amount: float,
        payment_date: datetime,
        payment_method: str | None,
    ) -> Payment:
        payment = Payment(
            student_id=student_id,
            fee_structure_id=fee_structure_id,
            recorded_by_admin_id=recorded_by_admin_id,
            amount=amount,
            payment_date=payment_date,
            payment_method=payment_method,
        )
        session.add(payment)
        session.flush()
        return payment

    def list_payments_for_student(self, session: Session, student_id: uuid.UUID) -> list[Payment]:
        return list(session.scalars(select(Payment).where(Payment.student_id == student_id)))

    def sum_payments(self, session: Session, student_id: uuid.UUID, fee_structure_id: uuid.UUID) -> float:
        total = session.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.student_id == student_id, Payment.fee_structure_id == fee_structure_id
            )
        )
        return float(total or 0)
