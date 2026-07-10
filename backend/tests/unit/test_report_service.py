"""
Unit tests: app.services.report_service.ReportService.

Repositories are stubbed (per CLAUDE.md §10) so these tests exercise the
Milestone 10 Reporting Requirements directly, without a database:
  - GET /results/reports: filter validation (422 on unknown department/
    semester/student), only-published-results inclusion, pass/fail
    threshold (grade_point > 0 = pass, == 0 = fail), and reuse of the
    existing credit-weighted GPA formula.
  - GET /fees/reports: filter validation, total_collected/outstanding
    computed from persisted payments, and total_overdue as the derived
    subset of total_outstanding (reusing fee_service._derived_status
    rather than reimplementing overdue detection).
"""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models.course import Course
from app.models.department import Department
from app.models.fee_structure import FeeStructure
from app.models.invoice import Invoice
from app.models.result import Result
from app.models.semester import Semester
from app.services import report_service as report_service_module
from app.services import result_service as result_service_module
from app.services.report_service import ReportService


def make_department(**overrides) -> Department:
    defaults = dict(id=uuid.uuid4(), name="CS", code="CS1")
    defaults.update(overrides)
    return Department(**defaults)


def make_semester(**overrides) -> Semester:
    defaults = dict(id=uuid.uuid4(), name="Spring 2026", start_date=date(2026, 1, 1), end_date=date(2026, 5, 1))
    defaults.update(overrides)
    return Semester(**defaults)


def make_course(**overrides) -> Course:
    defaults = dict(id=uuid.uuid4(), department_id=uuid.uuid4(), name="DB Systems", code="CS101", credit_hours=3)
    defaults.update(overrides)
    return Course(**defaults)


