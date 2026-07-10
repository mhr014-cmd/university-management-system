"""
Business logic service: grading (see docs/Requirement_Analysis.md
FR-023, FR-024, VR-006, and the Milestone 6 mandatory Examination Domain
Rules).

Calls ExamRepository/UserRepository, never the ORM session directly, per
CLAUDE.md §6.

Re-grading policy (resolved during the Milestone 6 pre-implementation
review — API_Contract.md's own text flagged this "policy TBD"):
`POST /exams/{id}/grade` upserts `question_grade` per answer (create if
none exists, update if one does), matching `UI_Wireframes.md` Section 14's
"Save Grades" wording (a save-style, re-saveable action, not a one-shot
"Submit"). `exam_submission.status` becomes `graded` only once every
answer for that submission has a `question_grade` — matches the Grading
Interface wireframe's "'Submit Results for Approval' disabled/hidden
until all students' submissions... show status: graded" language.
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.exam_repository import ExamRepository
from app.repositories.user_repository import UserRepository
from app.schemas.grading import (
    ExamGradeRequest,
    ExamGradeResponse,
    ExamResultsResponse,
    ExamResultsSubmissionSummary,
    ExamSubmissionDetailResponse,
    SubmissionQuestionDetail,
)

exam_repo = ExamRepository()
user_repo = UserRepository()


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def _forbidden(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _invalid(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail)


def _conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


class GradingService:
    # Shared by get_submission_detail (Teacher/Admin) and
    # get_my_submission_detail (Student/Parent, final-verification-pass
    # addition below) — identical question/answer/grade assembly either
    # way; only whether awarded_marks/feedback are revealed differs.
    def _build_question_details(
        self, session: Session, exam_id: uuid.UUID, submission_id: uuid.UUID, *, reveal: bool
    ) -> list[SubmissionQuestionDetail]:
        questions = exam_repo.list_questions_for_exam(session, exam_id)
        answers_by_question = {a.question_id: a for a in exam_repo.list_answers_for_submission(session, submission_id)}
        grades_by_answer = {g.answer_id: g for g in exam_repo.list_grades_for_submission(session, submission_id)}

        # Single batch lookup for every MCQ option's display text — not one
        # query per question — matching the get_results()/student_name
        # batch-lookup convention above, so this stays free of N+1 queries.
        options = exam_repo.list_options_for_questions(session, [q.id for q in questions])
        option_text_by_id = {o.id: o.option_text for o in options}

        question_details = []
        for question in questions:
            answer = answers_by_question.get(question.id)
            grade = grades_by_answer.get(answer.id) if answer is not None else None
            selected_option_id = answer.selected_option_id if answer is not None else None
            question_details.append(
                SubmissionQuestionDetail(
                    question_id=question.id,
                    question_text=question.question_text,
                    question_type=question.question_type,
                    marks=float(question.marks),
                    order_index=question.order_index,
                    answer_id=answer.id if answer is not None else None,
                    answer_text=answer.answer_text if answer is not None else None,
                    selected_option_id=selected_option_id,
                    selected_option_text=option_text_by_id.get(selected_option_id) if selected_option_id else None,
                    awarded_marks=float(grade.awarded_marks) if grade is not None and reveal else None,
                    feedback=grade.feedback if grade is not None and reveal else None,
                )
            )
        return question_details

    # --- GET /exams/{id}/submissions/{submission_id} (Derived — see -------
    # docs/Proposal_vs_Engineering_Additions.md) -----------------------------

    def get_submission_detail(
        self, session: Session, current_user: User, exam_id: uuid.UUID, submission_id: uuid.UUID
    ) -> ExamSubmissionDetailResponse:
        exam = exam_repo.get_exam(session, exam_id)
        if exam is None:
            raise _not_found("Exam not found")

        if current_user.role == "teacher":
            teacher = user_repo.get_teacher_profile_by_user_id(session, current_user.id)
            if exam.created_by_teacher_id != teacher.id:
                raise _forbidden("You are not the creator of this exam.")
        elif current_user.role != "admin":
            raise _forbidden("Only the exam's creating Teacher or an Admin may view submission detail.")

        submission = exam_repo.get_submission(session, submission_id)
        if submission is None or submission.exam_id != exam_id:
            raise _not_found("Submission not found")

        # Teacher/Admin always see awarded_marks/feedback in full — unchanged
        # from before this method was factored to share _build_question_details.
        question_details = self._build_question_details(session, exam_id, submission.id, reveal=True)

        return ExamSubmissionDetailResponse(
            submission_id=submission.id,
            exam_id=submission.exam_id,
            student_id=submission.student_id,
            status=submission.status,
            questions=question_details,
        )

    # --- GET /exams/{id}/my-submission (final-verification-pass addition) --
    # Feature 2: exposes the per-question feedback Teachers already save via
    # POST /exams/{id}/grade to the Student who owns the submission, and to
    # a linked Parent (same student_id ownership-scoping convention already
    # used by GET /attendance/me, /results/me, /fees/me, /exams). Read-only;
    # no grading logic changes. awarded_marks/feedback are only revealed
    # once exam.status == "published" — the exact same BR-001 gate
    # exam_service.get_exam() already applies for a Student's own view of
    # this exam, applied here identically for symmetry.

    def get_my_submission_detail(
        self,
        session: Session,
        current_user: User,
        exam_id: uuid.UUID,
        *,
        student_id: uuid.UUID | None = None,
    ) -> ExamSubmissionDetailResponse:
        exam = exam_repo.get_exam(session, exam_id)
        if exam is None:
            raise _not_found("Exam not found")

        if current_user.role == "student":
            student = user_repo.get_student_profile_by_user_id(session, current_user.id)
            target_student_id = student.id
        elif current_user.role == "parent":
            parent = user_repo.get_parent_profile_by_user_id(session, current_user.id)
            if student_id is None or not user_repo.parent_has_linked_student(session, parent.id, student_id):
                raise _forbidden("You may only view feedback for a linked student.")
            target_student_id = student_id
        else:
            raise _forbidden("Only the submitting Student or a linked Parent may view this submission.")

        submission = exam_repo.get_submission_by_exam_student(session, exam_id, target_student_id)
        if submission is None:
            raise _not_found("Submission not found")

        reveal = exam.status == "published"
        question_details = self._build_question_details(session, exam_id, submission.id, reveal=reveal)

        return ExamSubmissionDetailResponse(
            submission_id=submission.id,
            exam_id=submission.exam_id,
            student_id=submission.student_id,
            status=submission.status,
            questions=question_details,
        )

    # --- POST /exams/{id}/grade (FR-023, VR-006) ---------------------------

    def grade_submission(
        self, session: Session, current_user: User, exam_id: uuid.UUID, payload: ExamGradeRequest
    ) -> ExamGradeResponse:
        exam = exam_repo.get_exam(session, exam_id)
        if exam is None:
            raise _not_found("Exam not found")

        teacher = user_repo.get_teacher_profile_by_user_id(session, current_user.id)
        # Domain Rule 6: only the exam's creating Teacher may grade it.
        if exam.created_by_teacher_id != teacher.id:
            raise _forbidden("You are not the creator of this exam.")

        submission = exam_repo.get_submission(session, payload.submission_id)
        if submission is None or submission.exam_id != exam_id:
            raise _not_found("Submission not found")
        if submission.status == "in_progress":
            raise _conflict("This submission has not been submitted yet.")

        # Validate every grade in the batch before writing any of them
        # (Domain Rule 12 — all validation before any database write).
        answers_by_id = {}
        for grade_input in payload.grades:
            answer = exam_repo.get_answer(session, grade_input.answer_id)
            if answer is None or answer.submission_id != submission.id:
                raise _not_found(f"answer_id {grade_input.answer_id} does not belong to this submission")
            question = exam_repo.get_question(session, answer.question_id)
            # VR-006: awarded_marks cannot exceed the question's max marks.
            if grade_input.awarded_marks > float(question.marks):
                raise _invalid(
                    f"awarded_marks {grade_input.awarded_marks} exceeds question max marks {question.marks}"
                )
            answers_by_id[grade_input.answer_id] = answer

        now = datetime.now(timezone.utc)
        for grade_input in payload.grades:
            existing_grade = exam_repo.get_grade_for_answer(session, grade_input.answer_id)
            if existing_grade is not None:
                exam_repo.update_question_grade(
                    session,
                    existing_grade,
                    awarded_marks=grade_input.awarded_marks,
                    feedback=grade_input.feedback,
                    graded_at=now,
                )
            else:
                exam_repo.create_question_grade(
                    session,
                    answer_id=grade_input.answer_id,
                    graded_by_teacher_id=teacher.id,
                    awarded_marks=grade_input.awarded_marks,
                    feedback=grade_input.feedback,
                    graded_at=now,
                )

        # exam_submission.status becomes "graded" only once every answer
        # for this submission has a question_grade — see module docstring.
        all_answers = exam_repo.list_answers_for_submission(session, submission.id)
        all_grades = exam_repo.list_grades_for_submission(session, submission.id)
        if len(all_grades) >= len(all_answers) and len(all_answers) > 0:
            exam_repo.mark_graded(session, submission)

        session.commit()
        session.refresh(submission)

        total_awarded_marks = sum(float(g.awarded_marks) for g in exam_repo.list_grades_for_submission(session, submission.id))
        return ExamGradeResponse(
            submission_id=submission.id, status=submission.status, total_awarded_marks=total_awarded_marks
        )

    # --- GET /exams/{id}/results (FR-024) ----------------------------------

    def get_results(self, session: Session, current_user: User, exam_id: uuid.UUID) -> ExamResultsResponse:
        exam = exam_repo.get_exam(session, exam_id)
        if exam is None:
            raise _not_found("Exam not found")

        if current_user.role == "teacher":
            teacher = user_repo.get_teacher_profile_by_user_id(session, current_user.id)
            if exam.created_by_teacher_id != teacher.id:
                raise _forbidden("You are not the creator of this exam.")

        submissions = exam_repo.list_submissions_for_exam(session, exam_id)

        # Single batch lookup for every submission's student display name —
        # not one query per submission — so this listing never becomes an
        # N+1 query.
        students = user_repo.list_students_by_ids(session, [sub.student_id for sub in submissions])
        name_by_student_id = {s.id: f"{s.first_name} {s.last_name}" for s in students}

        summaries = []
        for submission in submissions:
            grades = exam_repo.list_grades_for_submission(session, submission.id)
            total = sum(float(g.awarded_marks) for g in grades)
            summaries.append(
                ExamResultsSubmissionSummary(
                    student_id=submission.student_id,
                    student_name=name_by_student_id.get(submission.student_id, "Unknown Student"),
                    submission_id=submission.id,
                    total_awarded_marks=total,
                    status=submission.status,
                )
            )
        return ExamResultsResponse(exam_id=exam_id, submissions=summaries)
