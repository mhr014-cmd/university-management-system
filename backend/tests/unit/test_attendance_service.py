"""
Unit tests: app.services.attendance_service.AttendanceService.

Repositories are stubbed (per CLAUDE.md §10) so these tests exercise the
Milestone 5 mandatory Attendance Domain Rules directly:
  1. Student exists and is active
  2. Class session exists
  3. Schedule entry exists for the class session
  4. Student has a valid Enrollment for the class session
  5. No duplicate attendance record for the same student/class/date
  6. Unrelated students/class sessions are rejected (via Rules 1/4)
  7. Teacher may only act on a class session they are assigned to
  8. Students cannot mark/modify attendance (enforced at the router RBAC
     level — not re-tested here, see test_attendance_router.py)
  9. Parent access is exactly what is documented (GET /attendance/{classId}
     only, scoped via ParentStudentLink)
  10. All validation happens before any database write
"""

import uuid
from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models.attendance_record import AttendanceRecord
from app.models.class_session import ClassSession
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.user import User
from app.schemas.attendance import AttendanceMarkRequest, AttendanceMeQuery, AttendanceRecordInput, AttendanceUpdateRequest
from app.services import attendance_service as attendance_service_module
from app.services.attendance_service import AttendanceService


def make_class_session(**overrides) -> ClassSession:
    defaults = dict(id=uuid.uuid4(), course_id=uuid.uuid4(), teacher_id=uuid.uuid4(), semester_id=uuid.uuid4(), section_label="A")
    defaults.update(overrides)
    return ClassSession(**defaults)


def make_teacher(**overrides) -> Teacher:
    defaults = dict(id=uuid.uuid4(), user_id=uuid.uuid4(), department_id=uuid.uuid4(), first_name="T", last_name="Teacher")
    defaults.update(overrides)
    return Teacher(**defaults)


def make_student_row(**overrides):
    defaults = dict(
        student=Student(id=uuid.uuid4(), user_id=uuid.uuid4(), department_id=uuid.uuid4(), first_name="S", last_name="Student"),
        user=User(id=uuid.uuid4(), email="s@example.com", role="student", is_active=True),
    )
    defaults.update(overrides)
    return (defaults["student"], defaults["user"])


@pytest.fixture
def stub_repos(monkeypatch):
    attendance_repo = MagicMock()
    schedule_repo = MagicMock()
    user_repo = MagicMock()
    department_repo = MagicMock()
    semester_repo = MagicMock()
    monkeypatch.setattr(attendance_service_module, "attendance_repo", attendance_repo)
    monkeypatch.setattr(attendance_service_module, "schedule_repo", schedule_repo)
    monkeypatch.setattr(attendance_service_module, "user_repo", user_repo)
    monkeypatch.setattr(attendance_service_module, "department_repo", department_repo)
    monkeypatch.setattr(attendance_service_module, "semester_repo", semester_repo)
    return attendance_repo, schedule_repo, user_repo, department_repo, semester_repo


@pytest.fixture
def service():
    return AttendanceService()


@pytest.fixture
def session():
    return MagicMock()


def _teacher_user(teacher_id=None):
    return User(id=uuid.uuid4(), email="t@example.com", role="teacher")


