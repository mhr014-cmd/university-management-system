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
from app.schemas.course import CourseCreate, CourseUpdate
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.schemas.room import RoomCreate, RoomUpdate
from app.schemas.semester import SemesterCreate, SemesterUpdate

department_repo = DepartmentRepository()
course_repo = CourseRepository()
room_repo = RoomRepository()
semester_repo = SemesterRepository()


def _not_found(entity: str, entity_id: uuid.UUID) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity} {entity_id} not found")


def _conflict_on_delete(entity: str) -> HTTPException:
    # ON DELETE RESTRICT (Database_Design.md §10) is what actually enforces
    # this — the IntegrityError it raises just needs translating into the
    # standard error envelope. Hard delete, not soft-deactivation: these
    # four are catalog/lookup data, not identity records like User/Student/
    # Teacher (Database_Design.md §10's "Deactivation, not Deletion" policy
    # is scoped to those, not to reference data).
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"This {entity.lower()} is still referenced by other records and cannot be deleted.",
    )


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

    def update(self, session: Session, department_id: uuid.UUID, payload: DepartmentUpdate) -> Department:
        department = self.get(session, department_id)
        if payload.name is not None:
            department.name = payload.name
        if payload.code is not None:
            department.code = payload.code
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A department with this name or code already exists.",
            )
        session.refresh(department)
        return department

    def delete(self, session: Session, department_id: uuid.UUID) -> None:
        department = self.get(session, department_id)
        try:
            department_repo.delete(session, department)
            session.commit()
        except IntegrityError:
            session.rollback()
            raise _conflict_on_delete("Department")


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

    def update(self, session: Session, course_id: uuid.UUID, payload: CourseUpdate) -> Course:
        course = self.get(session, course_id)
        if payload.department_id is not None:
            if department_repo.get(session, payload.department_id) is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"department_id {payload.department_id} does not reference an existing department",
                )
            course.department_id = payload.department_id
        if payload.name is not None:
            course.name = payload.name
        if payload.code is not None:
            course.code = payload.code
        if payload.credit_hours is not None:
            course.credit_hours = payload.credit_hours
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A course with this code already exists.",
            )
        session.refresh(course)
        return course

    def delete(self, session: Session, course_id: uuid.UUID) -> None:
        course = self.get(session, course_id)
        try:
            course_repo.delete(session, course)
            session.commit()
        except IntegrityError:
            session.rollback()
            raise _conflict_on_delete("Course")


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

    def update(self, session: Session, room_id: uuid.UUID, payload: RoomUpdate) -> Room:
        room = self.get(session, room_id)
        if payload.name is not None:
            room.name = payload.name
        if payload.building is not None:
            room.building = payload.building
        if payload.capacity is not None:
            room.capacity = payload.capacity
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A room with this name already exists.",
            )
        session.refresh(room)
        return room

    def delete(self, session: Session, room_id: uuid.UUID) -> None:
        room = self.get(session, room_id)
        try:
            room_repo.delete(session, room)
            session.commit()
        except IntegrityError:
            session.rollback()
            raise _conflict_on_delete("Room")


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

    def update(self, session: Session, semester_id: uuid.UUID, payload: SemesterUpdate) -> Semester:
        semester = self.get(session, semester_id)
        new_start = payload.start_date if payload.start_date is not None else semester.start_date
        new_end = payload.end_date if payload.end_date is not None else semester.end_date
        if new_start >= new_end:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="start_date must be before end_date",
            )
        if payload.name is not None:
            semester.name = payload.name
        semester.start_date = new_start
        semester.end_date = new_end
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A semester with this name already exists.",
            )
        session.refresh(semester)
        return semester

    def delete(self, session: Session, semester_id: uuid.UUID) -> None:
        semester = self.get(session, semester_id)
        try:
            semester_repo.delete(session, semester)
            session.commit()
        except IntegrityError:
            session.rollback()
            raise _conflict_on_delete("Semester")
