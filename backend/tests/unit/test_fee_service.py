"""
Unit tests: app.services.fee_service.FeeService.

Repositories are stubbed (per CLAUDE.md §10) so these tests exercise the
Milestone 8 mandatory Fees Domain Rules directly, without a database:
  1-2. Student exists and is active
  3. Enrollment-gated invoice auto-generation eligibility
  4. Fee structure must reference an existing semester
  5. Duplicate-invoice prevention (defensive check)
  6-8. Payment cannot exceed the remaining outstanding balance; amounts
       positive; outstanding never negative
  9. Fully paid invoices reject further payments
  10. Payments are immutable (no update/delete method exists at all)
  11-14. RBAC/ownership for Student/Parent/Admin
  15-16. Server-side-only financial calculations
  17. Invoice-generation batch is all-or-nothing (single eligibility query)
"""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models.department import Department
from app.models.fee_structure import FeeStructure
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.semester import Semester
from app.models.student import Student
from app.models.user import User
from app.schemas.fee import FeeStructureCreate, OverdueNotifyRequest, PaymentCreate
from app.services import fee_service as fee_service_module
from app.services.fee_service import FeeService


def make_fee_structure(**overrides) -> FeeStructure:
    defaults = dict(
        id=uuid.uuid4(), department_id=None, semester_id=uuid.uuid4(), name="Tuition", amount=10000,
        due_date=date(2030, 1, 1), created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return FeeStructure(**defaults)


def make_invoice(**overrides) -> Invoice:
    defaults = dict(
        id=uuid.uuid4(), student_id=uuid.uuid4(), fee_structure_id=uuid.uuid4(), status="unpaid",
        issued_at=datetime.now(timezone.utc), pdf_url=None,
    )
    defaults.update(overrides)
    return Invoice(**defaults)


def make_payment(**overrides) -> Payment:
    defaults = dict(
        id=uuid.uuid4(), student_id=uuid.uuid4(), fee_structure_id=uuid.uuid4(), recorded_by_admin_id=uuid.uuid4(),
        amount=100, payment_date=datetime.now(timezone.utc), payment_method=None,
    )
    defaults.update(overrides)
    return Payment(**defaults)


def make_student(**overrides) -> Student:
    defaults = dict(id=uuid.uuid4(), user_id=uuid.uuid4(), department_id=uuid.uuid4(), first_name="S", last_name="Student")
    defaults.update(overrides)
    return Student(**defaults)


def make_semester(**overrides) -> Semester:
    defaults = dict(id=uuid.uuid4(), name="Spring 2026", start_date=date(2026, 1, 1), end_date=date(2026, 5, 1))
    defaults.update(overrides)
    return Semester(**defaults)


def make_department(**overrides) -> Department:
    defaults = dict(id=uuid.uuid4(), name="CS", code="CS1")
    defaults.update(overrides)
    return Department(**defaults)


@pytest.fixture
def stub_repos(monkeypatch):
    fee_repo = MagicMock()
    user_repo = MagicMock()
    department_repo = MagicMock()
    semester_repo = MagicMock()
    monkeypatch.setattr(fee_service_module, "fee_repo", fee_repo)
    monkeypatch.setattr(fee_service_module, "user_repo", user_repo)
    monkeypatch.setattr(fee_service_module, "department_repo", department_repo)
    monkeypatch.setattr(fee_service_module, "semester_repo", semester_repo)
    return fee_repo, user_repo, department_repo, semester_repo


@pytest.fixture
def service():
    return FeeService()


@pytest.fixture
def session():
    return MagicMock()


def _admin_user():
    return User(id=uuid.uuid4(), email="a@example.com", role="admin")


def _student_user():
    return User(id=uuid.uuid4(), email="s@example.com", role="student")


def _parent_user():
    return User(id=uuid.uuid4(), email="p@example.com", role="parent")


class TestCreateFeeStructure:
    def test_rule4_invalid_semester_rejected(self, service, stub_repos, session):
        _fee_repo, _user_repo, _department_repo, semester_repo = stub_repos
        semester_repo.get.return_value = None
        payload = FeeStructureCreate(semester_id=uuid.uuid4(), name="Tuition", amount=1000, due_date=date(2030, 1, 1))
        with pytest.raises(HTTPException) as exc:
            service.create_fee_structure(session, _admin_user(), payload)
        assert exc.value.status_code == 422

    def test_invalid_department_rejected(self, service, stub_repos, session):
        fee_repo, _user_repo, department_repo, semester_repo = stub_repos
        semester_repo.get.return_value = make_semester()
        department_repo.get.return_value = None
        payload = FeeStructureCreate(
            department_id=uuid.uuid4(), semester_id=uuid.uuid4(), name="Tuition", amount=1000, due_date=date(2030, 1, 1)
        )
        with pytest.raises(HTTPException) as exc:
            service.create_fee_structure(session, _admin_user(), payload)
        assert exc.value.status_code == 422
        fee_repo.create_fee_structure.assert_not_called()

    def test_rule3_invoices_generated_only_for_eligible_students(self, service, stub_repos, session):
        fee_repo, _user_repo, _department_repo, semester_repo = stub_repos
        semester_repo.get.return_value = make_semester()
        fee_structure = make_fee_structure()
        fee_repo.create_fee_structure.return_value = fee_structure
        eligible = [make_student(), make_student()]
        fee_repo.list_eligible_students.return_value = eligible
        fee_repo.get_invoice_by_student_fee_structure.return_value = None

        payload = FeeStructureCreate(semester_id=fee_structure.semester_id, name="Tuition", amount=1000, due_date=date(2030, 1, 1))
        result = service.create_fee_structure(session, _admin_user(), payload)

        assert result.invoices_created == 2
        assert fee_repo.create_invoice.call_count == 2
        # 1 commit for the invoice-generation batch itself, plus 1 more per
        # eligible student for the Milestone 9 fee_due dispatch (each
        # dispatch commits independently — see
        # tests/unit/test_notification_dispatcher.py for dispatch-specific
        # coverage).
        assert session.commit.call_count == 3

    def test_rule5_defensive_duplicate_skip(self, service, stub_repos, session):
        fee_repo, _user_repo, _department_repo, semester_repo = stub_repos
        semester_repo.get.return_value = make_semester()
        fee_structure = make_fee_structure()
        fee_repo.create_fee_structure.return_value = fee_structure
        student = make_student()
        fee_repo.list_eligible_students.return_value = [student]
        fee_repo.get_invoice_by_student_fee_structure.return_value = make_invoice()  # already exists

        payload = FeeStructureCreate(semester_id=fee_structure.semester_id, name="Tuition", amount=1000, due_date=date(2030, 1, 1))
        result = service.create_fee_structure(session, _admin_user(), payload)

        assert result.invoices_created == 0
        fee_repo.create_invoice.assert_not_called()

    def test_no_eligible_students_creates_zero_invoices(self, service, stub_repos, session):
        fee_repo, _user_repo, _department_repo, semester_repo = stub_repos
        semester_repo.get.return_value = make_semester()
        fee_structure = make_fee_structure()
        fee_repo.create_fee_structure.return_value = fee_structure
        fee_repo.list_eligible_students.return_value = []

        payload = FeeStructureCreate(semester_id=fee_structure.semester_id, name="Tuition", amount=1000, due_date=date(2030, 1, 1))
        result = service.create_fee_structure(session, _admin_user(), payload)
        assert result.invoices_created == 0


class TestRecordPayment:
    def _setup(self, stub_repos, *, invoice_status="unpaid", fee_amount=10000, paid_so_far=0.0, student_active=True):
        fee_repo, user_repo, *_ = stub_repos
        student = make_student()
        student_user = User(id=uuid.uuid4(), email="s@example.com", role="student", is_active=student_active)
        user_repo.get_student_with_user.return_value = (student, student_user)
        user_repo.get_admin_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())
        fee_structure = make_fee_structure(amount=fee_amount)
        fee_repo.get_fee_structure.return_value = fee_structure
        invoice = make_invoice(student_id=student.id, fee_structure_id=fee_structure.id, status=invoice_status)
        fee_repo.get_invoice_by_student_fee_structure.return_value = invoice
        fee_repo.sum_payments.return_value = paid_so_far
        return student, fee_structure, invoice

    def test_student_not_found_raises_404(self, service, stub_repos, session):
        fee_repo, user_repo, *_ = stub_repos
        user_repo.get_student_with_user.return_value = None
        payload = PaymentCreate(student_id=uuid.uuid4(), fee_structure_id=uuid.uuid4(), amount=100, payment_date=datetime.now(timezone.utc))
        with pytest.raises(HTTPException) as exc:
            service.record_payment(session, _admin_user(), payload)
        assert exc.value.status_code == 404

    def test_rule2_inactive_student_rejected(self, service, stub_repos, session):
        student, fee_structure, _invoice = self._setup(stub_repos, student_active=False)
        payload = PaymentCreate(student_id=student.id, fee_structure_id=fee_structure.id, amount=100, payment_date=datetime.now(timezone.utc))
        with pytest.raises(HTTPException) as exc:
            service.record_payment(session, _admin_user(), payload)
        assert exc.value.status_code == 422

    def test_fee_structure_not_found_raises_404(self, service, stub_repos, session):
        fee_repo, user_repo, *_ = stub_repos
        student = make_student()
        user_repo.get_student_with_user.return_value = (student, User(id=uuid.uuid4(), email="s@x.com", role="student", is_active=True))
        fee_repo.get_fee_structure.return_value = None
        payload = PaymentCreate(student_id=student.id, fee_structure_id=uuid.uuid4(), amount=100, payment_date=datetime.now(timezone.utc))
        with pytest.raises(HTTPException) as exc:
            service.record_payment(session, _admin_user(), payload)
        assert exc.value.status_code == 404

    def test_no_invoice_exists_raises_404(self, service, stub_repos, session):
        fee_repo, user_repo, *_ = stub_repos
        student = make_student()
        user_repo.get_student_with_user.return_value = (student, User(id=uuid.uuid4(), email="s@x.com", role="student", is_active=True))
        fee_structure = make_fee_structure()
        fee_repo.get_fee_structure.return_value = fee_structure
        fee_repo.get_invoice_by_student_fee_structure.return_value = None
        payload = PaymentCreate(student_id=student.id, fee_structure_id=fee_structure.id, amount=100, payment_date=datetime.now(timezone.utc))
        with pytest.raises(HTTPException) as exc:
            service.record_payment(session, _admin_user(), payload)
        assert exc.value.status_code == 404

    def test_rule9_fully_paid_invoice_rejects_payment(self, service, stub_repos, session):
        student, fee_structure, _invoice = self._setup(stub_repos, invoice_status="paid")
        payload = PaymentCreate(student_id=student.id, fee_structure_id=fee_structure.id, amount=1, payment_date=datetime.now(timezone.utc))
        with pytest.raises(HTTPException) as exc:
            service.record_payment(session, _admin_user(), payload)
        assert exc.value.status_code == 409

    def test_rule6_overpayment_beyond_outstanding_rejected(self, service, stub_repos, session):
        fee_repo, _user_repo, *_ = stub_repos
        student, fee_structure, _invoice = self._setup(stub_repos, fee_amount=10000, paid_so_far=4000)
        payload = PaymentCreate(student_id=student.id, fee_structure_id=fee_structure.id, amount=7000, payment_date=datetime.now(timezone.utc))
        with pytest.raises(HTTPException) as exc:
            service.record_payment(session, _admin_user(), payload)
        assert exc.value.status_code == 409
        fee_repo.create_payment.assert_not_called()

    def test_exact_remaining_balance_succeeds_and_marks_paid(self, service, stub_repos, session):
        fee_repo, _user_repo, *_ = stub_repos
        student, fee_structure, _invoice = self._setup(stub_repos, fee_amount=10000, paid_so_far=4000)
        fee_repo.create_payment.return_value = make_payment(amount=6000, fee_structure_id=fee_structure.id)
        payload = PaymentCreate(student_id=student.id, fee_structure_id=fee_structure.id, amount=6000, payment_date=datetime.now(timezone.utc))
        service.record_payment(session, _admin_user(), payload)
        fee_repo.update_invoice_status.assert_called_once()
        args, kwargs = fee_repo.update_invoice_status.call_args
        assert args[-1] == "paid"

    def test_partial_payment_marks_partially_paid(self, service, stub_repos, session):
        fee_repo, _user_repo, *_ = stub_repos
        student, fee_structure, _invoice = self._setup(stub_repos, fee_amount=10000, paid_so_far=0)
        fee_repo.create_payment.return_value = make_payment(amount=3000, fee_structure_id=fee_structure.id)
        payload = PaymentCreate(student_id=student.id, fee_structure_id=fee_structure.id, amount=3000, payment_date=datetime.now(timezone.utc))
        service.record_payment(session, _admin_user(), payload)
        args, kwargs = fee_repo.update_invoice_status.call_args
        assert args[-1] == "partially_paid"
        session.commit.assert_called_once()


