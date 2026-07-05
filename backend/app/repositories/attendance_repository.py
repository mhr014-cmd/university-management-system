"""
Data access repository: attendance_record.

All SQLAlchemy queries for the `attendance_record` table live here, per
CLAUDE.md §6 — services call this module, never the ORM session directly.
No business logic here (percentage calculation, warning threshold, and
all RBAC/ownership/BR-xxx/VR-xxx validation live in
app/services/attendance_service.py).
"""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.attendance_record import AttendanceRecord
from app.models.class_session import ClassSession
from app.models.course import Course


class AttendanceRepository:
    def get_by_id(self, session: Session, record_id: uuid.UUID) -> AttendanceRecord | None:
        return session.get(AttendanceRecord, record_id)

    def get_record(
        self, session: Session, student_id: uuid.UUID, class_session_id: uuid.UUID, attendance_date: date
    ) -> AttendanceRecord | None:
        return session.scalar(
            select(AttendanceRecord).where(
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.class_session_id == class_session_id,
                AttendanceRecord.attendance_date == attendance_date,
            )
        )

    def create_record(
        self,
        session: Session,
        *,
        student_id: uuid.UUID,
        class_session_id: uuid.UUID,
        marked_by_teacher_id: uuid.UUID,
        attendance_date: date,
        status: str,
    ) -> AttendanceRecord:
        record = AttendanceRecord(
            student_id=student_id,
            class_session_id=class_session_id,
            marked_by_teacher_id=marked_by_teacher_id,
            attendance_date=attendance_date,
            status=status,
        )
        session.add(record)
        session.flush()
        return record

    def update_status(self, session: Session, record: AttendanceRecord, status: str) -> None:
        record.status = status
        session.add(record)
        session.flush()

    def list_for_student(
        self,
        session: Session,
        student_id: uuid.UUID,
        *,
        class_session_id: uuid.UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[tuple[AttendanceRecord, Course]]:
        stmt = (
            select(AttendanceRecord, Course)
            .join(ClassSession, AttendanceRecord.class_session_id == ClassSession.id)
            .join(Course, ClassSession.course_id == Course.id)
            .where(AttendanceRecord.student_id == student_id)
        )
        if class_session_id is not None:
            stmt = stmt.where(AttendanceRecord.class_session_id == class_session_id)
        if date_from is not None:
            stmt = stmt.where(AttendanceRecord.attendance_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(AttendanceRecord.attendance_date <= date_to)
        stmt = stmt.order_by(AttendanceRecord.attendance_date)
        return [(row[0], row[1]) for row in session.execute(stmt).all()]

    def list_for_class_session(
        self,
        session: Session,
        class_session_id: uuid.UUID,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        student_id: uuid.UUID | None = None,
    ) -> list[AttendanceRecord]:
        stmt = select(AttendanceRecord).where(AttendanceRecord.class_session_id == class_session_id)
        if date_from is not None:
            stmt = stmt.where(AttendanceRecord.attendance_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(AttendanceRecord.attendance_date <= date_to)
        if student_id is not None:
            stmt = stmt.where(AttendanceRecord.student_id == student_id)
        stmt = stmt.order_by(AttendanceRecord.attendance_date)
        return list(session.scalars(stmt))

    def list_for_report(
        self,
        session: Session,
        *,
        department_id: uuid.UUID | None = None,
        semester_id: uuid.UUID | None = None,
        student_id: uuid.UUID | None = None,
    ) -> list[AttendanceRecord]:
        stmt = select(AttendanceRecord).join(ClassSession, AttendanceRecord.class_session_id == ClassSession.id)
        if department_id is not None:
            stmt = stmt.join(Course, ClassSession.course_id == Course.id).where(
                Course.department_id == department_id
            )
        if semester_id is not None:
            stmt = stmt.where(ClassSession.semester_id == semester_id)
        if student_id is not None:
            stmt = stmt.where(AttendanceRecord.student_id == student_id)
        return list(session.scalars(stmt))
