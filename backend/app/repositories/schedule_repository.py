"""
Data access repository: schedule (class_session, enrollment, schedule_entry,
schedule_change_request).

All SQLAlchemy queries for these four tables live here, per CLAUDE.md §6 —
services call this module, never the ORM session directly. No business
logic here (conflict detection, ownership checks, and status transitions
live in app/services/schedule_service.py).
"""

import uuid
from datetime import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.class_session import ClassSession
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.room import Room
from app.models.schedule_change_request import ScheduleChangeRequest
from app.models.schedule_entry import ScheduleEntry
from app.models.student import Student
from app.models.teacher import Teacher


class ScheduleRepository:
    # --- class_session ---------------------------------------------------

    def get_class_session(self, session: Session, class_session_id: uuid.UUID) -> ClassSession | None:
        return session.get(ClassSession, class_session_id)

    def create_class_session(
        self,
        session: Session,
        *,
        course_id: uuid.UUID,
        teacher_id: uuid.UUID,
        semester_id: uuid.UUID,
        section_label: str,
    ) -> ClassSession:
        class_session = ClassSession(
            course_id=course_id, teacher_id=teacher_id, semester_id=semester_id, section_label=section_label
        )
        session.add(class_session)
        session.flush()
        return class_session

    def get_course_names_for_class_sessions(
        self, session: Session, class_session_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, str]:
        """Batch class_session_id -> course.name lookup — one query
        regardless of how many IDs are passed, so callers enriching an
        exam/result list with a display name never fall into a per-row
        N+1 pattern."""
        if not class_session_ids:
            return {}
        stmt = (
            select(ClassSession.id, Course.name)
            .join(Course, ClassSession.course_id == Course.id)
            .where(ClassSession.id.in_(class_session_ids))
        )
        return {row[0]: row[1] for row in session.execute(stmt).all()}

    # --- enrollment --------------------------------------------------------

    def get_enrollment(
        self, session: Session, student_id: uuid.UUID, class_session_id: uuid.UUID
    ) -> Enrollment | None:
        return session.scalar(
            select(Enrollment).where(
                Enrollment.student_id == student_id, Enrollment.class_session_id == class_session_id
            )
        )

    def create_enrollment(
        self, session: Session, *, student_id: uuid.UUID, class_session_id: uuid.UUID
    ) -> Enrollment:
        enrollment = Enrollment(student_id=student_id, class_session_id=class_session_id)
        session.add(enrollment)
        session.flush()
        return enrollment

    def list_class_session_ids_for_student(self, session: Session, student_id: uuid.UUID) -> list[uuid.UUID]:
        return list(session.scalars(select(Enrollment.class_session_id).where(Enrollment.student_id == student_id)))

    def list_enrolled_students(self, session: Session, class_session_id: uuid.UUID) -> list[Student]:
        stmt = (
            select(Student)
            .join(Enrollment, Enrollment.student_id == Student.id)
            .where(Enrollment.class_session_id == class_session_id)
            .order_by(Student.last_name, Student.first_name)
        )
        return list(session.scalars(stmt))

    # --- schedule_entry ------------------------------------------------------

    def get_schedule_entry(self, session: Session, schedule_entry_id: uuid.UUID) -> ScheduleEntry | None:
        return session.get(ScheduleEntry, schedule_entry_id)

    def class_session_has_schedule_entry(self, session: Session, class_session_id: uuid.UUID) -> bool:
        return (
            session.scalar(select(ScheduleEntry.id).where(ScheduleEntry.class_session_id == class_session_id))
            is not None
        )

    def create_schedule_entry(
        self,
        session: Session,
        *,
        class_session_id: uuid.UUID,
        room_id: uuid.UUID,
        teacher_id: uuid.UUID,
        day_of_week: str,
        start_time: time,
        end_time: time,
    ) -> ScheduleEntry:
        entry = ScheduleEntry(
            class_session_id=class_session_id,
            room_id=room_id,
            teacher_id=teacher_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
        )
        session.add(entry)
        session.flush()
        return entry

    def delete_schedule_entry(self, session: Session, entry: ScheduleEntry) -> None:
        session.delete(entry)
        session.flush()

    def find_overlapping_entries(
        self,
        session: Session,
        *,
        room_id: uuid.UUID,
        teacher_id: uuid.UUID,
        day_of_week: str,
        start_time: time,
        end_time: time,
        exclude_id: uuid.UUID | None = None,
    ) -> list[ScheduleEntry]:
        # Overlap iff existing.start_time < new.end_time AND
        # new.start_time < existing.end_time (standard interval-overlap
        # test) — same room OR same teacher, same day. Different
        # start_time values (so the DB-level UniqueConstraint alone
        # wouldn't catch this) are exactly the case BR-005 must cover.
        stmt = select(ScheduleEntry).where(
            ScheduleEntry.day_of_week == day_of_week,
            ScheduleEntry.start_time < end_time,
            start_time < ScheduleEntry.end_time,
            (ScheduleEntry.room_id == room_id) | (ScheduleEntry.teacher_id == teacher_id),
        )
        if exclude_id is not None:
            stmt = stmt.where(ScheduleEntry.id != exclude_id)
        return list(session.scalars(stmt))

    def list_entries_for_teacher(self, session: Session, teacher_id: uuid.UUID) -> list[tuple]:
        stmt = (
            select(ScheduleEntry, Course, Room)
            .join(ClassSession, ScheduleEntry.class_session_id == ClassSession.id)
            .join(Course, ClassSession.course_id == Course.id)
            .join(Room, ScheduleEntry.room_id == Room.id)
            .where(ScheduleEntry.teacher_id == teacher_id)
        )
        return [(row[0], row[1], row[2]) for row in session.execute(stmt).all()]

    def list_entries_for_class_sessions(self, session: Session, class_session_ids: list[uuid.UUID]) -> list[tuple]:
        if not class_session_ids:
            return []
        stmt = (
            select(ScheduleEntry, Course, Room)
            .join(ClassSession, ScheduleEntry.class_session_id == ClassSession.id)
            .join(Course, ClassSession.course_id == Course.id)
            .join(Room, ScheduleEntry.room_id == Room.id)
            .where(ScheduleEntry.class_session_id.in_(class_session_ids))
        )
        return [(row[0], row[1], row[2]) for row in session.execute(stmt).all()]

    def list_all_entries(self, session: Session, semester_id: uuid.UUID | None = None) -> list[ScheduleEntry]:
        stmt = select(ScheduleEntry)
        if semester_id is not None:
            stmt = stmt.join(ClassSession, ScheduleEntry.class_session_id == ClassSession.id).where(
                ClassSession.semester_id == semester_id
            )
        return list(session.scalars(stmt))

    # --- schedule_change_request ---------------------------------------

    def get_change_request(self, session: Session, request_id: uuid.UUID) -> ScheduleChangeRequest | None:
        return session.get(ScheduleChangeRequest, request_id)

    def create_change_request(
        self,
        session: Session,
        *,
        schedule_entry_id: uuid.UUID,
        requested_by_teacher_id: uuid.UUID,
        requested_change: dict,
    ) -> ScheduleChangeRequest:
        request = ScheduleChangeRequest(
            schedule_entry_id=schedule_entry_id,
            requested_by_teacher_id=requested_by_teacher_id,
            requested_change=requested_change,
        )
        session.add(request)
        session.flush()
        return request