class TestGetMyFees:
    def test_rule12_parent_missing_student_id_forbidden(self, service, stub_repos, session):
        _fee_repo, user_repo, *_ = stub_repos
        user_repo.get_parent_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())
        with pytest.raises(HTTPException) as exc:
            service.get_my_fees(session, _parent_user(), semester_id=None, student_id=None)
        assert exc.value.status_code == 403

    def test_rule12_parent_unlinked_student_forbidden(self, service, stub_repos, session):
        _fee_repo, user_repo, *_ = stub_repos
        user_repo.get_parent_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())
        user_repo.parent_has_linked_student.return_value = False
        with pytest.raises(HTTPException) as exc:
            service.get_my_fees(session, _parent_user(), semester_id=None, student_id=uuid.uuid4())
        assert exc.value.status_code == 403

    def test_outstanding_balance_computed_from_persisted_payments(self, service, stub_repos, session):
        fee_repo, user_repo, *_ = stub_repos
        student = make_student()
        user_repo.get_student_profile_by_user_id.return_value = student
        fee_structure = make_fee_structure(amount=10000, due_date=date(2030, 1, 1))
        invoice = make_invoice(student_id=student.id, fee_structure_id=fee_structure.id, status="partially_paid")
        fee_repo.list_invoices_for_student.return_value = [invoice]
        fee_repo.get_fee_structure.return_value = fee_structure
        fee_repo.sum_payments.return_value = 4000.0
        fee_repo.list_payments_for_student.return_value = [make_payment(amount=4000, fee_structure_id=fee_structure.id)]

        response = service.get_my_fees(session, _student_user(), semester_id=None, student_id=None)
        assert response.outstanding_balance == 6000.0
        assert response.invoices[0].status == "partially_paid"

    def test_derived_overdue_status_overrides_stored_status(self, service, stub_repos, session):
        fee_repo, user_repo, *_ = stub_repos
        student = make_student()
        user_repo.get_student_profile_by_user_id.return_value = student
        fee_structure = make_fee_structure(amount=10000, due_date=date(2020, 1, 1))
        invoice = make_invoice(student_id=student.id, fee_structure_id=fee_structure.id, status="unpaid")
        fee_repo.list_invoices_for_student.return_value = [invoice]
        fee_repo.get_fee_structure.return_value = fee_structure
        fee_repo.sum_payments.return_value = 0.0
        fee_repo.list_payments_for_student.return_value = []

        response = service.get_my_fees(session, _student_user(), semester_id=None, student_id=None)
        assert response.invoices[0].status == "overdue"