class TestMarkAttendance:
    def test_rule2_class_session_must_exist(self, service, stub_repos, session):
        _attendance_repo, schedule_repo, user_repo, *_ = stub_repos
        user_repo.get_teacher_profile_by_user_id.return_value = make_teacher()
        schedule_repo.get_class_session.return_value = None

        payload = AttendanceMarkRequest(
            class_session_id=uuid.uuid4(), attendance_date=date.today(), records=[AttendanceRecordInput(student_id=uuid.uuid4(), status="present")]
        )
        with pytest.raises(HTTPException) as exc:
            service.mark_attendance(session, _teacher_user(), payload)
        assert exc.value.status_code == 404

    def test_rule7_teacher_must_be_assigned_to_class_session(self, service, stub_repos, session):
        _attendance_repo, schedule_repo, user_repo, *_ = stub_repos
        teacher = make_teacher()
        user_repo.get_teacher_profile_by_user_id.return_value = teacher
        schedule_repo.get_class_session.return_value = make_class_session(teacher_id=uuid.uuid4())  # different teacher

        payload = AttendanceMarkRequest(
            class_session_id=uuid.uuid4(), attendance_date=date.today(), records=[AttendanceRecordInput(student_id=uuid.uuid4(), status="present")]
        )
        with pytest.raises(HTTPException) as exc:
            service.mark_attendance(session, _teacher_user(), payload)
        assert exc.value.status_code == 403
        schedule_repo.class_session_has_schedule_entry.assert_not_called()

    def test_rule3_schedule_entry_must_exist(self, service, stub_repos, session):
        _attendance_repo, schedule_repo, user_repo, *_ = stub_repos
        teacher = make_teacher()
        user_repo.get_teacher_profile_by_user_id.return_value = teacher
        schedule_repo.get_class_session.return_value = make_class_session(teacher_id=teacher.id)
        schedule_repo.class_session_has_schedule_entry.return_value = False

        payload = AttendanceMarkRequest(
            class_session_id=uuid.uuid4(), attendance_date=date.today(), records=[AttendanceRecordInput(student_id=uuid.uuid4(), status="present")]
        )
        with pytest.raises(HTTPException) as exc:
            service.mark_attendance(session, _teacher_user(), payload)
        assert exc.value.status_code == 422

    def test_vr005_future_dated_attendance_rejected(self, service, stub_repos, session):
        _attendance_repo, schedule_repo, user_repo, *_ = stub_repos
        teacher = make_teacher()
        user_repo.get_teacher_profile_by_user_id.return_value = teacher
        schedule_repo.get_class_session.return_value = make_class_session(teacher_id=teacher.id)
        schedule_repo.class_session_has_schedule_entry.return_value = True

        payload = AttendanceMarkRequest(
            class_session_id=uuid.uuid4(),
            attendance_date=date.today() + timedelta(days=1),
            records=[AttendanceRecordInput(student_id=uuid.uuid4(), status="present")],
        )
        with pytest.raises(HTTPException) as exc:
            service.mark_attendance(session, _teacher_user(), payload)
        assert exc.value.status_code == 422

    def test_rule1_deactivated_student_rejected(self, service, stub_repos, session):
        _attendance_repo, schedule_repo, user_repo, *_ = stub_repos
        teacher = make_teacher()
        user_repo.get_teacher_profile_by_user_id.return_value = teacher
        schedule_repo.get_class_session.return_value = make_class_session(teacher_id=teacher.id)
        schedule_repo.class_session_has_schedule_entry.return_value = True
        student, student_user = make_student_row()
        student_user.is_active = False
        user_repo.get_student_with_user.return_value = (student, student_user)

        payload = AttendanceMarkRequest(
            class_session_id=uuid.uuid4(), attendance_date=date.today(), records=[AttendanceRecordInput(student_id=student.id, status="present")]
        )
        with pytest.raises(HTTPException) as exc:
            service.mark_attendance(session, _teacher_user(), payload)
        assert exc.value.status_code == 422

    def test_rule4_student_must_be_enrolled(self, service, stub_repos, session):
        attendance_repo, schedule_repo, user_repo, *_ = stub_repos
        teacher = make_teacher()
        user_repo.get_teacher_profile_by_user_id.return_value = teacher
        schedule_repo.get_class_session.return_value = make_class_session(teacher_id=teacher.id)
        schedule_repo.class_session_has_schedule_entry.return_value = True
        student, student_user = make_student_row()
        user_repo.get_student_with_user.return_value = (student, student_user)
        schedule_repo.get_enrollment.return_value = None  # not enrolled

        payload = AttendanceMarkRequest(
            class_session_id=uuid.uuid4(), attendance_date=date.today(), records=[AttendanceRecordInput(student_id=student.id, status="present")]
        )
        with pytest.raises(HTTPException) as exc:
            service.mark_attendance(session, _teacher_user(), payload)
        assert exc.value.status_code == 422
        attendance_repo.create_record.assert_not_called()

    def test_rule5_duplicate_record_rejected(self, service, stub_repos, session):
        attendance_repo, schedule_repo, user_repo, *_ = stub_repos
        teacher = make_teacher()
        user_repo.get_teacher_profile_by_user_id.return_value = teacher
        schedule_repo.get_class_session.return_value = make_class_session(teacher_id=teacher.id)
        schedule_repo.class_session_has_schedule_entry.return_value = True
        student, student_user = make_student_row()
        user_repo.get_student_with_user.return_value = (student, student_user)
        schedule_repo.get_enrollment.return_value = MagicMock()
        attendance_repo.get_record.return_value = MagicMock()  # already exists

        payload = AttendanceMarkRequest(
            class_session_id=uuid.uuid4(), attendance_date=date.today(), records=[AttendanceRecordInput(student_id=student.id, status="present")]
        )
        with pytest.raises(HTTPException) as exc:
            service.mark_attendance(session, _teacher_user(), payload)
        assert exc.value.status_code == 409
        attendance_repo.create_record.assert_not_called()

    def test_rule10_all_records_validated_before_any_write(self, service, stub_repos, session):
        # Batch of two: first student valid, second student not enrolled.
        # Neither record should be created — validation must run for the
        # whole batch before any create_record call happens.
        attendance_repo, schedule_repo, user_repo, *_ = stub_repos
        teacher = make_teacher()
        user_repo.get_teacher_profile_by_user_id.return_value = teacher
        schedule_repo.get_class_session.return_value = make_class_session(teacher_id=teacher.id)
        schedule_repo.class_session_has_schedule_entry.return_value = True
        student_a, user_a = make_student_row()
        student_b, user_b = make_student_row()

        def get_student_with_user_side_effect(_session, student_id):
            if student_id == student_a.id:
                return (student_a, user_a)
            return (student_b, user_b)

        user_repo.get_student_with_user.side_effect = get_student_with_user_side_effect
        attendance_repo.get_record.return_value = None

        def get_enrollment_side_effect(_session, student_id, _class_session_id):
            return MagicMock() if student_id == student_a.id else None

        schedule_repo.get_enrollment.side_effect = get_enrollment_side_effect

        payload = AttendanceMarkRequest(
            class_session_id=uuid.uuid4(),
            attendance_date=date.today(),
            records=[
                AttendanceRecordInput(student_id=student_a.id, status="present"),
                AttendanceRecordInput(student_id=student_b.id, status="present"),
            ],
        )
        with pytest.raises(HTTPException) as exc:
            service.mark_attendance(session, _teacher_user(), payload)
        assert exc.value.status_code == 422
        attendance_repo.create_record.assert_not_called()
        session.commit.assert_not_called()

    def test_success_creates_all_records_in_one_transaction(self, service, stub_repos, session):
        attendance_repo, schedule_repo, user_repo, *_ = stub_repos
        teacher = make_teacher()
        user_repo.get_teacher_profile_by_user_id.return_value = teacher
        schedule_repo.get_class_session.return_value = make_class_session(teacher_id=teacher.id)
        schedule_repo.class_session_has_schedule_entry.return_value = True
        student, student_user = make_student_row()
        user_repo.get_student_with_user.return_value = (student, student_user)
        schedule_repo.get_enrollment.return_value = MagicMock()
        attendance_repo.get_record.return_value = None

        created_record = MagicMock(id=uuid.uuid4(), student_id=student.id, class_session_id=uuid.uuid4(), marked_by_teacher_id=teacher.id, attendance_date=date.today(), status="present")
        attendance_repo.create_record.return_value = created_record

        payload = AttendanceMarkRequest(
            class_session_id=uuid.uuid4(), attendance_date=date.today(), records=[AttendanceRecordInput(student_id=student.id, status="present")]
        )
        result = service.mark_attendance(session, _teacher_user(), payload)
        assert len(result) == 1
        session.commit.assert_called_once()


