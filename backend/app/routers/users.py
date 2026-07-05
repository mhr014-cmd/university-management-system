"""
API router: users (see docs/API_Contract.md §2).

`/users/me` needs the resolved `User` object (always scoped to the caller,
per NFR-002 — no ownership check beyond "this is the token's own subject"),
so it takes `get_current_user` as a parameter dependency rather than a
role-only `dependencies=[]` check. Student/Teacher management endpoints
follow the same `dependencies=[_require_x]` pattern as
app/routers/reference_data.py.
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.middleware.rbac import require_roles
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.student import StudentCreate, StudentRead, StudentUpdate
from app.schemas.teacher import TeacherCreate, TeacherRead, TeacherUpdate
from app.schemas.user import MeRead, MeUpdate, MyChildrenResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

user_service = UserService()

_require_admin = Depends(require_roles("admin"))
_require_admin_or_teacher = Depends(require_roles("admin", "teacher"))
_require_parent = Depends(require_roles("parent"))


@router.get("/me", response_model=MeRead)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return user_service.get_me(db, current_user)


@router.put("/me", response_model=MeRead)
def update_me(
    payload: MeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return user_service.update_me(db, current_user, payload)


@router.get("/me/children", response_model=MyChildrenResponse, dependencies=[_require_parent])
def get_my_children(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return user_service.get_my_children(db, current_user)


@router.get("/students", response_model=PaginatedResponse[StudentRead], dependencies=[_require_admin_or_teacher])
def list_students(
    department_id: uuid.UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = user_service.list_students(db, page, page_size, department_id)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/students", response_model=StudentRead, status_code=status.HTTP_201_CREATED, dependencies=[_require_admin])
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    return user_service.create_student(db, payload)


@router.get("/students/{student_id}", response_model=StudentRead, dependencies=[_require_admin_or_teacher])
def get_student(student_id: uuid.UUID, db: Session = Depends(get_db)):
    return user_service.get_student(db, student_id)


@router.put("/students/{student_id}", response_model=StudentRead, dependencies=[_require_admin])
def update_student(student_id: uuid.UUID, payload: StudentUpdate, db: Session = Depends(get_db)):
    return user_service.update_student(db, student_id, payload)


@router.delete("/students/{student_id}", dependencies=[_require_admin])
def deactivate_student(student_id: uuid.UUID, db: Session = Depends(get_db)):
    result = user_service.deactivate_student(db, student_id)
    return {"id": result.id, "is_active": result.is_active}


@router.get("/teachers", response_model=PaginatedResponse[TeacherRead], dependencies=[_require_admin])
def list_teachers(
    department_id: uuid.UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = user_service.list_teachers(db, page, page_size, department_id)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/teachers", response_model=TeacherRead, status_code=status.HTTP_201_CREATED, dependencies=[_require_admin])
def create_teacher(payload: TeacherCreate, db: Session = Depends(get_db)):
    return user_service.create_teacher(db, payload)


@router.put("/teachers/{teacher_id}", response_model=TeacherRead, dependencies=[_require_admin])
def update_teacher(teacher_id: uuid.UUID, payload: TeacherUpdate, db: Session = Depends(get_db)):
    return user_service.update_teacher(db, teacher_id, payload)
