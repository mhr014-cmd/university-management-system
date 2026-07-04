"""
Unit tests: app.services.exam_service.ExamService.

Repositories are stubbed (per CLAUDE.md §10) so these tests exercise the
Milestone 6 mandatory Examination Domain Rules, BR-001, BR-003, VR-003,
VR-004 directly, without a database:
  1. Exam existence checks (404)
  2. Class session existence (N/A here — see module docstring)
  5. Student enrollment required to start/submit
  6. Only the assigned Teacher may create an exam for their class session
  9. No exam uniqueness constraint (module docstring note — not re-tested)
  11. VR-003 (marks > 0, enforced by the Pydantic schema, not re-tested here)
  12. All validation before any database write
- BR-001: correct-answer/grading data hidden from Students pre-publish
- BR-003: published exams are immutable; status only moves forward
- VR-004: server-side time-limit enforcement using the stored started_at
- Derived POST /exams/{id}/start: idempotent, server-clock-only, immutable
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models.exam import Exam
from app.models.exam_submission import ExamSubmission
from app.models.question import Question
from app.models.question_option import QuestionOption
from app.models.teacher import Teacher
from app.models.user import User
from app.schemas.exam import ExamCreate, ExamUpdate, QuestionCreate, QuestionOptionCreate
from app.schemas.submission import AnswerInput, ExamSubmitRequest
from app.services import exam_service as exam_service_module
from app.services.exam_service import ExamService


def make_exam(**overrides) -> Exam:
    defaults = dict(
        id=uuid.uuid4(),
        class_session_id=uuid.uuid4(),
        created_by_teacher_id=uuid.uuid4(),
        title="Midterm",
        exam_type="mcq",
        time_limit_minutes=30,
        status="draft",
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


def make_question(**overrides) -> Question:
    defaults = dict(
        id=uuid.uuid4(), exam_id=uuid.uuid4(), question_text="Q1", question_type="mcq", marks=5, hint=None, order_index=0
    )
    defaults.update(overrides)
    return Question(**defaults)


def make_submission(**overrides) -> ExamSubmission:
    defaults = dict(
        id=uuid.uuid4(),
        exam_id=uuid.uuid4(),
        student_id=uuid.uuid4(),
        submitted_at=None,
        started_at=datetime.now(timezone.utc),
        status="in_progress",
    )
    defaults.update(overrides)
    return ExamSubmission(**defaults)


@pytest.fixture
def stub_repos(monkeypatch):
    exam_repo = MagicMock()
    schedule_repo = MagicMock()
    user_repo = MagicMock()
    monkeypatch.setattr(exam_service_module, "exam_repo", exam_repo)
    monkeypatch.setattr(exam_service_module, "schedule_repo", schedule_repo)
    monkeypatch.setattr(exam_service_module, "user_repo", user_repo)
    return exam_repo, schedule_repo, user_repo


@pytest.fixture
def service():
    return ExamService()


@pytest.fixture
def session():
    return MagicMock()


def _teacher_user():
    return User(id=uuid.uuid4(), email="t@example.com", role="teacher")


def _student_user():
    return User(id=uuid.uuid4(), email="s@example.com", role="student")


def _admin_user():
    return User(id=uuid.uuid4(), email="a@example.com", role="admin")


class TestCreateExam:
    def test_rule6_teacher_must_be_assigned_to_class_session(self, service, stub_repos, session):
        exam_repo, schedule_repo, user_repo = stub_repos
        teacher = make_teacher()
        user_repo.get_teacher_profile_by_user_id.return_value = teacher
        schedule_repo.get_class_session.return_value = MagicMock(teacher_id=uuid.uuid4())  # different teacher

        payload = ExamCreate(class_session_id=uuid.uuid4(), title="T", exam_type="mcq", time_limit_minutes=30)
        with pytest.raises(HTTPException) as exc:
            service.create_exam(session, _teacher_user(), payload)
        assert exc.value.status_code == 403
        exam_repo.create_exam.assert_not_called()

    def test_class_session_must_exist(self, service, stub_repos, session):
        exam_repo, schedule_repo, user_repo = stub_repos
        user_repo.get_teacher_profile_by_user_id.return_value = make_teacher()
        schedule_repo.get_class_session.return_value = None

        payload = ExamCreate(class_session_id=uuid.uuid4(), title="T", exam_type="mcq", time_limit_minutes=30)
        with pytest.raises(HTTPException) as exc:
            service.create_exam(session, _teacher_user(), payload)
        assert exc.value.status_code == 422

    def test_mcq_question_without_correct_option_rejected(self, service, stub_repos, session):
        exam_repo, schedule_repo, user_repo = stub_repos
        teacher = make_teacher()
        user_repo.get_teacher_profile_by_user_id.return_value = teacher
        schedule_repo.get_class_session.return_value = MagicMock(teacher_id=teacher.id)

        payload = ExamCreate(
            class_session_id=uuid.uuid4(),
            title="T",
            exam_type="mcq",
            time_limit_minutes=30,
            questions=[
                QuestionCreate(
                    question_text="Q1",
                    question_type="mcq",
                    marks=5,
                    order_index=0,
                    options=[
                        QuestionOptionCreate(option_text="A", is_correct=False),
                        QuestionOptionCreate(option_text="B", is_correct=False),
                    ],
                )
            ],
        )
        with pytest.raises(HTTPException) as exc:
            service.create_exam(session, _teacher_user(), payload)
        assert exc.value.status_code == 422
        exam_repo.create_exam.assert_not_called()

    def test_success_creates_exam_and_questions(self, service, stub_repos, session):
        exam_repo, schedule_repo, user_repo = stub_repos
        teacher = make_teacher()
        user_repo.get_teacher_profile_by_user_id.return_value = teacher
        schedule_repo.get_class_session.return_value = MagicMock(teacher_id=teacher.id)
        exam = make_exam(created_by_teacher_id=teacher.id)
        exam_repo.create_exam.return_value = exam
        exam_repo.get_exam.return_value = exam
        exam_repo.list_questions_for_exam.return_value = []
        exam_repo.list_options_for_questions.return_value = []

        payload = ExamCreate(class_session_id=uuid.uuid4(), title="T", exam_type="mcq", time_limit_minutes=30)
        result = service.create_exam(session, _teacher_user(), payload)
        assert result.id == exam.id
        session.commit.assert_called_once()


class TestGetExam:
    def test_not_found_raises_404(self, service, stub_repos, session):
        exam_repo, *_ = stub_repos
        exam_repo.get_exam.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.get_exam(session, _teacher_user(), uuid.uuid4())
        assert exc.value.status_code == 404

    def test_student_draft_exam_hidden_as_404(self, service, stub_repos, session):
        exam_repo, schedule_repo, user_repo = stub_repos
        exam_repo.get_exam.return_value = make_exam(status="draft")
        user_repo.get_student_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())

        with pytest.raises(HTTPException) as exc:
            service.get_exam(session, _student_user(), uuid.uuid4())
        assert exc.value.status_code == 404

    def test_student_not_enrolled_hidden_as_404(self, service, stub_repos, session):
        exam_repo, schedule_repo, user_repo = stub_repos
        exam_repo.get_exam.return_value = make_exam(status="open")
        user_repo.get_student_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())
        schedule_repo.get_enrollment.return_value = None

        with pytest.raises(HTTPException) as exc:
            service.get_exam(session, _student_user(), uuid.uuid4())
        assert exc.value.status_code == 404

    def test_br001_is_correct_hidden_from_student_before_publish(self, service, stub_repos, session):
        exam_repo, schedule_repo, user_repo = stub_repos
        exam = make_exam(status="open")
        exam_repo.get_exam.return_value = exam
        user_repo.get_student_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())
        schedule_repo.get_enrollment.return_value = MagicMock()
        exam_repo.get_submission_by_exam_student.return_value = None
        question = make_question(exam_id=exam.id, question_type="mcq")
        exam_repo.list_questions_for_exam.return_value = [question]
        option = QuestionOption(id=uuid.uuid4(), question_id=question.id, option_text="A", is_correct=True)
        exam_repo.list_options_for_questions.return_value = [option]

        result = service.get_exam(session, _student_user(), exam.id)
        assert result.questions[0].options[0].is_correct is None

    def test_br001_is_correct_revealed_to_student_after_publish(self, service, stub_repos, session):
        exam_repo, schedule_repo, user_repo = stub_repos
        exam = make_exam(status="published")
        exam_repo.get_exam.return_value = exam
        user_repo.get_student_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())
        schedule_repo.get_enrollment.return_value = MagicMock()
        submission = make_submission(exam_id=exam.id, status="graded")
        exam_repo.get_submission_by_exam_student.return_value = submission
        question = make_question(exam_id=exam.id, question_type="mcq")
        exam_repo.list_questions_for_exam.return_value = [question]
        option = QuestionOption(id=uuid.uuid4(), question_id=question.id, option_text="A", is_correct=True)
        exam_repo.list_options_for_questions.return_value = [option]
        exam_repo.list_answers_for_submission.return_value = []

        result = service.get_exam(session, _student_user(), exam.id)
        assert result.questions[0].options[0].is_correct is True

    def test_teacher_always_sees_is_correct_even_pre_publish(self, service, stub_repos, session):
        exam_repo, schedule_repo, user_repo = stub_repos
        exam = make_exam(status="open")
        exam_repo.get_exam.return_value = exam
        question = make_question(exam_id=exam.id, question_type="mcq")
        exam_repo.list_questions_for_exam.return_value = [question]
        option = QuestionOption(id=uuid.uuid4(), question_id=question.id, option_text="A", is_correct=True)
        exam_repo.list_options_for_questions.return_value = [option]

        result = service.get_exam(session, _teacher_user(), exam.id)
        assert result.questions[0].options[0].is_correct is True


class TestUpdateExam:
    def test_not_found_raises_404(self, service, stub_repos, session):
        exam_repo, *_ = stub_repos
        exam_repo.get_exam.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.update_exam(session, _teacher_user(), uuid.uuid4(), ExamUpdate())
        assert exc.value.status_code == 404

    def test_non_creator_teacher_forbidden(self, service, stub_repos, session):
        exam_repo, schedule_repo, user_repo = stub_repos
        exam_repo.get_exam.return_value = make_exam(created_by_teacher_id=uuid.uuid4())
        user_repo.get_teacher_profile_by_user_id.return_value = make_teacher()  # different id

        with pytest.raises(HTTPException) as exc:
            service.update_exam(session, _teacher_user(), uuid.uuid4(), ExamUpdate())
        assert exc.value.status_code == 403

    def test_br003_published_exam_is_immutable(self, service, stub_repos, session):
        exam_repo, schedule_repo, user_repo = stub_repos
        teacher = make_teacher()
        exam_repo.get_exam.return_value = make_exam(created_by_teacher_id=teacher.id, status="published")
        user_repo.get_teacher_profile_by_user_id.return_value = teacher

        with pytest.raises(HTTPException) as exc:
            service.update_exam(session, _teacher_user(), uuid.uuid4(), ExamUpdate(title="New"))
        assert exc.value.status_code == 409

    def test_br003_status_cannot_move_backward(self, service, stub_repos, session):
        exam_repo, schedule_repo, user_repo = stub_repos
        teacher = make_teacher()
        exam_repo.get_exam.return_value = make_exam(created_by_teacher_id=teacher.id, status="open")
        user_repo.get_teacher_profile_by_user_id.return_value = teacher

        with pytest.raises(HTTPException) as exc:
            service.update_exam(session, _teacher_user(), uuid.uuid4(), ExamUpdate(status="draft"))
        assert exc.value.status_code == 422

    def test_status_can_move_forward(self, service, stub_repos, session):
        exam_repo, schedule_repo, user_repo = stub_repos
        teacher = make_teacher()
        exam = make_exam(created_by_teacher_id=teacher.id, status="draft")
        exam_repo.get_exam.return_value = exam
        user_repo.get_teacher_profile_by_user_id.return_value = teacher
        exam_repo.list_questions_for_exam.return_value = []
        exam_repo.list_options_for_questions.return_value = []

        service.update_exam(session, _teacher_user(), uuid.uuid4(), ExamUpdate(status="open"))
        assert exam.status == "open"
        session.commit.assert_called_once()

    def test_replace_all_questions_rejects_mcq_without_correct_option(self, service, stub_repos, session):
        exam_repo, schedule_repo, user_repo = stub_repos
        teacher = make_teacher()
        exam_repo.get_exam.return_value = make_exam(created_by_teacher_id=teacher.id, status="draft")
        user_repo.get_teacher_profile_by_user_id.return_value = teacher

        payload = ExamUpdate(
            questions=[
                QuestionCreate(
                    question_text="Q1",
                    question_type="mcq",
                    marks=5,
                    order_index=0,
                    options=[QuestionOptionCreate(option_text="A", is_correct=False)],
                )
            ]
        )
        with pytest.raises(HTTPException) as exc:
            service.update_exam(session, _teacher_user(), uuid.uuid4(), payload)
        assert exc.value.status_code == 422
        exam_repo.delete_questions_for_exam.assert_not_called()


class TestDeleteExam:
    def test_not_found_raises_404(self, service, stub_repos, session):
        exam_repo, *_ = stub_repos
        exam_repo.get_exam.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.delete_exam(session, _admin_user(), uuid.uuid4())
        assert exc.value.status_code == 404

    def test_br003_published_exam_cannot_be_deleted(self, service, stub_repos, session):
        exam_repo, *_ = stub_repos
        exam_repo.get_exam.return_value = make_exam(status="published")
        with pytest.raises(HTTPException) as exc:
            service.delete_exam(session, _admin_user(), uuid.uuid4())
        assert exc.value.status_code == 409
        exam_repo.delete_exam.assert_not_called()

    def test_non_creator_teacher_forbidden(self, service, stub_repos, session):
        exam_repo, schedule_repo, user_repo = stub_repos
        exam_repo.get_exam.return_value = make_exam(created_by_teacher_id=uuid.uuid4(), status="draft")
        user_repo.get_teacher_profile_by_user_id.return_value = make_teacher()

        with pytest.raises(HTTPException) as exc:
            service.delete_exam(session, _teacher_user(), uuid.uuid4())
        assert exc.value.status_code == 403

    def test_admin_can_delete_any_unpublished_exam(self, service, stub_repos, session):
        exam_repo, *_ = stub_repos
        exam_repo.get_exam.return_value = make_exam(status="draft")
        service.delete_exam(session, _admin_user(), uuid.uuid4())
        exam_repo.delete_exam.assert_called_once()
        session.commit.assert_called_once()


class TestStartExam:
    def test_exam_not_found_raises_404(self, service, stub_repos, session):
        exam_repo, schedule_repo, user_repo = stub_repos
        user_repo.get_student_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())
        exam_repo.get_exam.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.start_exam(session, _student_user(), uuid.uuid4())
        assert exc.value.status_code == 404

    def test_exam_not_open_rejected(self, service, stub_repos, session):
        exam_repo, schedule_repo, user_repo = stub_repos
        user_repo.get_student_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())
        exam_repo.get_exam.return_value = make_exam(status="draft")
        with pytest.raises(HTTPException) as exc:
            service.start_exam(session, _student_user(), uuid.uuid4())
        assert exc.value.status_code == 409

    def test_rule5_student_not_enrolled_forbidden(self, service, stub_repos, session):
        exam_repo, schedule_repo, user_repo = stub_repos
        user_repo.get_student_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())
        exam_repo.get_exam.return_value = make_exam(status="open")
        schedule_repo.get_enrollment.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.start_exam(session, _student_user(), uuid.uuid4())
        assert exc.value.status_code == 403
        exam_repo.create_submission.assert_not_called()

    def test_duplicate_start_after_submit_rejected(self, service, stub_repos, session):
        exam_repo, schedule_repo, user_repo = stub_repos
        user_repo.get_student_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())
        exam_repo.get_exam.return_value = make_exam(status="open")
        schedule_repo.get_enrollment.return_value = MagicMock()
        exam_repo.get_submission_by_exam_student.return_value = make_submission(status="submitted")
        with pytest.raises(HTTPException) as exc:
            service.start_exam(session, _student_user(), uuid.uuid4())
        assert exc.value.status_code == 409
        exam_repo.create_submission.assert_not_called()

    def test_idempotent_returns_existing_in_progress_submission_unchanged(self, service, stub_repos, session):
        exam_repo, schedule_repo, user_repo = stub_repos
        user_repo.get_student_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())
        exam_repo.get_exam.return_value = make_exam(status="open")
        schedule_repo.get_enrollment.return_value = MagicMock()
        existing = make_submission(status="in_progress")
        exam_repo.get_submission_by_exam_student.return_value = existing

        result, created = service.start_exam(session, _student_user(), existing.exam_id)
        assert created is False
        assert result.submission_id == existing.id
        assert result.started_at == existing.started_at
        exam_repo.create_submission.assert_not_called()

    def test_new_start_uses_server_clock_and_returns_created_true(self, service, stub_repos, session):
        exam_repo, schedule_repo, user_repo = stub_repos
        user_repo.get_student_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())
        exam = make_exam(status="open")
        exam_repo.get_exam.return_value = exam
        schedule_repo.get_enrollment.return_value = MagicMock()
        exam_repo.get_submission_by_exam_student.return_value = None
        created_submission = make_submission(exam_id=exam.id)
        exam_repo.create_submission.return_value = created_submission

        before = datetime.now(timezone.utc)
        result, created = service.start_exam(session, _student_user(), exam.id)
        after = datetime.now(timezone.utc)

        assert created is True
        call_kwargs = exam_repo.create_submission.call_args.kwargs
        assert before <= call_kwargs["started_at"] <= after
        session.commit.assert_called_once()


class TestSubmitExam:
    def _base_setup(self, stub_repos, exam_status="open", enrolled=True, submission=None):
        exam_repo, schedule_repo, user_repo = stub_repos
        user_repo.get_student_profile_by_user_id.return_value = MagicMock(id=uuid.uuid4())
        exam = make_exam(status=exam_status, time_limit_minutes=30)
        exam_repo.get_exam.return_value = exam
        schedule_repo.get_enrollment.return_value = MagicMock() if enrolled else None
        exam_repo.get_submission_by_exam_student.return_value = submission
        return exam

    def test_exam_not_open_rejected(self, service, stub_repos, session):
        self._base_setup(stub_repos, exam_status="closed")
        with pytest.raises(HTTPException) as exc:
            service.submit_exam(session, _student_user(), uuid.uuid4(), ExamSubmitRequest(answers=[]))
        assert exc.value.status_code == 409

    def test_not_enrolled_forbidden(self, service, stub_repos, session):
        self._base_setup(stub_repos, enrolled=False)
        with pytest.raises(HTTPException) as exc:
            service.submit_exam(session, _student_user(), uuid.uuid4(), ExamSubmitRequest(answers=[]))
        assert exc.value.status_code == 403

    def test_no_started_submission_rejected(self, service, stub_repos, session):
        self._base_setup(stub_repos, submission=None)
        with pytest.raises(HTTPException) as exc:
            service.submit_exam(session, _student_user(), uuid.uuid4(), ExamSubmitRequest(answers=[]))
        assert exc.value.status_code == 409

    def test_duplicate_submission_rejected(self, service, stub_repos, session):
        self._base_setup(stub_repos, submission=make_submission(status="submitted"))
        with pytest.raises(HTTPException) as exc:
            service.submit_exam(session, _student_user(), uuid.uuid4(), ExamSubmitRequest(answers=[]))
        assert exc.value.status_code == 409

    def test_vr004_time_limit_exceeded_rejected(self, service, stub_repos, session):
        started_long_ago = datetime.now(timezone.utc) - timedelta(minutes=45)
        submission = make_submission(status="in_progress", started_at=started_long_ago)
        self._base_setup(stub_repos, submission=submission)
        with pytest.raises(HTTPException) as exc:
            service.submit_exam(session, _student_user(), uuid.uuid4(), ExamSubmitRequest(answers=[]))
        assert exc.value.status_code == 409
        assert "time limit" in exc.value.detail.lower()

    def test_vr004_within_time_limit_succeeds(self, service, stub_repos, session):
        started_recently = datetime.now(timezone.utc) - timedelta(minutes=5)
        submission = make_submission(status="in_progress", started_at=started_recently)
        exam = self._base_setup(stub_repos, submission=submission)
        exam_repo, *_ = stub_repos
        exam_repo.list_questions_for_exam.return_value = []

        def mark_submitted_side_effect(_session, sub, submitted_at):
            sub.submitted_at = submitted_at
            sub.status = "submitted"

        exam_repo.mark_submitted.side_effect = mark_submitted_side_effect

        result = service.submit_exam(session, _student_user(), exam.id, ExamSubmitRequest(answers=[]))
        assert result.status == "submitted"
        exam_repo.mark_submitted.assert_called_once()
        session.commit.assert_called_once()

    def test_answer_referencing_foreign_question_rejected(self, service, stub_repos, session):
        submission = make_submission(status="in_progress", started_at=datetime.now(timezone.utc))
        exam = self._base_setup(stub_repos, submission=submission)
        exam_repo, *_ = stub_repos
        exam_repo.list_questions_for_exam.return_value = []  # no questions belong to this exam

        payload = ExamSubmitRequest(answers=[AnswerInput(question_id=uuid.uuid4(), answer_text="x")])
        with pytest.raises(HTTPException) as exc:
            service.submit_exam(session, _student_user(), exam.id, payload)
        assert exc.value.status_code == 404
        exam_repo.create_answer.assert_not_called()

    def test_all_answers_validated_before_any_write(self, service, stub_repos, session):
        submission = make_submission(status="in_progress", started_at=datetime.now(timezone.utc))
        exam = self._base_setup(stub_repos, submission=submission)
        exam_repo, *_ = stub_repos
        valid_question = make_question(exam_id=exam.id)
        exam_repo.list_questions_for_exam.return_value = [valid_question]

        payload = ExamSubmitRequest(
            answers=[
                AnswerInput(question_id=valid_question.id, answer_text="ok"),
                AnswerInput(question_id=uuid.uuid4(), answer_text="foreign"),
            ]
        )
        with pytest.raises(HTTPException) as exc:
            service.submit_exam(session, _student_user(), exam.id, payload)
        assert exc.value.status_code == 404
        exam_repo.create_answer.assert_not_called()
        session.commit.assert_not_called()
