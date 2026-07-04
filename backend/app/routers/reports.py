"""
API router: reports (see docs/API_Contract.md Section 9).

Hosts `GET /results/reports` and `GET /fees/reports` — two different URL
prefixes in one file, per Implementation_Roadmap.md's Milestone 10 file
list, so this router declares no prefix of its own and each route spells
out its full path instead. `GET /attendance/reports` is NOT duplicated
here — it already lives in `routers/attendance.py` per Milestone 5.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.rbac import require_roles
from app.schemas.report import FeesReportResponse, ResultsReportResponse
from app.services.report_service import ReportService

router = APIRouter(tags=["reports"])

report_service = ReportService()

_require_admin = Depends(require_roles("admin"))


@router.get("/results/reports", response_model=ResultsReportResponse, dependencies=[_require_admin])
def get_results_report(
    department_id: uuid.UUID | None = Query(default=None),
    semester_id: uuid.UUID | None = Query(default=None),
    student_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return report_service.get_results_report(
        db, department_id=department_id, semester_id=semester_id, student_id=student_id
    )


@router.get("/fees/reports", response_model=FeesReportResponse, dependencies=[_require_admin])
def get_fees_report(
    department_id: uuid.UUID | None = Query(default=None),
    semester_id: uuid.UUID | None = Query(default=None),
    student_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return report_service.get_fees_report(
        db, department_id=department_id, semester_id=semester_id, student_id=student_id
    )
