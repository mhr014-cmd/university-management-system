"""
API router: attendance (see docs/API_Contract.md Section 4).

Role-only RBAC is enforced here via `dependencies=[]`; every ownership and
business-rule check (Rules 1-10 in this milestone's mandate) happens in
app/services/attendance_service.py, never here, per CLAUDE.md §6.
"""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.middleware.rbac import require_roles
from app.models.user import User
from app.schemas.attendance import (
    AttendanceMarkRequest,
    AttendanceMeQuery,
    AttendanceMeResponse,
    AttendanceRecordRead,
    AttendanceReportsResponse,
    AttendanceUpdateRequest,
    ClassAttendanceResponse,
)
from app.services.attendance_service import AttendanceService

router = APIRouter(prefix="/attendance", tags=["attendance"])

attendance_service = AttendanceService()

_require_student = Depends(require_roles("student"))
_require_teacher = Depends(require_roles("teacher"))
_require_teacher_or_admin = Depends(require_roles("teacher", "admin"))
# Rule 9: Parent access is explicitly documented for this one endpoint
# only (API_Contract.md Section 4.3) — Teacher/Admin/Parent are the only
# roles ever passed to require_roles() for attendance endpoints; Student
# is never included except for GET /attendance/me, per Rule 8.
_require_teacher_admin_or_parent = Depends(require_roles("teacher", "admin", "parent"))
_require_admin = Depends(require_roles("admin"))
# Production-polish gap closure: GET /attendance/me now also accepts Parent
# (with a required student_id scoped to a linked child), mirroring the
# Parent-scoping convention already used by GET /fees/me and GET /results/me
# — see attendance_service.get_me and docs/Proposal_vs_Engineering_Additions.md.
_require_student_or_parent = Depends(require_roles("student", "parent"))


@router.get("/me", response_model=AttendanceMeResponse, dependencies=[_require_student_or_parent])
def get_my_attendance(
    class_session_id: uuid.UUID | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    student_id: uuid.UUID | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = AttendanceMeQuery(
        class_session_id=class_session_id, date_from=date_from, date_to=date_to, student_id=student_id
    )
    return attendance_service.get_me(db, current_user, query)


@router.post("", response_model=list[AttendanceRecordRead], status_code=201, dependencies=[_require_teacher])
def mark_attendance(
    payload: AttendanceMarkRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return attendance_service.mark_attendance(db, current_user, payload)


@router.put("/{attendance_id}", response_model=AttendanceRecordRead, dependencies=[_require_teacher_or_admin])
def update_attendance(
    attendance_id: uuid.UUID,
    payload: AttendanceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return attendance_service.update_attendance(db, current_user, attendance_id, payload)


# Registered before /{class_id} — FastAPI matches routes in declaration
# order, and "/attendance/reports" would otherwise be swallowed by the
# "/{class_id}" path parameter (matching class_id="reports" and failing
# UUID validation with a confusing 422 instead of reaching this endpoint).
@router.get("/reports", response_model=AttendanceReportsResponse, dependencies=[_require_admin])
def get_attendance_reports(
    department_id: uuid.UUID | None = Query(default=None),
    semester_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return attendance_service.get_reports(db, department_id, semester_id)


@router.get(
    "/{class_id}", response_model=ClassAttendanceResponse, dependencies=[_require_teacher_admin_or_parent]
)
def get_class_attendance(
    class_id: uuid.UUID,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    student_id: uuid.UUID | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return attendance_service.get_class_attendance(
        db, current_user, class_id, date_from=date_from, date_to=date_to, student_id=student_id
    )