def make_result(**overrides) -> Result:
    defaults = dict(
        id=uuid.uuid4(), student_id=uuid.uuid4(), course_id=uuid.uuid4(), semester_id=uuid.uuid4(), exam_id=uuid.uuid4(),
        submitted_by_teacher_id=uuid.uuid4(), approved_by_admin_id=uuid.uuid4(), grade_letter="A", grade_point=4.0,
        status="published", submitted_at=datetime.now(timezone.utc), approved_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return Result(**defaults)


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


@pytest.fixture
def stub_repos(monkeypatch):
    result_repo = MagicMock()
    fee_repo = MagicMock()
    department_repo = MagicMock()
    semester_repo = MagicMock()
    user_repo = MagicMock()
    # Detail-section gap closure: get_results_report/get_fees_report now
    # also batch-resolve student names and per-result course/exam names
    # (see report_service.py). Defaulted here so every pre-existing test
    # below — none of which assert on `.details` — doesn't need to know
    # about this; only tests that care about the detail rows configure
    # these further.
    user_repo.list_students_by_ids.return_value = []
    course_repo = MagicMock()
    course_repo.get.return_value = make_course()
    exam_repo = MagicMock()
    exam_repo.get_exam.return_value = None
    monkeypatch.setattr(report_service_module, "result_repo", result_repo)
    monkeypatch.setattr(report_service_module, "fee_repo", fee_repo)
    monkeypatch.setattr(report_service_module, "department_repo", department_repo)
    monkeypatch.setattr(report_service_module, "semester_repo", semester_repo)
    monkeypatch.setattr(report_service_module, "user_repo", user_repo)
    monkeypatch.setattr(report_service_module, "course_repo", course_repo)
    monkeypatch.setattr(report_service_module, "exam_repo", exam_repo)
    return result_repo, fee_repo, department_repo, semester_repo, user_repo


@pytest.fixture
def service():
    return ReportService()


@pytest.fixture
def session():
    return MagicMock()


class TestGetResultsReport:
    def test_invalid_department_rejected(self, service, stub_repos, session):
        _result_repo, _fee_repo, department_repo, _semester_repo, _user_repo = stub_repos
        department_repo.get.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.get_results_report(session, department_id=uuid.uuid4(), semester_id=None, student_id=None)
        assert exc.value.status_code == 422

    def test_invalid_semester_rejected(self, service, stub_repos, session):
        _result_repo, _fee_repo, _department_repo, semester_repo, _user_repo = stub_repos
        semester_repo.get.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.get_results_report(session, department_id=None, semester_id=uuid.uuid4(), student_id=None)
        assert exc.value.status_code == 422

    def test_invalid_student_rejected(self, service, stub_repos, session):
        _result_repo, _fee_repo, _department_repo, _semester_repo, user_repo = stub_repos
        user_repo.get_student_with_user.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.get_results_report(session, department_id=None, semester_id=None, student_id=uuid.uuid4())
        assert exc.value.status_code == 422

    def test_pass_fail_counted_by_grade_point_threshold(self, service, stub_repos, session, monkeypatch):
        result_repo, *_ = stub_repos
        monkeypatch.setattr(result_service_module, "course_repo", MagicMock(get=lambda *_a, **_k: make_course()))
        passing = make_result(grade_letter="A", grade_point=4.0)
        failing = make_result(grade_letter="F", grade_point=0.0)
        result_repo.list_published_for_report.return_value = [passing, failing]

        response = service.get_results_report(session, department_id=None, semester_id=None, student_id=None)
        assert response.pass_count == 1
        assert response.fail_count == 1

    def test_grade_distribution_counts_each_letter(self, service, stub_repos, session, monkeypatch):
        result_repo, *_ = stub_repos
        monkeypatch.setattr(result_service_module, "course_repo", MagicMock(get=lambda *_a, **_k: make_course()))
        result_repo.list_published_for_report.return_value = [
            make_result(grade_letter="A", grade_point=4.0),
            make_result(grade_letter="A", grade_point=4.0),
            make_result(grade_letter="B", grade_point=3.0),
        ]

        response = service.get_results_report(session, department_id=None, semester_id=None, student_id=None)
        distribution = {e.grade_letter: e.count for e in response.grade_distribution}
        assert distribution == {"A": 2, "B": 1}

    def test_average_gpa_reuses_credit_weighted_formula(self, service, stub_repos, session, monkeypatch):
        result_repo, *_ = stub_repos
        results = [make_result(grade_point=4.0), make_result(grade_point=2.0)]
        result_repo.list_published_for_report.return_value = results

        gpa_mock = MagicMock(return_value=3.14)
        monkeypatch.setattr(report_service_module, "compute_credit_weighted_gpa", gpa_mock)

        response = service.get_results_report(session, department_id=None, semester_id=None, student_id=None)
        gpa_mock.assert_called_once_with(session, results)
        assert response.average_gpa == 3.14

    def test_only_published_results_requested_from_repository(self, service, stub_repos, session):
        result_repo, *_ = stub_repos
        result_repo.list_published_for_report.return_value = []
        department_id = uuid.uuid4()
        semester_id = uuid.uuid4()
        student_id = uuid.uuid4()

        service.get_results_report(session, department_id=department_id, semester_id=semester_id, student_id=student_id)
        result_repo.list_published_for_report.assert_called_once_with(
            session, department_id=department_id, semester_id=semester_id, student_id=student_id
        )

    def test_details_include_student_course_exam_and_grade(self, service, stub_repos, session, monkeypatch):
        result_repo, _fee_repo, _department_repo, _semester_repo, user_repo = stub_repos
        from app.models.student import Student
        from app.models.user import User

        student_id = uuid.uuid4()
        result = make_result(student_id=student_id, grade_letter="A", grade_point=4.0)
        result_repo.list_published_for_report.return_value = [result]
        student = Student(id=student_id, user_id=uuid.uuid4(), department_id=uuid.uuid4(), first_name="Rafiq", last_name="Chowdhury")
        user_repo.list_students_by_ids.return_value = [student]

        course = make_course(name="Data Structures")
        monkeypatch.setattr(report_service_module, "course_repo", MagicMock(get=lambda *_a, **_k: course))
        monkeypatch.setattr(result_service_module, "course_repo", MagicMock(get=lambda *_a, **_k: course))

        from app.models.exam import Exam

        exam = Exam(
            id=result.exam_id, class_session_id=uuid.uuid4(), created_by_teacher_id=uuid.uuid4(), title="Midterm",
            exam_type="mcq", time_limit_minutes=30, status="published",
        )
        monkeypatch.setattr(report_service_module, "exam_repo", MagicMock(get_exam=lambda *_a, **_k: exam))

        response = service.get_results_report(session, department_id=None, semester_id=None, student_id=None)
        assert len(response.details) == 1
        detail = response.details[0]
        assert detail.student_name == "Rafiq Chowdhury"
        assert detail.course_name == "Data Structures"
        assert detail.exam_title == "Midterm"
        assert detail.grade_letter == "A"
        assert detail.grade_point == 4.0


class TestGetFeesReport:
    def test_invalid_department_rejected(self, service, stub_repos, session):
        _result_repo, _fee_repo, department_repo, _semester_repo, _user_repo = stub_repos
        department_repo.get.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.get_fees_report(session, department_id=uuid.uuid4(), semester_id=None, student_id=None)
        assert exc.value.status_code == 422

    def test_total_collected_sums_persisted_payments(self, service, stub_repos, session):
        _result_repo, fee_repo, *_ = stub_repos
        fee_structure = make_fee_structure(amount=10000, due_date=date(2030, 1, 1))
        invoice = make_invoice(fee_structure_id=fee_structure.id, status="partially_paid")
        fee_repo.list_invoices_for_report.return_value = [(invoice, fee_structure)]
        fee_repo.sum_payments.return_value = 4000.0

        response = service.get_fees_report(session, department_id=None, semester_id=None, student_id=None)
        assert response.total_collected == 4000.0
        assert response.total_outstanding == 6000.0
        assert response.total_overdue == 0.0

    def test_total_overdue_is_subset_of_outstanding(self, service, stub_repos, session):
        _result_repo, fee_repo, *_ = stub_repos
        overdue_structure = make_fee_structure(amount=5000, due_date=date(2020, 1, 1))
        overdue_invoice = make_invoice(fee_structure_id=overdue_structure.id, status="unpaid")
        current_structure = make_fee_structure(amount=3000, due_date=date(2030, 1, 1))
        current_invoice = make_invoice(fee_structure_id=current_structure.id, status="unpaid")
        fee_repo.list_invoices_for_report.return_value = [
            (overdue_invoice, overdue_structure),
            (current_invoice, current_structure),
        ]
        fee_repo.sum_payments.return_value = 0.0

        response = service.get_fees_report(session, department_id=None, semester_id=None, student_id=None)
        assert response.total_outstanding == 8000.0
        assert response.total_overdue == 5000.0

    def test_fully_paid_invoice_contributes_nothing_outstanding(self, service, stub_repos, session):
        _result_repo, fee_repo, *_ = stub_repos
        fee_structure = make_fee_structure(amount=1000, due_date=date(2020, 1, 1))
        invoice = make_invoice(fee_structure_id=fee_structure.id, status="paid")
        fee_repo.list_invoices_for_report.return_value = [(invoice, fee_structure)]
        fee_repo.sum_payments.return_value = 1000.0

        response = service.get_fees_report(session, department_id=None, semester_id=None, student_id=None)
        assert response.total_outstanding == 0.0
        assert response.total_overdue == 0.0

    def test_details_include_student_fee_name_and_amounts(self, service, stub_repos, session):
        _result_repo, fee_repo, _department_repo, _semester_repo, user_repo = stub_repos
        from app.models.student import Student

        student_id = uuid.uuid4()
        fee_structure = make_fee_structure(name="Tuition", amount=10000, due_date=date(2020, 1, 1))
        invoice = make_invoice(student_id=student_id, fee_structure_id=fee_structure.id, status="unpaid")
        fee_repo.list_invoices_for_report.return_value = [(invoice, fee_structure)]
        fee_repo.sum_payments.return_value = 4000.0
        student = Student(id=student_id, user_id=uuid.uuid4(), department_id=uuid.uuid4(), first_name="Rafiq", last_name="Chowdhury")
        user_repo.list_students_by_ids.return_value = [student]

        response = service.get_fees_report(session, department_id=None, semester_id=None, student_id=None)
        assert len(response.details) == 1
        detail = response.details[0]
        assert detail.student_name == "Rafiq Chowdhury"
        assert detail.fee_name == "Tuition"
        assert detail.amount == 10000.0
        assert detail.paid == 4000.0
        assert detail.outstanding == 6000.0
        assert detail.status == "overdue"
