"""
Data access repository: reference data (Department, Course, Room, Semester).

All SQLAlchemy queries for these four entities live here, per CLAUDE.md §6 —
services call this module, never the ORM session directly. No business
logic here (uniqueness/error translation lives in the service layer).
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.department import Department
from app.models.room import Room
from app.models.semester import Semester


def _paginate(session: Session, stmt, page: int, page_size: int):
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = session.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    return items, total


class DepartmentRepository:
    def list(self, session: Session, page: int, page_size: int):
        return _paginate(session, select(Department).order_by(Department.name), page, page_size)

    def get(self, session: Session, department_id: uuid.UUID) -> Department | None:
        return session.get(Department, department_id)

    def create(self, session: Session, *, name: str, code: str) -> Department:
        department = Department(name=name, code=code)
        session.add(department)
        session.flush()
        return department


class CourseRepository:
    def list(self, session: Session, page: int, page_size: int, department_id: uuid.UUID | None = None):
        stmt = select(Course).order_by(Course.name)
        if department_id is not None:
            stmt = stmt.where(Course.department_id == department_id)
        return _paginate(session, stmt, page, page_size)

    def get(self, session: Session, course_id: uuid.UUID) -> Course | None:
        return session.get(Course, course_id)

    def create(self, session: Session, *, department_id: uuid.UUID, name: str, code: str, credit_hours: int) -> Course:
        course = Course(department_id=department_id, name=name, code=code, credit_hours=credit_hours)
        session.add(course)
        session.flush()
        return course


class RoomRepository:
    def list(self, session: Session, page: int, page_size: int):
        return _paginate(session, select(Room).order_by(Room.name), page, page_size)

    def get(self, session: Session, room_id: uuid.UUID) -> Room | None:
        return session.get(Room, room_id)

    def create(self, session: Session, *, name: str, building: str | None, capacity: int | None) -> Room:
        room = Room(name=name, building=building, capacity=capacity)
        session.add(room)
        session.flush()
        return room


class SemesterRepository:
    def list(self, session: Session, page: int, page_size: int):
        return _paginate(session, select(Semester).order_by(Semester.start_date), page, page_size)

    def get(self, session: Session, semester_id: uuid.UUID) -> Semester | None:
        return session.get(Semester, semester_id)

    def create(self, session: Session, *, name: str, start_date, end_date) -> Semester:
        semester = Semester(name=name, start_date=start_date, end_date=end_date)
        session.add(semester)
        session.flush()
        return semester
