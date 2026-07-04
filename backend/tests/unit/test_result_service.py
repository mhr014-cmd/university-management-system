"""
Unit tests: app.services.result_service.ResultService.

Repositories are stubbed (per CLAUDE.md §10) so these tests exercise the
Milestone 7 mandatory Results & Academic Records Domain Rules directly,
without a database:
  1. Student exists and is active
  2. Student has a valid enrollment
  3. Referenced exam exists
  4. Exam is published before contributing to Results
  5. Grading is complete before Results are calculated
  6. QuestionGrade/submission belongs to the correct exam and student
  7. Duplicate-prevention, with the resubmission-after-reject exception
  8. GPA follows only the documented credit-hour-weighted formula
  9-10. Read-only access to exam/submission/answer/question_grade data
  11-14. RBAC/ownership for Student/Parent/Teacher/Admin
  15. All validation before any write (two-pass batch)
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models.course import Course
from app.models.exam import Exam
from app.models.exam_submission import ExamSubmission
from app.models.result import Result
from app.models.semester import Semester
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.user import User
from app.schemas.result import ResultApprovalRequest, ResultSubmitEntry, ResultSubmitRequest
from app.services import result_service as result_service_module
from app.services.result_service import ResultService


def make_exam(**overrides) -> Exam:
    defaults = dict(
        id=uuid.uuid4(),
        class_session_id=uuid.uuid4(),
        created_by_teacher_id=uuid.uuid4(),
        title="Final",
        exam_type="mcq",
        time_limit_minutes=30,
        status="published",
        scheduled_at=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return Exam(**defaults)


def make_class_session(**overrides):
    defaults = dict(course_id=uuid.uuid4(), semester_id=uuid.uuid4(), teacher_id=uuid.uuid4())
    defaults.update(overrides)
    return MagicMock(**defaults)


def make_teacher(**overrides) -> Teacher:
    defaults = dict(id=uuid.uuid4(), user_id=uuid.uuid4(), department_id=uuid.uuid4(), first_name="T", last_name="Teacher")
    defaults.update(overrides)
    return Teacher(**defaults)


def make_student(**overrides) -> Student:
    defaults = dict(
        id=uuid.uuid4(), user_id=uuid.uuid4(), department_id=uuid.uuid4(), first_name="S", last_name="Student"
    )
    defaults.update(overrides)
    return Student(**defaults)


def make_submission(**overrides) -> ExamSubmission:
    defaults = dict(
        id=uuid.uuid4(), exam_id=uuid.uuid4(), student_id=uuid.uuid4(), submitted_at=datetime.now(timezone.utc),
        started_at=datetime.now(timezone.utc), status="graded",
    )
    defaults.update(overrides)
    return ExamSubmission(**defaults)


def make_result(**overrides) -> Result:
    defaults = dict(
        id=uuid.uuid4(), student_id=uuid.uuid4(), course_id=uuid.uuid4(), semester_id=uuid.uuid4(), exam_id=uuid.uuid4(),
        submitted_by_teacher_id=uuid.uuid4(), approved_by_admin_id=None, grade_letter="A", grade_point=4.0,
        status="submitted", submitted_at=datetime.now(timezone.utc), approved_at=None,
    )
    defaults.update(overrides)
    return Result(**defaults)


def make_course(**overrides) -> Course:
    defaults = dict(id=uuid.uuid4(), department_id=uuid.uuid4(), name="DB Systems", code="CS101", credit_hours=3)
    defaults.update(overrides)
    return Course(**defaults)


def make_semester(**overrides) -> Semester:
    from datetime import date

    defaults = dict(id=uuid.uuid4(), name="Spring 2026", start_date=date(2026, 1, 1), end_date=date(2026, 5, 1))
    defaults.update(overrides)
    return Semester(**defaults)


@pytest.fixture
def stub_repos(monkeypatch):
    result_repo = MagicMock()
    exam_repo = MagicMock()
    schedule_repo = MagicMock()
    user_repo = MagicMock()
    course_repo = MagicMock()
    semester_repo = MagicMock()
    monkeypatch.setattr(result_service_module, "result_repo", result_repo)
    monkeypatch.setattr(result_service_module, "exam_repo", exam_repo)
    monkeypatch.setattr(result_service_module, "schedule_repo", schedule_repo)
    monkeypatch.setattr(result_service_module, "user_repo", user_repo)
    monkeypatch.setattr(result_service_module, "course_repo", course_repo)
    monkeypatch.setattr(result_service_module, "semester_repo", semester_repo)
    return result_repo, exam_repo, schedule_repo, user_repo, course_repo, semester_repo


@pytest.fixture
def service():
    return ResultService()


@pytest.fixture
def session():
    return MagicMock()


def _teacher_user():
    return User(id=uuid.uuid4(), email="t@example.com", role="teacher")


def _student_user():
    return User(id=uuid.uuid4(), email="s@example.com", role="student")


def _parent_user():
    return User(id=uuid.uuid4(), email="p@example.com", role="parent")


def _admin_user():
    return User(id=uuid.uuid4(), email="a@example.com", role="admin")


class TestGetMyResults:
    def test_invalid_semester_id_rejected(self, service, stub_repos, session):
        _result_repo, _exam_repo, _schedule_repo, user_repo, _course_repo, semester_repo = stub_repos
        semester_repo.get.return_value = None
        user_repo.get_student_profile_by_user_id.return_value = make_student()

        with pytest.raises(HTTPException) as exc:
            service.get_my_results(session, _student_user(), semester_id=uuid.uuid4(), student_id=None)
        assert exc.value.status_code == 422

    def test_rule13_parent_missing_student_id_forbidden(self, service, stub_repos, session):
        _result_repo, _exam_repo, _schedule_repo, user_repo, *_ = stub_repos
        user_repo.get_parent_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())

        with pytest.raises(HTTPException) as exc:
            service.get_my_results(session, _parent_user(), semester_id=None, student_id=None)
        assert exc.value.status_code == 403

    def test_rule13_parent_unlinked_student_forbidden(self, service, stub_repos, session):
        _result_repo, _exam_repo, _schedule_repo, user_repo, *_ = stub_repos
        user_repo.get_parent_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())
        user_repo.parent_has_linked_student.return_value = False

        with pytest.raises(HTTPException) as exc:
            service.get_my_results(session, _parent_user(), semester_id=None, student_id=uuid.uuid4())
        assert exc.value.status_code == 403

    def test_rule13_parent_with_link_succeeds(self, service, stub_repos, session):
        result_repo, _exam_repo, _schedule_repo, user_repo, _course_repo, _semester_repo = stub_repos
        user_repo.get_parent_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())
        user_repo.parent_has_linked_student.return_value = True
        result_repo.list_for_student.return_value = []

        target_student_id = uuid.uuid4()
        response = service.get_my_results(session, _parent_user(), semester_id=None, student_id=target_student_id)
        assert response.student_id == target_student_id
        assert response.semesters == []

    def test_gpa_is_credit_weighted_average(self, service, stub_repos, session):
        result_repo, _exam_repo, _schedule_repo, user_repo, course_repo, semester_repo = stub_repos
        student = make_student()
        user_repo.get_student_profile_by_user_id.return_value = student
        semester = make_semester()
        course_a = make_course(credit_hours=3)
        course_b = make_course(credit_hours=1)
        result_a = make_result(student_id=student.id, course_id=course_a.id, semester_id=semester.id, grade_point=4.0, status="published")
        result_b = make_result(student_id=student.id, course_id=course_b.id, semester_id=semester.id, grade_point=2.0, status="published")
        result_repo.list_for_student.return_value = [result_a, result_b]
        semester_repo.get.return_value = semester

        def course_side_effect(_session, course_id):
            return course_a if course_id == course_a.id else course_b

        course_repo.get.side_effect = course_side_effect

        response = service.get_my_results(session, _student_user(), semester_id=None, student_id=None)
        # (4.0*3 + 2.0*1) / (3+1) = 14/4 = 3.5
        assert response.semesters[0].gpa == 3.5


class TestSubmitResults:
    def _base_setup(self, stub_repos, *, exam_status="published", teacher_owns=True, submissions=None):
        result_repo, exam_repo, schedule_repo, user_repo, _course_repo, _semester_repo = stub_repos
        teacher = make_teacher()
        user_repo.get_teacher_profile_by_user_id.return_value = teacher
        exam = make_exam(status=exam_status, created_by_teacher_id=teacher.id if teacher_owns else uuid.uuid4())
        exam_repo.get_exam.return_value = exam
        class_session = make_class_session()
        schedule_repo.get_class_session.return_value = class_session
        exam_repo.list_submissions_for_exam.return_value = submissions if submissions is not None else []
        return teacher, exam, class_session

    def test_exam_not_found_raises_404(self, service, stub_repos, session):
        _result_repo, exam_repo, *_ = stub_repos
        exam_repo.get_exam.return_value = None
        payload = ResultSubmitRequest(results=[ResultSubmitEntry(student_id=uuid.uuid4(), grade_letter="A", grade_point=4.0)])
        with pytest.raises(HTTPException) as exc:
            service.submit_results(session, _teacher_user(), uuid.uuid4(), payload)
        assert exc.value.status_code == 404

    def test_rule14_non_creator_teacher_forbidden(self, service, stub_repos, session):
        self._base_setup(stub_repos, teacher_owns=False)
        payload = ResultSubmitRequest(results=[ResultSubmitEntry(student_id=uuid.uuid4(), grade_letter="A", grade_point=4.0)])
        with pytest.raises(HTTPException) as exc:
            service.submit_results(session, _teacher_user(), uuid.uuid4(), payload)
        assert exc.value.status_code == 403

    def test_rule4_exam_not_published_rejected(self, service, stub_repos, session):
        _teacher, exam, _cs = self._base_setup(stub_repos, exam_status="closed")
        payload = ResultSubmitRequest(results=[ResultSubmitEntry(student_id=uuid.uuid4(), grade_letter="A", grade_point=4.0)])
        with pytest.raises(HTTPException) as exc:
            service.submit_results(session, _teacher_user(), exam.id, payload)
        assert exc.value.status_code == 409

    def test_rule5_exam_not_fully_graded_rejected(self, service, stub_repos, session):
        submission = make_submission(status="submitted")
        _teacher, exam, _cs = self._base_setup(stub_repos, submissions=[submission])
        payload = ResultSubmitRequest(results=[ResultSubmitEntry(student_id=uuid.uuid4(), grade_letter="A", grade_point=4.0)])
        with pytest.raises(HTTPException) as exc:
            service.submit_results(session, _teacher_user(), exam.id, payload)
        assert exc.value.status_code == 409

    def test_rule1_inactive_student_rejected(self, service, stub_repos, session):
        result_repo, exam_repo, schedule_repo, user_repo, *_ = stub_repos
        student = make_student()
        submission = make_submission(student_id=student.id, status="graded")
        _teacher, exam, _cs = self._base_setup(stub_repos, submissions=[submission])
        inactive_user = User(id=uuid.uuid4(), email="s@example.com", role="student", is_active=False)
        user_repo.get_student_with_user.return_value = (student, inactive_user)

        payload = ResultSubmitRequest(results=[ResultSubmitEntry(student_id=student.id, grade_letter="A", grade_point=4.0)])
        with pytest.raises(HTTPException) as exc:
            service.submit_results(session, _teacher_user(), exam.id, payload)
        assert exc.value.status_code == 422
        result_repo.create.assert_not_called()

    def test_rule2_student_not_enrolled_rejected(self, service, stub_repos, session):
        result_repo, exam_repo, schedule_repo, user_repo, *_ = stub_repos
        student = make_student()
        submission = make_submission(student_id=student.id, status="graded")
        _teacher, exam, _cs = self._base_setup(stub_repos, submissions=[submission])
        active_user = User(id=uuid.uuid4(), email="s@example.com", role="student", is_active=True)
        user_repo.get_student_with_user.return_value = (student, active_user)
        schedule_repo.get_enrollment.return_value = None

        payload = ResultSubmitRequest(results=[ResultSubmitEntry(student_id=student.id, grade_letter="A", grade_point=4.0)])
        with pytest.raises(HTTPException) as exc:
            service.submit_results(session, _teacher_user(), exam.id, payload)
        assert exc.value.status_code == 422
        result_repo.create.assert_not_called()

    def test_rule6_student_never_graded_on_exam_rejected(self, service, stub_repos, session):
        result_repo, exam_repo, schedule_repo, user_repo, *_ = stub_repos
        student = make_student()
        other_submission = make_submission(student_id=uuid.uuid4(), status="graded")
        _teacher, exam, _cs = self._base_setup(stub_repos, submissions=[other_submission])
        active_user = User(id=uuid.uuid4(), email="s@example.com", role="student", is_active=True)
        user_repo.get_student_with_user.return_value = (student, active_user)
        schedule_repo.get_enrollment.return_value = MagicMock()

        payload = ResultSubmitRequest(results=[ResultSubmitEntry(student_id=student.id, grade_letter="A", grade_point=4.0)])
        with pytest.raises(HTTPException) as exc:
            service.submit_results(session, _teacher_user(), exam.id, payload)
        assert exc.value.status_code == 422
        result_repo.create.assert_not_called()

    def test_rule7_duplicate_submitted_result_rejected(self, service, stub_repos, session):
        result_repo, exam_repo, schedule_repo, user_repo, *_ = stub_repos
        student = make_student()
        submission = make_submission(student_id=student.id, status="graded")
        _teacher, exam, _cs = self._base_setup(stub_repos, submissions=[submission])
        active_user = User(id=uuid.uuid4(), email="s@example.com", role="student", is_active=True)
        user_repo.get_student_with_user.return_value = (student, active_user)
        schedule_repo.get_enrollment.return_value = MagicMock()
        result_repo.get_by_student_course_semester.return_value = make_result(status="submitted")

        payload = ResultSubmitRequest(results=[ResultSubmitEntry(student_id=student.id, grade_letter="A", grade_point=4.0)])
        with pytest.raises(HTTPException) as exc:
            service.submit_results(session, _teacher_user(), exam.id, payload)
        assert exc.value.status_code == 409
        result_repo.create.assert_not_called()

    def test_rejected_result_is_resubmitted_in_place(self, service, stub_repos, session):
        result_repo, exam_repo, schedule_repo, user_repo, *_ = stub_repos
        student = make_student()
        submission = make_submission(student_id=student.id, status="graded")
        teacher, exam, _cs = self._base_setup(stub_repos, submissions=[submission])
        active_user = User(id=uuid.uuid4(), email="s@example.com", role="student", is_active=True)
        user_repo.get_student_with_user.return_value = (student, active_user)
        schedule_repo.get_enrollment.return_value = MagicMock()
        existing = make_result(student_id=student.id, status="rejected")
        result_repo.get_by_student_course_semester.return_value = existing

        payload = ResultSubmitRequest(results=[ResultSubmitEntry(student_id=student.id, grade_letter="B", grade_point=3.0)])
        service.submit_results(session, _teacher_user(), exam.id, payload)
        result_repo.update_for_resubmission.assert_called_once()
        result_repo.create.assert_not_called()
        session.commit.assert_called_once()

    def test_rule15_batch_validated_before_any_write(self, service, stub_repos, session):
        # Two students: first valid, second not enrolled. Neither should
        # be written.
        result_repo, exam_repo, schedule_repo, user_repo, *_ = stub_repos
        student_a = make_student()
        student_b = make_student()
        submission_a = make_submission(student_id=student_a.id, status="graded")
        submission_b = make_submission(student_id=student_b.id, status="graded")
        _teacher, exam, _cs = self._base_setup(stub_repos, submissions=[submission_a, submission_b])
        active_user_a = User(id=uuid.uuid4(), email="a@example.com", role="student", is_active=True)
        active_user_b = User(id=uuid.uuid4(), email="b@example.com", role="student", is_active=True)

        def get_student_with_user_side_effect(_session, student_id):
            if student_id == student_a.id:
                return (student_a, active_user_a)
            return (student_b, active_user_b)

        user_repo.get_student_with_user.side_effect = get_student_with_user_side_effect

        def get_enrollment_side_effect(_session, student_id, _class_session_id):
            return MagicMock() if student_id == student_a.id else None

        schedule_repo.get_enrollment.side_effect = get_enrollment_side_effect
        result_repo.get_by_student_course_semester.return_value = None

        payload = ResultSubmitRequest(
            results=[
                ResultSubmitEntry(student_id=student_a.id, grade_letter="A", grade_point=4.0),
                ResultSubmitEntry(student_id=student_b.id, grade_letter="B", grade_point=3.0),
            ]
        )
        with pytest.raises(HTTPException) as exc:
            service.submit_results(session, _teacher_user(), exam.id, payload)
        assert exc.value.status_code == 422
        result_repo.create.assert_not_called()
        session.commit.assert_not_called()

    def test_success_creates_new_result(self, service, stub_repos, session):
        result_repo, exam_repo, schedule_repo, user_repo, *_ = stub_repos
        student = make_student()
        submission = make_submission(student_id=student.id, status="graded")
        _teacher, exam, _cs = self._base_setup(stub_repos, submissions=[submission])
        active_user = User(id=uuid.uuid4(), email="s@example.com", role="student", is_active=True)
        user_repo.get_student_with_user.return_value = (student, active_user)
        schedule_repo.get_enrollment.return_value = MagicMock()
        result_repo.get_by_student_course_semester.return_value = None

        payload = ResultSubmitRequest(results=[ResultSubmitEntry(student_id=student.id, grade_letter="A", grade_point=4.0)])
        response = service.submit_results(session, _teacher_user(), exam.id, payload)
        assert response.status == "submitted"
        result_repo.create.assert_called_once()
        session.commit.assert_called_once()


class TestApproveOrReject:
    def test_not_found_raises_404(self, service, stub_repos, session):
        result_repo, *_ = stub_repos
        result_repo.get.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.approve_or_reject(session, _admin_user(), uuid.uuid4(), ResultApprovalRequest(decision="approve"))
        assert exc.value.status_code == 404

    def test_not_submitted_status_rejected(self, service, stub_repos, session):
        result_repo, *_ = stub_repos
        result_repo.get.return_value = make_result(status="published")
        with pytest.raises(HTTPException) as exc:
            service.approve_or_reject(session, _admin_user(), uuid.uuid4(), ResultApprovalRequest(decision="approve"))
        assert exc.value.status_code == 409

    def test_reject_without_comment_rejected(self, service, stub_repos, session):
        result_repo, *_ = stub_repos
        result_repo.get.return_value = make_result(status="submitted")
        with pytest.raises(HTTPException) as exc:
            service.approve_or_reject(session, _admin_user(), uuid.uuid4(), ResultApprovalRequest(decision="reject"))
        assert exc.value.status_code == 422
        result_repo.mark_rejected.assert_not_called()

    def test_approve_success(self, service, stub_repos, session):
        result_repo, _exam_repo, _schedule_repo, user_repo, *_ = stub_repos
        result = make_result(status="submitted")
        result_repo.get.return_value = result
        user_repo.get_admin_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())

        def mark_approved_side_effect(_session, r, *, admin_id, approved_at):
            r.status = "published"
            r.approved_at = approved_at

        result_repo.mark_approved.side_effect = mark_approved_side_effect

        response = service.approve_or_reject(session, _admin_user(), result.id, ResultApprovalRequest(decision="approve"))
        assert response.status == "published"
        session.commit.assert_called_once()

    def test_reject_with_comment_success(self, service, stub_repos, session):
        result_repo, _exam_repo, _schedule_repo, user_repo, *_ = stub_repos
        result = make_result(status="submitted")
        result_repo.get.return_value = result
        user_repo.get_admin_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())

        def mark_rejected_side_effect(_session, r, *, admin_id, approved_at):
            r.status = "rejected"
            r.approved_at = approved_at

        result_repo.mark_rejected.side_effect = mark_rejected_side_effect

        response = service.approve_or_reject(
            session, _admin_user(), result.id, ResultApprovalRequest(decision="reject", comment="Incorrect marks")
        )
        assert response.status == "rejected"


class TestGetTranscriptData:
    def test_student_not_found_raises_404(self, service, stub_repos, session):
        _result_repo, _exam_repo, _schedule_repo, user_repo, *_ = stub_repos
        user_repo.get_student_with_user.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.get_transcript_data(session, _admin_user(), uuid.uuid4())
        assert exc.value.status_code == 404

    def test_inactive_student_raises_404(self, service, stub_repos, session):
        _result_repo, _exam_repo, _schedule_repo, user_repo, *_ = stub_repos
        student = make_student()
        inactive_user = User(id=uuid.uuid4(), email="s@example.com", role="student", is_active=False)
        user_repo.get_student_with_user.return_value = (student, inactive_user)
        with pytest.raises(HTTPException) as exc:
            service.get_transcript_data(session, _admin_user(), student.id)
        assert exc.value.status_code == 404

    def test_student_cannot_download_other_students_transcript(self, service, stub_repos, session):
        _result_repo, _exam_repo, _schedule_repo, user_repo, *_ = stub_repos
        target_student = make_student()
        active_user = User(id=uuid.uuid4(), email="s@example.com", role="student", is_active=True)
        user_repo.get_student_with_user.return_value = (target_student, active_user)
        user_repo.get_student_profile_by_user_id.return_value = make_student()  # different id

        with pytest.raises(HTTPException) as exc:
            service.get_transcript_data(session, _student_user(), target_student.id)
        assert exc.value.status_code == 403

    def test_admin_can_download_any_transcript(self, service, stub_repos, session):
        result_repo, _exam_repo, _schedule_repo, user_repo, *_ = stub_repos
        target_student = make_student()
        active_user = User(id=uuid.uuid4(), email="s@example.com", role="student", is_active=True)
        user_repo.get_student_with_user.return_value = (target_student, active_user)
        result_repo.list_for_student.return_value = []

        student_name, semesters = service.get_transcript_data(session, _admin_user(), target_student.id)
        assert student_name == "S Student"
        assert semesters == []
