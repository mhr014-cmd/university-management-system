"""
Unit tests: app.services.grading_service.GradingService.

Repositories are stubbed (per CLAUDE.md §10) so these tests exercise
VR-006, the grading re-save/idempotency policy, and the Derived
GET /exams/{id}/submissions/{submission_id} endpoint's ownership rules
directly, without a database.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models.answer import Answer
from app.models.exam import Exam
from app.models.exam_submission import ExamSubmission
from app.models.question import Question
from app.models.question_grade import QuestionGrade
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.user import User
from app.schemas.grading import ExamGradeRequest, GradeInput
from app.services import grading_service as grading_service_module
from app.services.grading_service import GradingService


def make_exam(**overrides) -> Exam:
    defaults = dict(
        id=uuid.uuid4(),
        class_session_id=uuid.uuid4(),
        created_by_teacher_id=uuid.uuid4(),
        title="Midterm",
        exam_type="mcq",
        time_limit_minutes=30,
        status="closed",
        scheduled_at=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return Exam(**defaults)


def make_teacher(**overrides) -> Teacher:
    defaults = dict(id=uuid.uuid4(), user_id=uuid.uuid4(), department_id=uuid.uuid4(), first_name="T", last_name="Teacher")
    defaults.update(overrides)
    return Teacher(**defaults)


def make_submission(**overrides) -> ExamSubmission:
    defaults = dict(
        id=uuid.uuid4(),
        exam_id=uuid.uuid4(),
        student_id=uuid.uuid4(),
        submitted_at=datetime.now(timezone.utc),
        started_at=datetime.now(timezone.utc),
        status="submitted",
    )
    defaults.update(overrides)
    return ExamSubmission(**defaults)


def make_answer(**overrides) -> Answer:
    defaults = dict(id=uuid.uuid4(), submission_id=uuid.uuid4(), question_id=uuid.uuid4(), answer_text="my answer", selected_option_id=None)
    defaults.update(overrides)
    return Answer(**defaults)


def make_question(**overrides) -> Question:
    defaults = dict(
        id=uuid.uuid4(), exam_id=uuid.uuid4(), question_text="Q1", question_type="short_answer", marks=10, hint=None, order_index=0
    )
    defaults.update(overrides)
    return Question(**defaults)


def make_grade(**overrides) -> QuestionGrade:
    defaults = dict(
        id=uuid.uuid4(), answer_id=uuid.uuid4(), graded_by_teacher_id=uuid.uuid4(), awarded_marks=5, feedback="ok",
        graded_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return QuestionGrade(**defaults)


@pytest.fixture
def stub_repos(monkeypatch):
    exam_repo = MagicMock()
    user_repo = MagicMock()
    monkeypatch.setattr(grading_service_module, "exam_repo", exam_repo)
    monkeypatch.setattr(grading_service_module, "user_repo", user_repo)
    return exam_repo, user_repo


@pytest.fixture
def service():
    return GradingService()


@pytest.fixture
def session():
    return MagicMock()


def _teacher_user():
    return User(id=uuid.uuid4(), email="t@example.com", role="teacher")


def _admin_user():
    return User(id=uuid.uuid4(), email="a@example.com", role="admin")


class TestGradeSubmission:
    def test_exam_not_found_raises_404(self, service, stub_repos, session):
        exam_repo, *_ = stub_repos
        exam_repo.get_exam.return_value = None
        payload = ExamGradeRequest(submission_id=uuid.uuid4(), grades=[GradeInput(answer_id=uuid.uuid4(), awarded_marks=1)])
        with pytest.raises(HTTPException) as exc:
            service.grade_submission(session, _teacher_user(), uuid.uuid4(), payload)
        assert exc.value.status_code == 404

    def test_non_creator_teacher_forbidden(self, service, stub_repos, session):
        exam_repo, user_repo = stub_repos
        exam_repo.get_exam.return_value = make_exam(created_by_teacher_id=uuid.uuid4())
        user_repo.get_teacher_profile_by_user_id.return_value = make_teacher()
        payload = ExamGradeRequest(submission_id=uuid.uuid4(), grades=[GradeInput(answer_id=uuid.uuid4(), awarded_marks=1)])
        with pytest.raises(HTTPException) as exc:
            service.grade_submission(session, _teacher_user(), uuid.uuid4(), payload)
        assert exc.value.status_code == 403

    def test_submission_not_submitted_yet_rejected(self, service, stub_repos, session):
        exam_repo, user_repo = stub_repos
        teacher = make_teacher()
        exam = make_exam(created_by_teacher_id=teacher.id)
        exam_repo.get_exam.return_value = exam
        user_repo.get_teacher_profile_by_user_id.return_value = teacher
        exam_repo.get_submission.return_value = make_submission(exam_id=exam.id, status="in_progress")

        payload = ExamGradeRequest(submission_id=uuid.uuid4(), grades=[GradeInput(answer_id=uuid.uuid4(), awarded_marks=1)])
        with pytest.raises(HTTPException) as exc:
            service.grade_submission(session, _teacher_user(), exam.id, payload)
        assert exc.value.status_code == 409

    def test_submission_belonging_to_different_exam_not_found(self, service, stub_repos, session):
        exam_repo, user_repo = stub_repos
        teacher = make_teacher()
        exam = make_exam(created_by_teacher_id=teacher.id)
        exam_repo.get_exam.return_value = exam
        user_repo.get_teacher_profile_by_user_id.return_value = teacher
        exam_repo.get_submission.return_value = make_submission(exam_id=uuid.uuid4(), status="submitted")

        payload = ExamGradeRequest(submission_id=uuid.uuid4(), grades=[GradeInput(answer_id=uuid.uuid4(), awarded_marks=1)])
        with pytest.raises(HTTPException) as exc:
            service.grade_submission(session, _teacher_user(), exam.id, payload)
        assert exc.value.status_code == 404

    def test_vr006_awarded_marks_exceeding_question_max_rejected(self, service, stub_repos, session):
        exam_repo, user_repo = stub_repos
        teacher = make_teacher()
        exam = make_exam(created_by_teacher_id=teacher.id)
        exam_repo.get_exam.return_value = exam
        user_repo.get_teacher_profile_by_user_id.return_value = teacher
        submission = make_submission(exam_id=exam.id, status="submitted")
        exam_repo.get_submission.return_value = submission
        answer = make_answer(submission_id=submission.id)
        exam_repo.get_answer.return_value = answer
        exam_repo.get_question.return_value = make_question(marks=5)

        payload = ExamGradeRequest(submission_id=submission.id, grades=[GradeInput(answer_id=answer.id, awarded_marks=10)])
        with pytest.raises(HTTPException) as exc:
            service.grade_submission(session, _teacher_user(), exam.id, payload)
        assert exc.value.status_code == 422
        exam_repo.create_question_grade.assert_not_called()

    def test_all_grades_validated_before_any_write(self, service, stub_repos, session):
        # Batch of two grades: first valid, second exceeds max marks.
        # Neither should be written.
        exam_repo, user_repo = stub_repos
        teacher = make_teacher()
        exam = make_exam(created_by_teacher_id=teacher.id)
        exam_repo.get_exam.return_value = exam
        user_repo.get_teacher_profile_by_user_id.return_value = teacher
        submission = make_submission(exam_id=exam.id, status="submitted")
        exam_repo.get_submission.return_value = submission
        answer_a = make_answer(submission_id=submission.id)
        answer_b = make_answer(submission_id=submission.id)

        def get_answer_side_effect(_session, answer_id):
            return answer_a if answer_id == answer_a.id else answer_b

        exam_repo.get_answer.side_effect = get_answer_side_effect
        exam_repo.get_question.return_value = make_question(marks=5)

        payload = ExamGradeRequest(
            submission_id=submission.id,
            grades=[
                GradeInput(answer_id=answer_a.id, awarded_marks=5),
                GradeInput(answer_id=answer_b.id, awarded_marks=99),
            ],
        )
        with pytest.raises(HTTPException) as exc:
            service.grade_submission(session, _teacher_user(), exam.id, payload)
        assert exc.value.status_code == 422
        exam_repo.create_question_grade.assert_not_called()
        exam_repo.update_question_grade.assert_not_called()

    def test_regrade_upserts_existing_grade(self, service, stub_repos, session):
        exam_repo, user_repo = stub_repos
        teacher = make_teacher()
        exam = make_exam(created_by_teacher_id=teacher.id)
        exam_repo.get_exam.return_value = exam
        user_repo.get_teacher_profile_by_user_id.return_value = teacher
        submission = make_submission(exam_id=exam.id, status="graded")
        exam_repo.get_submission.return_value = submission
        answer = make_answer(submission_id=submission.id)
        exam_repo.get_answer.return_value = answer
        exam_repo.get_question.return_value = make_question(marks=10)
        existing_grade = make_grade(answer_id=answer.id, awarded_marks=5)
        exam_repo.get_grade_for_answer.return_value = existing_grade
        exam_repo.list_answers_for_submission.return_value = [answer]
        exam_repo.list_grades_for_submission.return_value = [existing_grade]

        payload = ExamGradeRequest(submission_id=submission.id, grades=[GradeInput(answer_id=answer.id, awarded_marks=8)])
        service.grade_submission(session, _teacher_user(), exam.id, payload)
        exam_repo.update_question_grade.assert_called_once()
        exam_repo.create_question_grade.assert_not_called()

    def test_status_becomes_graded_only_once_every_answer_graded(self, service, stub_repos, session):
        exam_repo, user_repo = stub_repos
        teacher = make_teacher()
        exam = make_exam(created_by_teacher_id=teacher.id)
        exam_repo.get_exam.return_value = exam
        user_repo.get_teacher_profile_by_user_id.return_value = teacher
        submission = make_submission(exam_id=exam.id, status="submitted")
        exam_repo.get_submission.return_value = submission
        answer_a = make_answer(submission_id=submission.id)
        answer_b = make_answer(submission_id=submission.id)
        exam_repo.get_answer.return_value = answer_a
        exam_repo.get_question.return_value = make_question(marks=10)
        exam_repo.get_grade_for_answer.return_value = None
        # Two answers exist for this submission but only one is graded here.
        exam_repo.list_answers_for_submission.return_value = [answer_a, answer_b]
        exam_repo.list_grades_for_submission.return_value = [make_grade(answer_id=answer_a.id)]

        payload = ExamGradeRequest(submission_id=submission.id, grades=[GradeInput(answer_id=answer_a.id, awarded_marks=8)])
        service.grade_submission(session, _teacher_user(), exam.id, payload)
        exam_repo.mark_graded.assert_not_called()

    def test_status_becomes_graded_when_all_answers_graded(self, service, stub_repos, session):
        exam_repo, user_repo = stub_repos
        teacher = make_teacher()
        exam = make_exam(created_by_teacher_id=teacher.id)
        exam_repo.get_exam.return_value = exam
        user_repo.get_teacher_profile_by_user_id.return_value = teacher
        submission = make_submission(exam_id=exam.id, status="submitted")
        exam_repo.get_submission.return_value = submission
        answer = make_answer(submission_id=submission.id)
        exam_repo.get_answer.return_value = answer
        exam_repo.get_question.return_value = make_question(marks=10)
        exam_repo.get_grade_for_answer.return_value = None
        grade = make_grade(answer_id=answer.id, awarded_marks=8)
        exam_repo.list_answers_for_submission.return_value = [answer]
        exam_repo.list_grades_for_submission.return_value = [grade]

        payload = ExamGradeRequest(submission_id=submission.id, grades=[GradeInput(answer_id=answer.id, awarded_marks=8)])
        service.grade_submission(session, _teacher_user(), exam.id, payload)
        exam_repo.mark_graded.assert_called_once()


class TestGetSubmissionDetail:
    def test_exam_not_found_raises_404(self, service, stub_repos, session):
        exam_repo, *_ = stub_repos
        exam_repo.get_exam.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.get_submission_detail(session, _teacher_user(), uuid.uuid4(), uuid.uuid4())
        assert exc.value.status_code == 404

    def test_non_creator_teacher_forbidden(self, service, stub_repos, session):
        exam_repo, user_repo = stub_repos
        exam_repo.get_exam.return_value = make_exam(created_by_teacher_id=uuid.uuid4())
        user_repo.get_teacher_profile_by_user_id.return_value = make_teacher()
        with pytest.raises(HTTPException) as exc:
            service.get_submission_detail(session, _teacher_user(), uuid.uuid4(), uuid.uuid4())
        assert exc.value.status_code == 403

    def test_non_teacher_non_admin_forbidden(self, service, stub_repos, session):
        exam_repo, *_ = stub_repos
        exam_repo.get_exam.return_value = make_exam()
        student_user = User(id=uuid.uuid4(), email="s@example.com", role="student")
        with pytest.raises(HTTPException) as exc:
            service.get_submission_detail(session, student_user, uuid.uuid4(), uuid.uuid4())
        assert exc.value.status_code == 403

    def test_submission_not_found_raises_404(self, service, stub_repos, session):
        exam_repo, *_ = stub_repos
        exam_repo.get_exam.return_value = make_exam()
        exam_repo.get_submission.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.get_submission_detail(session, _admin_user(), uuid.uuid4(), uuid.uuid4())
        assert exc.value.status_code == 404

    def test_submission_belonging_to_different_exam_not_found(self, service, stub_repos, session):
        exam_repo, *_ = stub_repos
        exam = make_exam()
        exam_repo.get_exam.return_value = exam
        exam_repo.get_submission.return_value = make_submission(exam_id=uuid.uuid4())
        with pytest.raises(HTTPException) as exc:
            service.get_submission_detail(session, _admin_user(), exam.id, uuid.uuid4())
        assert exc.value.status_code == 404

    def test_admin_allowed_regardless_of_creator(self, service, stub_repos, session):
        exam_repo, *_ = stub_repos
        exam = make_exam()
        exam_repo.get_exam.return_value = exam
        submission = make_submission(exam_id=exam.id)
        exam_repo.get_submission.return_value = submission
        exam_repo.list_questions_for_exam.return_value = []
        exam_repo.list_answers_for_submission.return_value = []
        exam_repo.list_grades_for_submission.return_value = []

        result = service.get_submission_detail(session, _admin_user(), exam.id, submission.id)
        assert result.submission_id == submission.id
        assert result.questions == []

    def test_questions_returned_in_order_with_answers_and_grades(self, service, stub_repos, session):
        exam_repo, user_repo = stub_repos
        teacher = make_teacher()
        exam = make_exam(created_by_teacher_id=teacher.id)
        exam_repo.get_exam.return_value = exam
        user_repo.get_teacher_profile_by_user_id.return_value = teacher
        submission = make_submission(exam_id=exam.id)
        exam_repo.get_submission.return_value = submission

        q1 = make_question(exam_id=exam.id, order_index=0)
        q2 = make_question(exam_id=exam.id, order_index=1)
        exam_repo.list_questions_for_exam.return_value = [q1, q2]

        answer_q1 = make_answer(submission_id=submission.id, question_id=q1.id, answer_text="answer 1")
        # q2 deliberately left unanswered — no Answer row.
        exam_repo.list_answers_for_submission.return_value = [answer_q1]

        grade_q1 = make_grade(answer_id=answer_q1.id, awarded_marks=7, feedback="good")
        exam_repo.list_grades_for_submission.return_value = [grade_q1]

        result = service.get_submission_detail(session, _teacher_user(), exam.id, submission.id)
        assert [q.question_id for q in result.questions] == [q1.id, q2.id]
        assert result.questions[0].answer_id == answer_q1.id
        assert result.questions[0].answer_text == "answer 1"
        assert result.questions[0].awarded_marks == 7.0
        assert result.questions[0].feedback == "good"
        assert result.questions[1].answer_id is None
        assert result.questions[1].awarded_marks is None


class TestGetResults:
    """Final-polish fix: GET /exams/{id}/results must return a
    student_name per submission, resolved via a single batch lookup (not
    one query per submission — CLAUDE.md §11's N+1 guidance)."""

    def test_summaries_include_student_name_via_single_batch_lookup(self, service, stub_repos, session):
        exam_repo, user_repo = stub_repos
        exam = make_exam()
        exam_repo.get_exam.return_value = exam
        student = Student(id=uuid.uuid4(), user_id=uuid.uuid4(), department_id=uuid.uuid4(), first_name="Sam", last_name="Student")
        submission = make_submission(exam_id=exam.id, student_id=student.id, status="graded")
        exam_repo.list_submissions_for_exam.return_value = [submission]
        exam_repo.list_grades_for_submission.return_value = []
        user_repo.list_students_by_ids.return_value = [student]

        result = service.get_results(session, _admin_user(), exam.id)

        assert result.submissions[0].student_name == "Sam Student"
        user_repo.list_students_by_ids.assert_called_once()

    def test_unknown_student_falls_back_to_placeholder_name(self, service, stub_repos, session):
        exam_repo, user_repo = stub_repos
        exam = make_exam()
        exam_repo.get_exam.return_value = exam
        submission = make_submission(exam_id=exam.id, status="graded")
        exam_repo.list_submissions_for_exam.return_value = [submission]
        exam_repo.list_grades_for_submission.return_value = []
        user_repo.list_students_by_ids.return_value = []

        result = service.get_results(session, _admin_user(), exam.id)

        assert result.submissions[0].student_name == "Unknown Student"
