"""
Business logic service: exam (see docs/Requirement_Analysis.md
FR-017-FR-022, BR-001, BR-003, VR-003, VR-004, and the Milestone 6
mandatory Examination Domain Rules).

Calls ExamRepository/ScheduleRepository/UserRepository, never the ORM
session directly, per CLAUDE.md §6. Every RBAC/ownership/business-rule
check happens here, before any database write — routers only shape the
request/response and enforce role-only RBAC via dependencies.

Interpretive notes (Milestone 6 pre-implementation review):
- Domain Rule 2 ("class session exists and is active"): `class_session`
  has no status/active column in Database_Design.md §6.9 — "active" is
  interpreted as "exists", same as Milestone 5's identical wording.
- Domain Rule 3 ("schedule entry exists where required by the project
  design"): not required for exams — Database_Design.md never ties
  `exam`/`exam_submission` to `schedule_entry`, unlike Milestone 5's
  attendance domain, which explicitly required it. Conditional per the
  rule's own wording; not applicable here.
- Domain Rule 9 ("prevent duplicate examination records where uniqueness
  is required"): `exam` has no uniqueness constraint in Database_Design.md
  §6.14 — multiple exams per class_session are allowed (e.g. midterm +
  final), so this rule is satisfied vacuously for exam creation itself.
- Domain Rule 11 ("validate score, marks, grade, and weighting"): no
  "weighting" concept exists anywhere in this schema; only VR-003
  (marks > 0) and VR-006 (awarded_marks <= question.marks, in
  grading_service.py) apply.
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.exam_repository import ExamRepository
from app.repositories.schedule_repository import ScheduleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.exam import (
    EXAM_STATUS_ORDER,
    ExamCreate,
    ExamListItem,
    ExamRead,
    ExamUpdate,
    QuestionOptionRead,
    QuestionRead,
)
from app.schemas.submission import ExamStartResponse, ExamSubmitRequest, ExamSubmitResponse

exam_repo = ExamRepository()
schedule_repo = ScheduleRepository()
user_repo = UserRepository()


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def _forbidden(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _invalid(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail)


def _conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


class ExamService:
    # --- GET /exams (FR-017) ----------------------------------------------

    def list_exams(
        self,
        session: Session,
        current_user: User,
        page: int,
        page_size: int,
        *,
        class_session_id: uuid.UUID | None = None,
        status_filter: str | None = None,
    ) -> tuple[list[ExamListItem], int]:
        if current_user.role == "teacher":
            teacher = user_repo.get_teacher_profile_by_user_id(session, current_user.id)
            exams, total = exam_repo.list_exams(
                session,
                page,
                page_size,
                class_session_id=class_session_id,
                status=status_filter,
                created_by_teacher_id=teacher.id,
            )
        elif current_user.role == "student":
            student = user_repo.get_student_profile_by_user_id(session, current_user.id)
            class_session_ids = schedule_repo.list_class_session_ids_for_student(session, student.id)
            exams, total = exam_repo.list_exams(
                session,
                page,
                page_size,
                class_session_id=class_session_id,
                status=status_filter,
                class_session_ids=class_session_ids,
            )
            # UI_Wireframes.md Section 4: "Draft" exams are never shown on
            # the Student-facing list.
            exams = [e for e in exams if e.status != "draft"]
            total = len(exams)
        else:
            exams, total = exam_repo.list_exams(
                session, page, page_size, class_session_id=class_session_id, status=status_filter
            )

        # Single batch lookup for every exam's class/course display name —
        # not one query per exam — so this list never becomes an N+1 query.
        course_name_by_class_session_id = schedule_repo.get_course_names_for_class_sessions(
            session, list({e.class_session_id for e in exams})
        )

        items = [
            ExamListItem(
                id=e.id,
                title=e.title,
                class_session_id=e.class_session_id,
                course_name=course_name_by_class_session_id.get(e.class_session_id, "Unknown Class"),
                exam_type=e.exam_type,
                time_limit_minutes=e.time_limit_minutes,
                status=e.status,
                scheduled_at=e.scheduled_at,
            )
            for e in exams
        ]
        return items, total

    # --- GET /exams/{id} (FR-019, BR-001) ---------------------------------

    def get_exam(self, session: Session, current_user: User, exam_id: uuid.UUID) -> ExamRead:
        exam = exam_repo.get_exam(session, exam_id)
        if exam is None:
            raise _not_found("Exam not found")

        student = None
        submission = None
        if current_user.role == "student":
            student = user_repo.get_student_profile_by_user_id(session, current_user.id)
            # Ownership-hiding convention (System_Architecture.md Section 6):
            # a Student outside the exam's class, or a still-draft exam,
            # is hidden as 404, not exposed via a 403.
            if exam.status == "draft" or schedule_repo.get_enrollment(session, student.id, exam.class_session_id) is None:
                raise _not_found("Exam not found")
            submission = exam_repo.get_submission_by_exam_student(session, exam_id, student.id)

        questions = exam_repo.list_questions_for_exam(session, exam_id)
        question_ids = [q.id for q in questions]
        all_options = exam_repo.list_options_for_questions(session, question_ids)
        options_by_question: dict[uuid.UUID, list] = {}
        for option in all_options:
            options_by_question.setdefault(option.question_id, []).append(option)

        # BR-001: correct-answer/grading data hidden from Students until
        # exam.status = published.
        reveal_to_student = current_user.role != "student" or exam.status == "published"

        answers_by_question: dict[uuid.UUID, tuple] = {}
        if current_user.role == "student" and reveal_to_student and submission is not None:
            answers = exam_repo.list_answers_for_submission(session, submission.id)
            for answer in answers:
                grade = exam_repo.get_grade_for_answer(session, answer.id)
                if grade is not None:
                    answers_by_question[answer.question_id] = (grade.awarded_marks, grade.feedback)

        question_reads = []
        for q in questions:
            options = options_by_question.get(q.id, [])
            option_reads = None
            if options:
                option_reads = [
                    QuestionOptionRead(
                        id=o.id,
                        option_text=o.option_text,
                        is_correct=o.is_correct if reveal_to_student else None,
                    )
                    for o in options
                ]
            awarded_marks, feedback = answers_by_question.get(q.id, (None, None))
            question_reads.append(
                QuestionRead(
                    id=q.id,
                    question_text=q.question_text,
                    question_type=q.question_type,
                    marks=float(q.marks),
                    hint=q.hint,
                    order_index=q.order_index,
                    options=option_reads,
                    awarded_marks=float(awarded_marks) if awarded_marks is not None else None,
                    feedback=feedback,
                )
            )

        return ExamRead(
            id=exam.id,
            class_session_id=exam.class_session_id,
            created_by_teacher_id=exam.created_by_teacher_id,
            title=exam.title,
            exam_type=exam.exam_type,
            time_limit_minutes=exam.time_limit_minutes,
            status=exam.status,
            scheduled_at=exam.scheduled_at,
            created_at=exam.created_at,
            updated_at=exam.updated_at,
            questions=question_reads,
        )

    # --- POST /exams (FR-018) ---------------------------------------------

    def create_exam(self, session: Session, current_user: User, payload: ExamCreate) -> ExamRead:
        teacher = user_repo.get_teacher_profile_by_user_id(session, current_user.id)

        class_session = schedule_repo.get_class_session(session, payload.class_session_id)
        if class_session is None:
            raise _invalid("class_session_id does not reference an existing class session")
        # Domain Rule 6: only the class session's assigned Teacher may
        # create an exam for it.
        if class_session.teacher_id != teacher.id:
            raise _forbidden("You are not the assigned Teacher for this class session.")

        for q in payload.questions:
            if q.question_type == "mcq" and not any(o.is_correct for o in q.options):
                raise _invalid("Every MCQ question must have at least one option with is_correct = true.")

        exam = exam_repo.create_exam(
            session,
            class_session_id=payload.class_session_id,
            created_by_teacher_id=teacher.id,
            title=payload.title,
            exam_type=payload.exam_type,
            time_limit_minutes=payload.time_limit_minutes,
        )
        for q in payload.questions:
            question = exam_repo.create_question(
                session,
                exam_id=exam.id,
                question_text=q.question_text,
                question_type=q.question_type,
                marks=q.marks,
                hint=q.hint,
                order_index=q.order_index,
            )
            for o in q.options:
                exam_repo.create_question_option(
                    session, question_id=question.id, option_text=o.option_text, is_correct=o.is_correct
                )
        session.commit()
        return self.get_exam(session, current_user, exam.id)

    # --- PUT /exams/{id} (FR-020, BR-003 status transitions) --------------

    def update_exam(self, session: Session, current_user: User, exam_id: uuid.UUID, payload: ExamUpdate) -> ExamRead:
        exam = exam_repo.get_exam(session, exam_id)
        if exam is None:
            raise _not_found("Exam not found")

        teacher = user_repo.get_teacher_profile_by_user_id(session, current_user.id)
        if exam.created_by_teacher_id != teacher.id:
            raise _forbidden("You are not the creator of this exam.")

        # BR-003: once published, an exam is immutable.
        if exam.status == "published":
            raise _conflict("This exam is published and cannot be edited.")

        if payload.status is not None and payload.status != exam.status:
            current_rank = EXAM_STATUS_ORDER.index(exam.status)
            new_rank = EXAM_STATUS_ORDER.index(payload.status)
            if new_rank < current_rank:
                raise _invalid(f"Cannot move exam status backward from {exam.status!r} to {payload.status!r}.")
            exam.status = payload.status

        if payload.title is not None:
            exam.title = payload.title
        if payload.exam_type is not None:
            exam.exam_type = payload.exam_type
        if payload.time_limit_minutes is not None:
            exam.time_limit_minutes = payload.time_limit_minutes

        if payload.questions is not None:
            for q in payload.questions:
                if q.question_type == "mcq" and not any(o.is_correct for o in q.options):
                    raise _invalid("Every MCQ question must have at least one option with is_correct = true.")
            exam_repo.delete_questions_for_exam(session, exam.id)
            for q in payload.questions:
                question = exam_repo.create_question(
                    session,
                    exam_id=exam.id,
                    question_text=q.question_text,
                    question_type=q.question_type,
                    marks=q.marks,
                    hint=q.hint,
                    order_index=q.order_index,
                )
                for o in q.options:
                    exam_repo.create_question_option(
                        session, question_id=question.id, option_text=o.option_text, is_correct=o.is_correct
                    )

        session.add(exam)
        session.commit()
        return self.get_exam(session, current_user, exam.id)

    # --- DELETE /exams/{id} (FR-021, BR-003) -------------------------------

    def delete_exam(self, session: Session, current_user: User, exam_id: uuid.UUID) -> None:
        exam = exam_repo.get_exam(session, exam_id)
        if exam is None:
            raise _not_found("Exam not found")

        if current_user.role == "teacher":
            teacher = user_repo.get_teacher_profile_by_user_id(session, current_user.id)
            if exam.created_by_teacher_id != teacher.id:
                raise _forbidden("You are neither the creating Teacher nor an Admin.")

        if exam.status == "published":
            raise _conflict("A published exam cannot be deleted.")

        exam_repo.delete_exam(session, exam)
        session.commit()

    # --- POST /exams/{id}/start (Derived, API_Contract.md Section 3.6) ----

    def start_exam(self, session: Session, current_user: User, exam_id: uuid.UUID) -> tuple[ExamStartResponse, bool]:
        student = user_repo.get_student_profile_by_user_id(session, current_user.id)

        exam = exam_repo.get_exam(session, exam_id)
        if exam is None:
            raise _not_found("Exam not found")
        if exam.status != "open":
            raise _conflict("This exam is not open for submissions.")

        # Domain Rule 5: student must be enrolled in the exam's class session.
        if schedule_repo.get_enrollment(session, student.id, exam.class_session_id) is None:
            raise _forbidden("You are not enrolled in this exam's class.")

        existing = exam_repo.get_submission_by_exam_student(session, exam_id, student.id)
        if existing is not None:
            if existing.status in ("submitted", "graded"):
                raise _conflict("You have already submitted this exam.")
            # Idempotent: return the existing in_progress attempt, do not
            # create a second one, and never touch its started_at.
            return (
                ExamStartResponse(
                    submission_id=existing.id, exam_id=exam_id, status=existing.status, started_at=existing.started_at
                ),
                False,
            )

        # started_at is set from the server clock only — never a
        # client-supplied value — and is never updated after creation.
        started_at = datetime.now(timezone.utc)
        submission = exam_repo.create_submission(session, exam_id=exam_id, student_id=student.id, started_at=started_at)
        session.commit()
        session.refresh(submission)
        return (
            ExamStartResponse(
                submission_id=submission.id, exam_id=exam_id, status=submission.status, started_at=submission.started_at
            ),
            True,
        )

    # --- POST /exams/{id}/submit (FR-022, VR-004) --------------------------

    def submit_exam(
        self, session: Session, current_user: User, exam_id: uuid.UUID, payload: ExamSubmitRequest
    ) -> ExamSubmitResponse:
        student = user_repo.get_student_profile_by_user_id(session, current_user.id)

        exam = exam_repo.get_exam(session, exam_id)
        if exam is None:
            raise _not_found("Exam not found")
        if exam.status != "open":
            raise _conflict("This exam is not open for submissions.")

        if schedule_repo.get_enrollment(session, student.id, exam.class_session_id) is None:
            raise _forbidden("You are not enrolled in this exam's class.")

        submission = exam_repo.get_submission_by_exam_student(session, exam_id, student.id)
        if submission is None:
            raise _conflict("No exam attempt has been started — call POST /exams/{id}/start first.")
        if submission.status in ("submitted", "graded"):
            raise _conflict("This exam has already been submitted.")

        # VR-004: elapsed time computed entirely server-side, from the
        # stored started_at (set only by POST /exams/{id}/start) — never
        # from a client-supplied timestamp.
        now = datetime.now(timezone.utc)
        elapsed_minutes = (now - submission.started_at).total_seconds() / 60
        if elapsed_minutes > exam.time_limit_minutes:
            raise _conflict("The time limit for this exam has been exceeded.")

        valid_question_ids = {q.id for q in exam_repo.list_questions_for_exam(session, exam_id)}
        for a in payload.answers:
            if a.question_id not in valid_question_ids:
                raise _not_found(f"question_id {a.question_id} does not belong to this exam")

        for a in payload.answers:
            exam_repo.create_answer(
                session,
                submission_id=submission.id,
                question_id=a.question_id,
                answer_text=a.answer_text,
                selected_option_id=a.selected_option_id,
            )

        exam_repo.mark_submitted(session, submission, now)
        session.commit()
        session.refresh(submission)
        return ExamSubmitResponse(
            submission_id=submission.id, exam_id=exam_id, status=submission.status, submitted_at=submission.submitted_at
        )
