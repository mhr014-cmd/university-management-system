"""
API router: schedule (see docs/API_Contract.md Section 7).
"""

import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.middleware.rbac import require_roles
from app.models.user import User
from app.schemas.schedule import (
    ClassSessionCreate,
    ClassSessionRead,
    ClassSessionRosterResponse,
    EnrollmentCreate,
    EnrollmentRead,
    ScheduleChangeRequestCreate,
    ScheduleChangeRequestCreateResponse,
    ScheduleChangeRequestListResponse,
    ScheduleChangeRequestResolve,
    ScheduleChangeRequestResolveResponse,
    ScheduleConflictsResponse,
    ScheduleEntryCreate,
    ScheduleEntryRead,
    ScheduleEntryUpdate,
    ScheduleMeResponse,
)
from app.services.schedule_service import ScheduleService

router = APIRouter(prefix="/schedule", tags=["schedule"])

schedule_service = ScheduleService()

_require_admin = Depends(require_roles("admin"))
_require_teacher = Depends(require_roles("teacher"))
# Gap closure (post-M11 audit): the proposal (Section 5, Parent — "Results
# & schedule") explicitly promises Parents visibility into their child's
# class timetable; this endpoint previously excluded Parent entirely.
# Parent access is scoped to a linked child via student_id, mirroring the
# same convention already used by GET /fees/me and GET /results/me.
_require_student_teacher_or_parent = Depends(require_roles("student", "teacher", "parent"))
_require_teacher_or_admin = Depends(require_roles("teacher", "admin"))


@router.get("/me", response_model=ScheduleMeResponse, dependencies=[_require_student_teacher_or_parent])
def get_my_schedule(
    student_id: uuid.UUID | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return schedule_service.get_me(db, current_user, student_id=student_id)


@router.post("", response_model=ScheduleEntryRead, status_code=status.HTTP_201_CREATED, dependencies=[_require_admin])
def create_schedule_entry(payload: ScheduleEntryCreate, db: Session = Depends(get_db)):
    return schedule_service.create_entry(db, payload)


@router.put("/{schedule_entry_id}", response_model=ScheduleEntryRead, dependencies=[_require_admin])
def update_schedule_entry(schedule_entry_id: uuid.UUID, payload: ScheduleEntryUpdate, db: Session = Depends(get_db)):
    return schedule_service.update_entry(db, schedule_entry_id, payload)


@router.delete("/{schedule_entry_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[_require_admin])
def delete_schedule_entry(schedule_entry_id: uuid.UUID, db: Session = Depends(get_db)):
    schedule_service.delete_entry(db, schedule_entry_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/conflicts", response_model=ScheduleConflictsResponse, dependencies=[_require_admin])
def get_schedule_conflicts(
    semester_id: uuid.UUID | None = Query(default=None), db: Session = Depends(get_db)
):
    return schedule_service.get_conflicts(db, semester_id)


@router.post(
    "/change-requests",
    response_model=ScheduleChangeRequestCreateResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_require_teacher],
)
def create_change_request(
    payload: ScheduleChangeRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return schedule_service.create_change_request(db, current_user, payload)


# Admin approval queue (production-readiness audit gap closure) — backend
# create/resolve already existed, but nothing ever listed pending requests.
@router.get(
    "/change-requests",
    response_model=ScheduleChangeRequestListResponse,
    dependencies=[_require_admin],
)
def list_change_requests(
    status_filter: str | None = Query(default="pending", alias="status"),
    db: Session = Depends(get_db),
):
    return schedule_service.list_change_requests(db, status_filter)


@router.post(
    "/change-requests/{request_id}/resolve",
    response_model=ScheduleChangeRequestResolveResponse,
    dependencies=[_require_admin],
)
def resolve_change_request(
    request_id: uuid.UUID,
    payload: ScheduleChangeRequestResolve,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return schedule_service.resolve_change_request(db, request_id, payload, current_user)


@router.post(
    "/class-sessions",
    response_model=ClassSessionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_require_admin],
)
def create_class_session(payload: ClassSessionCreate, db: Session = Depends(get_db)):
    return schedule_service.create_class_session(db, payload)


@router.post(
    "/enrollments", response_model=EnrollmentRead, status_code=status.HTTP_201_CREATED, dependencies=[_require_admin]
)
def create_enrollment(payload: EnrollmentCreate, db: Session = Depends(get_db)):
    return schedule_service.create_enrollment(db, payload)


@router.get(
    "/class-sessions/{class_session_id}/roster",
    response_model=ClassSessionRosterResponse,
    dependencies=[_require_teacher_or_admin],
)
def get_class_session_roster(
    class_session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return schedule_service.get_roster(db, current_user, class_session_id)