class TestGetPaymentHistory:
    def test_student_not_found_raises_404(self, service, stub_repos, session):
        _fee_repo, user_repo, *_ = stub_repos
        user_repo.get_student_with_user.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.get_payment_history(session, _admin_user(), uuid.uuid4())
        assert exc.value.status_code == 404

    def test_rule12_parent_without_link_forbidden(self, service, stub_repos, session):
        fee_repo, user_repo, *_ = stub_repos
        student = make_student()
        user_repo.get_student_with_user.return_value = (student, User(id=uuid.uuid4(), email="s@x.com", role="student"))
        user_repo.get_parent_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())
        user_repo.parent_has_linked_student.return_value = False
        with pytest.raises(HTTPException) as exc:
            service.get_payment_history(session, _parent_user(), student.id)
        assert exc.value.status_code == 403


class TestGetInvoiceData:
    def test_invoice_not_found_raises_404(self, service, stub_repos, session):
        fee_repo, *_ = stub_repos
        fee_repo.get_invoice.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.get_invoice_data(session, _admin_user(), uuid.uuid4())
        assert exc.value.status_code == 404

    def test_rule11_student_cannot_view_other_students_invoice(self, service, stub_repos, session):
        fee_repo, user_repo, *_ = stub_repos
        invoice = make_invoice()
        fee_repo.get_invoice.return_value = invoice
        user_repo.get_student_profile_by_user_id.return_value = make_student()  # different id

        with pytest.raises(HTTPException) as exc:
            service.get_invoice_data(session, _student_user(), invoice.id)
        assert exc.value.status_code == 403

    def test_admin_can_view_any_invoice(self, service, stub_repos, session):
        fee_repo, user_repo, *_ = stub_repos
        student = make_student()
        invoice = make_invoice(student_id=student.id)
        fee_repo.get_invoice.return_value = invoice
        fee_structure = make_fee_structure(id=invoice.fee_structure_id)
        fee_repo.get_fee_structure.return_value = fee_structure
        user_repo.get_student_with_user.return_value = (student, User(id=uuid.uuid4(), email="s@x.com", role="student"))
        fee_repo.sum_payments.return_value = 0.0

        data = service.get_invoice_data(session, _admin_user(), invoice.id)
        assert data["student_name"] == "S Student"
        assert data["outstanding"] == float(fee_structure.amount)


