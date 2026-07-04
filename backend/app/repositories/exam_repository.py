"""
Data access repository: exam, question, question_option, exam_submission,
answer, question_grade.

All SQLAlchemy queries for the six exam-domain tables live here, per
CLAUDE.md §6 — services call this module, never the ORM session directly.
No business logic here (BR-001/BR-003/VR-003/VR-004/VR-006, RBAC, and
ownership checks live in app/services/exam_service.py).
"""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.answer import Answer
from app.models.exam import Exam
from app.models.exam_submission import ExamSubmission
from app.models.question import Question
from app.models.question_grade import QuestionGrade
from app.models.question_option import QuestionOption


class ExamRepository:
    # --- exam --------------------------------------------------------------

    def get_exam(self, session: Session, exam_id: uuid.UUID) -> Exam | None:
        return session.get(Exam, exam_id)

    def create_exam(
        self,
        session: Session,
        *,
        class_session_id: uuid.UUID,
        created_by_teacher_id: uuid.UUID,
        title: str,
        exam_type: str,
        time_limit_minutes: int,
    ) -> Exam:
        exam = Exam(
            class_session_id=class_session_id,
            created_by_teacher_id=created_by_teacher_id,
            title=title,
            exam_type=exam_type,
            time_limit_minutes=time_limit_minutes,
        )
        session.add(exam)
        session.flush()
        return exam

    def delete_exam(self, session: Session, exam: Exam) -> None:
        session.delete(exam)
        session.flush()

    def list_exams(
        self,
        session: Session,
        page: int,
        page_size: int,
        *,
        class_session_id: uuid.UUID | None = None,
        status: str | None = None,
        created_by_teacher_id: uuid.UUID | None = None,
        class_session_ids: list[uuid.UUID] | None = None,
    ) -> tuple[list[Exam], int]:
        stmt = select(Exam)
        if class_session_id is not None:
            stmt = stmt.where(Exam.class_session_id == class_session_id)
        if status is not None:
            stmt = stmt.where(Exam.status == status)
        if created_by_teacher_id is not None:
            stmt = stmt.where(Exam.created_by_teacher_id == created_by_teacher_id)
        if class_session_ids is not None:
            if not class_session_ids:
                return [], 0
            stmt = stmt.where(Exam.class_session_id.in_(class_session_ids))
        stmt = stmt.order_by(Exam.created_at.desc())
        total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = list(session.scalars(stmt.offset((page - 1) * page_size).limit(page_size)))
        return items, total

    # --- question / question_option -----------------------------------------

    def get_question(self, session: Session, question_id: uuid.UUID) -> Question | None:
        return session.get(Question, question_id)

    def create_question(
        self,
        session: Session,
        *,
        exam_id: uuid.UUID,
        question_text: str,
        question_type: str,
        marks: float,
        hint: str | None,
        order_index: int,
    ) -> Question:
        question = Question(
            exam_id=exam_id,
            question_text=question_text,
            question_type=question_type,
            marks=marks,
            hint=hint,
            order_index=order_index,
        )
        session.add(question)
        session.flush()
        return question

    def delete_questions_for_exam(self, session: Session, exam_id: uuid.UUID) -> None:
        for question in session.scalars(select(Question).where(Question.exam_id == exam_id)):
            session.delete(question)
        session.flush()

    def list_questions_for_exam(self, session: Session, exam_id: uuid.UUID) -> list[Question]:
        return list(
            session.scalars(select(Question).where(Question.exam_id == exam_id).order_by(Question.order_index))
        )

    def create_question_option(
        self, session: Session, *, question_id: uuid.UUID, option_text: str, is_correct: bool
    ) -> QuestionOption:
        option = QuestionOption(question_id=question_id, option_text=option_text, is_correct=is_correct)
        session.add(option)
        session.flush()
        return option

    def list_options_for_questions(self, session: Session, question_ids: list[uuid.UUID]) -> list[QuestionOption]:
        if not question_ids:
            return []
        return list(session.scalars(select(QuestionOption).where(QuestionOption.question_id.in_(question_ids))))

    # --- exam_submission -----------------------------------------------------

    def get_submission(self, session: Session, submission_id: uuid.UUID) -> ExamSubmission | None:
        return session.get(ExamSubmission, submission_id)

    def get_submission_by_exam_student(
        self, session: Session, exam_id: uuid.UUID, student_id: uuid.UUID
    ) -> ExamSubmission | None:
        return session.scalar(
            select(ExamSubmission).where(
                ExamSubmission.exam_id == exam_id, ExamSubmission.student_id == student_id
            )
        )

    def create_submission(
        self, session: Session, *, exam_id: uuid.UUID, student_id: uuid.UUID, started_at: datetime
    ) -> ExamSubmission:
        submission = ExamSubmission(exam_id=exam_id, student_id=student_id, started_at=started_at)
        session.add(submission)
        session.flush()
        return submission

    def mark_submitted(self, session: Session, submission: ExamSubmission, submitted_at: datetime) -> None:
        submission.submitted_at = submitted_at
        submission.status = "submitted"
        session.add(submission)
        session.flush()

    def mark_graded(self, session: Session, submission: ExamSubmission) -> None:
        submission.status = "graded"
        session.add(submission)
        session.flush()

    def list_submissions_for_exam(self, session: Session, exam_id: uuid.UUID) -> list[ExamSubmission]:
        return list(session.scalars(select(ExamSubmission).where(ExamSubmission.exam_id == exam_id)))

    # --- answer --------------------------------------------------------------

    def get_answer(self, session: Session, answer_id: uuid.UUID) -> Answer | None:
        return session.get(Answer, answer_id)

    def create_answer(
        self,
        session: Session,
        *,
        submission_id: uuid.UUID,
        question_id: uuid.UUID,
        answer_text: str | None,
        selected_option_id: uuid.UUID | None,
    ) -> Answer:
        answer = Answer(
            submission_id=submission_id,
            question_id=question_id,
            answer_text=answer_text,
            selected_option_id=selected_option_id,
        )
        session.add(answer)
        session.flush()
        return answer

    def list_answers_for_submission(self, session: Session, submission_id: uuid.UUID) -> list[Answer]:
        return list(session.scalars(select(Answer).where(Answer.submission_id == submission_id)))

    # --- question_grade --------------------------------------------------------

    def get_grade_for_answer(self, session: Session, answer_id: uuid.UUID) -> QuestionGrade | None:
        return session.scalar(select(QuestionGrade).where(QuestionGrade.answer_id == answer_id))

    def create_question_grade(
        self,
        session: Session,
        *,
        answer_id: uuid.UUID,
        graded_by_teacher_id: uuid.UUID,
        awarded_marks: float,
        feedback: str | None,
        graded_at: datetime,
    ) -> QuestionGrade:
        grade = QuestionGrade(
            answer_id=answer_id,
            graded_by_teacher_id=graded_by_teacher_id,
            awarded_marks=awarded_marks,
            feedback=feedback,
            graded_at=graded_at,
        )
        session.add(grade)
        session.flush()
        return grade

    def update_question_grade(
        self, session: Session, grade: QuestionGrade, *, awarded_marks: float, feedback: str | None, graded_at: datetime
    ) -> None:
        grade.awarded_marks = awarded_marks
        grade.feedback = feedback
        grade.graded_at = graded_at
        session.add(grade)
        session.flush()

    def list_grades_for_submission(self, session: Session, submission_id: uuid.UUID) -> list[QuestionGrade]:
        stmt = select(QuestionGrade).join(Answer, QuestionGrade.answer_id == Answer.id).where(
            Answer.submission_id == submission_id
        )
        return list(session.scalars(stmt))