class TestUpdateAttendance:
    def test_not_found_raises_404(self, service, stub_repos, session):
        attendance_repo, *_ = stub_repos
        attendance_repo.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.update_attendance(session, _teacher_user(), uuid.uuid4(), AttendanceUpdateRequest(status="absent"))
        assert exc.value.status_code == 404

    def test_rule7_teacher_cannot_correct_unrelated_class_session(self, service, stub_repos, session):
        attendance_repo, schedule_repo, user_repo, *_ = stub_repos
        record = MagicMock(class_session_id=uuid.uuid4())
        attendance_repo.get_by_id.return_value = record
        teacher = make_teacher()
        user_repo.get_teacher_profile_by_user_id.return_value = teacher
        schedule_repo.get_class_session.return_value = make_class_session(teacher_id=uuid.uuid4())

        with pytest.raises(HTTPException) as exc:
            service.update_attendance(session, _teacher_user(), uuid.uuid4(), AttendanceUpdateRequest(status="absent"))
        assert exc.value.status_code == 403
        attendance_repo.update_status.assert_not_called()

    def test_admin_bypasses_ownership_check(self, service, stub_repos, session):
        attendance_repo, *_ = stub_repos
        record = MagicMock(
            id=uuid.uuid4(), class_session_id=uuid.uuid4(), student_id=uuid.uuid4(), marked_by_teacher_id=uuid.uuid4(),
            attendance_date=date.today(), status="absent",
        )
        attendance_repo.get_by_id.return_value = record
        admin_user = User(id=uuid.uuid4(), email="a@example.com", role="admin")

        service.update_attendance(session, admin_user, record.id, AttendanceUpdateRequest(status="present"))
        attendance_repo.update_status.assert_called_once()