class TestGetOverdueAccounts:
    def test_invalid_department_rejected(self, service, stub_repos, session):
        _fee_repo, _user_repo, department_repo, _semester_repo = stub_repos
        department_repo.get.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.get_overdue_accounts(session, uuid.uuid4(), None)
        assert exc.value.status_code == 422

    def test_only_past_due_unpaid_invoices_included(self, service, stub_repos, session):
        fee_repo, *_ = stub_repos
        fee_structure_past = make_fee_structure(due_date=date(2020, 1, 1), amount=5000)
        fee_structure_future = make_fee_structure(due_date=date(2030, 1, 1), amount=3000)
        invoice_past = make_invoice(fee_structure_id=fee_structure_past.id, status="unpaid")
        invoice_future = make_invoice(fee_structure_id=fee_structure_future.id, status="unpaid")
        fee_repo.list_unpaid_or_partial_invoices.return_value = [
            (invoice_past, fee_structure_past),
            (invoice_future, fee_structure_future),
        ]
        fee_repo.sum_payments.return_value = 0.0

        result = service.get_overdue_accounts(session, None, None)
        assert len(result.overdue_accounts) == 1
        assert result.overdue_accounts[0].amount_due == 5000.0
        assert result.overdue_accounts[0].days_overdue > 0


class TestNotifyOverdueAccounts:
    """Milestone 10: POST /fees/overdue/notify. Verifies this reuses the
    existing Notification Dispatcher (`dispatcher.notify_fee_due`) rather
    than introducing a second notification system, and that the
    scope="selected" path validates the whole batch before any dispatch
    (Domain Rule 15 pattern)."""

    def test_scope_all_overdue_notifies_every_overdue_student(self, service, stub_repos, session, monkeypatch):
        fee_repo, user_repo, *_ = stub_repos
        notify_mock = MagicMock()
        monkeypatch.setattr(fee_service_module.dispatcher, "notify_fee_due", notify_mock)

        fee_structure_past = make_fee_structure(due_date=date(2020, 1, 1), amount=5000)
        fee_structure_future = make_fee_structure(due_date=date(2030, 1, 1), amount=3000)
        invoice_past = make_invoice(fee_structure_id=fee_structure_past.id, status="unpaid")
        invoice_future = make_invoice(fee_structure_id=fee_structure_future.id, status="unpaid")
        fee_repo.list_unpaid_or_partial_invoices.return_value = [
            (invoice_past, fee_structure_past),
            (invoice_future, fee_structure_future),
        ]
        student = make_student(id=invoice_past.student_id)
        user_repo.get_student_with_user.return_value = (student, User(id=uuid.uuid4(), email="s@x.com", role="student"))

        payload = OverdueNotifyRequest(student_ids=[], scope="all_overdue")
        result = service.notify_overdue_accounts(session, payload)

        assert result.notified_count == 1
        notify_mock.assert_called_once()
        _args, kwargs = notify_mock.call_args
        assert kwargs["student_id"] == invoice_past.student_id
        assert kwargs["amount"] == 5000.0

    def test_scope_selected_rejects_student_without_overdue_invoice(self, service, stub_repos, session, monkeypatch):
        fee_repo, user_repo, *_ = stub_repos
        notify_mock = MagicMock()
        monkeypatch.setattr(fee_service_module.dispatcher, "notify_fee_due", notify_mock)
        fee_repo.list_unpaid_or_partial_invoices.return_value = []

        payload = OverdueNotifyRequest(student_ids=[uuid.uuid4()], scope="selected")
        with pytest.raises(HTTPException) as exc:
            service.notify_overdue_accounts(session, payload)
        assert exc.value.status_code == 422
        notify_mock.assert_not_called()

    def test_scope_selected_empty_student_ids_rejected(self, service, stub_repos, session):
        payload = OverdueNotifyRequest(student_ids=[], scope="selected")
        with pytest.raises(HTTPException) as exc:
            service.notify_overdue_accounts(session, payload)
        assert exc.value.status_code == 422

    def test_scope_selected_notifies_only_named_students(self, service, stub_repos, session, monkeypatch):
        fee_repo, user_repo, *_ = stub_repos
        notify_mock = MagicMock()
        monkeypatch.setattr(fee_service_module.dispatcher, "notify_fee_due", notify_mock)

        fee_structure = make_fee_structure(due_date=date(2020, 1, 1), amount=1000)
        invoice_selected = make_invoice(fee_structure_id=fee_structure.id, status="unpaid")
        invoice_other = make_invoice(fee_structure_id=fee_structure.id, status="unpaid")
        fee_repo.list_unpaid_or_partial_invoices.return_value = [
            (invoice_selected, fee_structure),
            (invoice_other, fee_structure),
        ]
        student = make_student(id=invoice_selected.student_id)
        user_repo.get_student_with_user.return_value = (student, User(id=uuid.uuid4(), email="s@x.com", role="student"))

        payload = OverdueNotifyRequest(student_ids=[invoice_selected.student_id], scope="selected")
        result = service.notify_overdue_accounts(session, payload)

        assert result.notified_count == 1
        notify_mock.assert_called_once()
