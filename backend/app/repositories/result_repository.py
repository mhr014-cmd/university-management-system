"""
Data access repository: result.

All SQLAlchemy queries for `result` live here, per CLAUDE.md §6 — the
service layer calls this module, never the ORM session directly. No
business logic here (Milestone 7's mandatory Results & Academic Records
Domain Rules live in app/services/result_service.py).
"""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.result import Result
from app.models.student import Student


class ResultRepository:
    def get(self, session: Session, result_id: uuid.UUID) -> Result | None:
        return session.get(Result, result_id)

    def get_by_student_course_semester(
        self, session: Session, student_id: uuid.UUID, course_id: uuid.UUID, semester_id: uuid.UUID
    ) -> Result | None:
        return session.scalar(
            select(Result).where(
                Result.student_id == student_id,
                Result.course_id == course_id,
                Result.semester_id == semester_id,
            )
        )

    def create(
        self,
        session: Session,
        *,
        student_id: uuid.UUID,
        course_id: uuid.UUID,
        semester_id: uuid.UUID,
        exam_id: uuid.UUID | None,
        submitted_by_teacher_id: uuid.UUID,
        grade_letter: str,
        grade_point: float,
        submitted_at: datetime,
    ) -> Result:
        result = Result(
            student_id=student_id,
            course_id=course_id,
            semester_id=semester_id,
            exam_id=exam_id,
            submitted_by_teacher_id=submitted_by_teacher_id,
            grade_letter=grade_letter,
            grade_point=grade_point,
            submitted_at=submitted_at,
        )
        session.add(result)
        session.flush()
        return result

    def update_for_resubmission(
        self,
        session: Session,
        result: Result,
        *,
        exam_id: uuid.UUID | None,
        submitted_by_teacher_id: uuid.UUID,
        grade_letter: str,
        grade_point: float,
        submitted_at: datetime,
    ) -> None:
        result.exam_id = exam_id
        result.submitted_by_teacher_id = submitted_by_teacher_id
        result.grade_letter = grade_letter
        result.grade_point = grade_point
        result.status = "submitted"
        result.submitted_at = submitted_at
        result.approved_by_admin_id = None
        result.approved_at = None
        session.add(result)
        session.flush()

    def mark_approved(self, session: Session, result: Result, *, admin_id: uuid.UUID, approved_at: datetime) -> None:
        result.status = "published"
        result.approved_by_admin_id = admin_id
        result.approved_at = approved_at
        session.add(result)
        session.flush()

    def mark_rejected(self, session: Session, result: Result, *, admin_id: uuid.UUID, approved_at: datetime) -> None:
        result.status = "rejected"
        result.approved_by_admin_id = admin_id
        result.approved_at = approved_at
        session.add(result)
        session.flush()

    def list_for_student(
        self,
        session: Session,
        student_id: uuid.UUID,
        *,
        semester_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[Result]:
        stmt = select(Result).where(Result.student_id == student_id)
        if semester_id is not None:
            stmt = stmt.where(Result.semester_id == semester_id)
        if status is not None:
            stmt = stmt.where(Result.status == status)
        return list(session.scalars(stmt))

    def list_by_status(self, session: Session, status: str) -> list[Result]:
        return list(session.scalars(select(Result).where(Result.status == status).order_by(Result.submitted_at.desc())))

    def list_published_for_report(
        self,
        session: Session,
        *,
        department_id: uuid.UUID | None = None,
        semester_id: uuid.UUID | None = None,
        student_id: uuid.UUID | None = None,
    ) -> list[Result]:
        """Milestone 10: GET /results/reports — published results matching
        the given optional filters. `department_id` filters via the
        result's student's own department_id (Database_Design.md §6.2),
        since `result` has no department column of its own."""
        stmt = select(Result).where(Result.status == "published")
        if department_id is not None:
            stmt = stmt.join(Student, Student.id == Result.student_id).where(Student.department_id == department_id)
        if semester_id is not None:
            stmt = stmt.where(Result.semester_id == semester_id)
        if student_id is not None:
            stmt = stmt.where(Result.student_id == student_id)
        return list(session.scalars(stmt))