class TestGetClassAttendance:
    def test_rule9_parent_requires_student_id(self, service, stub_repos, session):
        _attendance_repo, schedule_repo, _user_repo, *_ = stub_repos
        schedule_repo.get_class_session.return_value = make_class_session()
        parent_user = User(id=uuid.uuid4(), email="p@example.com", role="parent")

        with pytest.raises(HTTPException) as exc:
            service.get_class_attendance(session, parent_user, uuid.uuid4(), date_from=None, date_to=None, student_id=None)
        assert exc.value.status_code == 403

    def test_rule9_parent_without_link_rejected(self, service, stub_repos, session):
        _attendance_repo, schedule_repo, user_repo, *_ = stub_repos
        schedule_repo.get_class_session.return_value = make_class_session()
        user_repo.get_parent_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())
        user_repo.parent_has_linked_student.return_value = False
        parent_user = User(id=uuid.uuid4(), email="p@example.com", role="parent")

        with pytest.raises(HTTPException) as exc:
            service.get_class_attendance(
                session, parent_user, uuid.uuid4(), date_from=None, date_to=None, student_id=uuid.uuid4()
            )
        assert exc.value.status_code == 403

    def test_rule9_parent_with_link_succeeds(self, service, stub_repos, session):
        attendance_repo, schedule_repo, user_repo, *_ = stub_repos
        schedule_repo.get_class_session.return_value = make_class_session()
        user_repo.get_parent_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())
        user_repo.parent_has_linked_student.return_value = True
        attendance_repo.list_for_class_session.return_value = []
        parent_user = User(id=uuid.uuid4(), email="p@example.com", role="parent")

        result = service.get_class_attendance(
            session, parent_user, uuid.uuid4(), date_from=None, date_to=None, student_id=uuid.uuid4()
        )
        assert result.records == []


class TestGetMe:
    def test_computes_percentage_excluding_excused(self, service, stub_repos, session):
        attendance_repo, _schedule_repo, user_repo, *_ = stub_repos
        student = MagicMock(id=uuid.uuid4())
        user_repo.get_student_profile_by_user_id.return_value = student

        course = MagicMock()
        course.name = "Intro to CS"
        class_session_id = uuid.uuid4()
        records = [
            MagicMock(class_session_id=class_session_id, attendance_date=date(2026, 1, 1), status="present"),
            MagicMock(class_session_id=class_session_id, attendance_date=date(2026, 1, 2), status="absent"),
            MagicMock(class_session_id=class_session_id, attendance_date=date(2026, 1, 3), status="excused"),
        ]
        attendance_repo.list_for_student.return_value = [(r, course) for r in records]

        result = service.get_me(session, MagicMock(id=uuid.uuid4()), AttendanceMeQuery())

        # 1 present out of 2 countable (excused excluded) = 50%, below 80%.
        assert result.overall_percentage == 50.0
        assert result.low_attendance_warning is True

    def test_no_records_yields_100_percent_no_warning(self, service, stub_repos, session):
        attendance_repo, _schedule_repo, user_repo, *_ = stub_repos
        user_repo.get_student_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())
        attendance_repo.list_for_student.return_value = []

        result = service.get_me(session, MagicMock(id=uuid.uuid4()), AttendanceMeQuery())

        assert result.overall_percentage == 100.0
        assert result.low_attendance_warning is False


class TestAttendanceMeQueryValidation:
    def test_date_from_after_date_to_rejected(self):
        with pytest.raises(ValueError):
            AttendanceMeQuery(date_from=date(2026, 2, 1), date_to=date(2026, 1, 1))


class TestGetReports:
    """Final-polish fix: GET /attendance/reports must return a display
    name per student, resolved via a single batch lookup (not one query
    per student — CLAUDE.md §11's N+1 guidance)."""

    def test_report_entries_include_student_name_via_single_batch_lookup(self, service, stub_repos, session):
        attendance_repo, _schedule_repo, user_repo, *_ = stub_repos
        student = Student(id=uuid.uuid4(), user_id=uuid.uuid4(), department_id=uuid.uuid4(), first_name="Sam", last_name="Student")
        attendance_repo.list_for_report.return_value = [
            AttendanceRecord(
                id=uuid.uuid4(), student_id=student.id, class_session_id=uuid.uuid4(),
                marked_by_teacher_id=uuid.uuid4(), attendance_date=date(2026, 1, 5), status="present",
            )
        ]
        user_repo.list_students_by_ids.return_value = [student]

        result = service.get_reports(session, None, None)

        assert result.summary[0].student_name == "Sam Student"
        user_repo.list_students_by_ids.assert_called_once()

    def test_unknown_student_falls_back_to_placeholder_name(self, service, stub_repos, session):
        attendance_repo, _schedule_repo, user_repo, *_ = stub_repos
        attendance_repo.list_for_report.return_value = [
            AttendanceRecord(
                id=uuid.uuid4(), student_id=uuid.uuid4(), class_session_id=uuid.uuid4(),
                marked_by_teacher_id=uuid.uuid4(), attendance_date=date(2026, 1, 5), status="present",
            )
        ]
        user_repo.list_students_by_ids.return_value = []

        result = service.get_reports(session, None, None)

        assert result.summary[0].student_name == "Unknown Student"
