"""
Business logic: reference data (Department, Course, Room, Semester).

Milestone 1 scope only — no business/validation rules (BR-xxx/VR-xxx) apply
to this domain (none are defined for it in Requirement_Analysis.md); this
layer's job is limited to uniqueness enforcement and FK existence checks,
translated into the standard error envelope via app.middleware.error_handlers.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.department import Department
from app.models.room import Room
from app.models.semester import Semester
from app.repositories.reference_data_repository import (
    CourseRepository,
    DepartmentRepository,
    RoomRepository,
    SemesterRepository,
)
from app.schemas.course import CourseCreate
from app.schemas.department import DepartmentCreate
from app.schemas.room import RoomCreate
from app.schemas.semester import SemesterCreate

department_repo = DepartmentRepository()
course_repo = CourseRepository()
room_repo = RoomRepository()
semester_repo = SemesterRepository()


def _not_found(entity: str, entity_id: uuid.UUID) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity} {entity_id} not found")


class DepartmentService:
    def list(self, session: Session, page: int, page_size: int):
        return department_repo.list(session, page, page_size)

    def get(self, session: Session, department_id: uuid.UUID) -> Department:
        department = department_repo.get(session, department_id)
        if department is None:
            raise _not_found("Department", department_id)
        return department

    def create(self, session: Session, payload: DepartmentCreate) -> Department:
        try:
            department = department_repo.create(session, name=payload.name, code=payload.code)
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A department with this name or code already exists.",
            )
        session.refresh(department)
        return department


class CourseService:
    def list(self, session: Session, page: int, page_size: int, department_id: uuid.UUID | None = None):
        if department_id is not None and department_repo.get(session, department_id) is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"department_id {department_id} does not reference an existing department",
            )
        return course_repo.list(session, page, page_size, department_id)

    def get(self, session: Session, course_id: uuid.UUID) -> Course:
        course = course_repo.get(session, course_id)
        if course is None:
            raise _not_found("Course", course_id)
        return course

    def create(self, session: Session, payload: CourseCreate) -> Course:
        if department_repo.get(session, payload.department_id) is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"department_id {payload.department_id} does not reference an existing department",
            )
        try:
            course = course_repo.create(
                session,
                department_id=payload.department_id,
                name=payload.name,
                code=payload.code,
                credit_hours=payload.credit_hours,
            )
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A course with this code already exists.",
            )
        session.refresh(course)
        return course


class RoomService:
    def list(self, session: Session, page: int, page_size: int):
        return room_repo.list(session, page, page_size)

    def get(self, session: Session, room_id: uuid.UUID) -> Room:
        room = room_repo.get(session, room_id)
        if room is None:
            raise _not_found("Room", room_id)
        return room

    def create(self, session: Session, payload: RoomCreate) -> Room:
        try:
            room = room_repo.create(session, name=payload.name, building=payload.building, capacity=payload.capacity)
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A room with this name already exists.",
            )
        session.refresh(room)
        return room


class SemesterService:
    def list(self, session: Session, page: int, page_size: int):
        return semester_repo.list(session, page, page_size)

    def get(self, session: Session, semester_id: uuid.UUID) -> Semester:
        semester = semester_repo.get(session, semester_id)
        if semester is None:
            raise _not_found("Semester", semester_id)
        return semester

    def create(self, session: Session, payload: SemesterCreate) -> Semester:
        try:
            semester = semester_repo.create(
                session, name=payload.name, start_date=payload.start_date, end_date=payload.end_date
            )
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A semester with this name already exists.",
            )
        session.refresh(semester)
        return semester
