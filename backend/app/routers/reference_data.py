"""
API router: reference data (Department, Course, Room, Semester).

See docs/API_Contract.md §10. RBAC retrofit (Milestone 2): read endpoints
(list/get-by-id) require authentication but are open to any authenticated
role — this is lookup data every role needs (students see their
department, teachers see courses, scheduling needs rooms, etc.) and the
proposal never restricted reads. Create endpoints are Admin-only, per the
"User Roles (intended): Admin" already documented for them since
Milestone 1 — this is completing a stated intent, not a new decision.

Update/delete (Version 2.3 — Academic Setup) are additive to this same
Admin-only convention; no RBAC change. Delete is a hard DELETE — these are
catalog/lookup entities, not identity records, and the existing
ON DELETE RESTRICT FK policy (Database_Design.md §10) already provides
the only safety property needed (rejecting deletion of anything still
referenced), translated to 409 by the service layer.
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.middleware.rbac import require_roles
from app.schemas.common import PaginatedResponse
from app.schemas.course import CourseCreate, CourseRead, CourseUpdate
from app.schemas.department import DepartmentCreate, DepartmentRead, DepartmentUpdate
from app.schemas.room import RoomCreate, RoomRead, RoomUpdate
from app.schemas.semester import SemesterCreate, SemesterRead, SemesterUpdate
from app.services.reference_data_service import CourseService, DepartmentService, RoomService, SemesterService

router = APIRouter(tags=["reference-data"])

department_service = DepartmentService()
course_service = CourseService()
room_service = RoomService()
semester_service = SemesterService()

_require_authenticated = Depends(get_current_user)
_require_admin = Depends(require_roles("admin"))


@router.get("/departments", response_model=PaginatedResponse[DepartmentRead], dependencies=[_require_authenticated])
def list_departments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = department_service.list(db, page, page_size)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/departments", response_model=DepartmentRead, status_code=201, dependencies=[_require_admin])
def create_department(payload: DepartmentCreate, db: Session = Depends(get_db)):
    return department_service.create(db, payload)


@router.get(
    "/departments/{department_id}", response_model=DepartmentRead, dependencies=[_require_authenticated]
)
def get_department(department_id: uuid.UUID, db: Session = Depends(get_db)):
    return department_service.get(db, department_id)


@router.put("/departments/{department_id}", response_model=DepartmentRead, dependencies=[_require_admin])
def update_department(department_id: uuid.UUID, payload: DepartmentUpdate, db: Session = Depends(get_db)):
    return department_service.update(db, department_id, payload)


@router.delete("/departments/{department_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[_require_admin])
def delete_department(department_id: uuid.UUID, db: Session = Depends(get_db)):
    department_service.delete(db, department_id)


@router.get("/courses", response_model=PaginatedResponse[CourseRead], dependencies=[_require_authenticated])
def list_courses(
    department_id: uuid.UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = course_service.list(db, page, page_size, department_id)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/courses", response_model=CourseRead, status_code=201, dependencies=[_require_admin])
def create_course(payload: CourseCreate, db: Session = Depends(get_db)):
    return course_service.create(db, payload)


@router.get("/courses/{course_id}", response_model=CourseRead, dependencies=[_require_authenticated])
def get_course(course_id: uuid.UUID, db: Session = Depends(get_db)):
    return course_service.get(db, course_id)


@router.put("/courses/{course_id}", response_model=CourseRead, dependencies=[_require_admin])
def update_course(course_id: uuid.UUID, payload: CourseUpdate, db: Session = Depends(get_db)):
    return course_service.update(db, course_id, payload)


@router.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[_require_admin])
def delete_course(course_id: uuid.UUID, db: Session = Depends(get_db)):
    course_service.delete(db, course_id)


@router.get("/rooms", response_model=PaginatedResponse[RoomRead], dependencies=[_require_authenticated])
def list_rooms(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = room_service.list(db, page, page_size)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/rooms", response_model=RoomRead, status_code=201, dependencies=[_require_admin])
def create_room(payload: RoomCreate, db: Session = Depends(get_db)):
    return room_service.create(db, payload)


@router.get("/rooms/{room_id}", response_model=RoomRead, dependencies=[_require_authenticated])
def get_room(room_id: uuid.UUID, db: Session = Depends(get_db)):
    return room_service.get(db, room_id)


@router.put("/rooms/{room_id}", response_model=RoomRead, dependencies=[_require_admin])
def update_room(room_id: uuid.UUID, payload: RoomUpdate, db: Session = Depends(get_db)):
    return room_service.update(db, room_id, payload)


@router.delete("/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[_require_admin])
def delete_room(room_id: uuid.UUID, db: Session = Depends(get_db)):
    room_service.delete(db, room_id)


@router.get("/semesters", response_model=PaginatedResponse[SemesterRead], dependencies=[_require_authenticated])
def list_semesters(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = semester_service.list(db, page, page_size)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/semesters", response_model=SemesterRead, status_code=201, dependencies=[_require_admin])
def create_semester(payload: SemesterCreate, db: Session = Depends(get_db)):
    return semester_service.create(db, payload)


@router.get("/semesters/{semester_id}", response_model=SemesterRead, dependencies=[_require_authenticated])
def get_semester(semester_id: uuid.UUID, db: Session = Depends(get_db)):
    return semester_service.get(db, semester_id)


@router.put("/semesters/{semester_id}", response_model=SemesterRead, dependencies=[_require_admin])
def update_semester(semester_id: uuid.UUID, payload: SemesterUpdate, db: Session = Depends(get_db)):
    return semester_service.update(db, semester_id, payload)


@router.delete("/semesters/{semester_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[_require_admin])
def delete_semester(semester_id: uuid.UUID, db: Session = Depends(get_db)):
    semester_service.delete(db, semester_id)
