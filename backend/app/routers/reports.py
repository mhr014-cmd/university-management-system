"""
API router: reports (see docs/API_Contract.md Section 9).

Hosts `GET /results/reports` and `GET /fees/reports` — two different URL
prefixes in one file, per Implementation_Roadmap.md's Milestone 10 file
list, so this router declares no prefix of its own and each route spells
out its full path instead. `GET /attendance/reports` is NOT duplicated
here — it already lives in `routers/attendance.py` per Milestone 5.

Export endpoints (`/results/reports/pdf`, `/results/reports/excel`,
`/fees/reports/pdf`, `/fees/reports/excel` — Reports-module consistency
enhancement, so all three report tabs support the same Print/PDF/Excel
actions) reuse the exact same base64-JSON-envelope pattern already
established by `routers/attendance.py`'s `/attendance/reports/pdf`/`/excel`
(see `app/core/file_response.py`'s docstring for why a raw
`application/pdf`/xlsx response isn't used) and the same
`app/pdf/shared.py`/`app/excel/shared.py` document-building helpers —
only the report-specific content module differs per report type.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.core.file_response import file_json_response
from app.db.session import get_db
from app.excel.fees_report import generate_fees_report_excel
from app.excel.results_report import generate_results_report_excel
from app.middleware.rbac import require_roles
from app.pdf.fees_report import generate_fees_report_pdf
from app.pdf.results_report import generate_results_report_pdf
from app.schemas.report import FeesReportResponse, ResultsReportResponse
from app.services.report_scope import resolve_scope_labels
from app.services.report_service import ReportService

router = APIRouter(tags=["reports"])

report_service = ReportService()

_require_admin = Depends(require_roles("admin"))


def _export_filename(report_name: str, extension: str) -> str:
    # Timestamped, matching routers/attendance.py's _export_filename
    # convention, so repeated exports in the same session never overwrite
    # a previous download.
    return f"{report_name}-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.{extension}"


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


@router.get("/results/reports/pdf", dependencies=[_require_admin])
async def get_results_report_pdf(
    department_id: uuid.UUID | None = Query(default=None),
    semester_id: uuid.UUID | None = Query(default=None),
    student_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
):
    report = report_service.get_results_report(
        db, department_id=department_id, semester_id=semester_id, student_id=student_id
    )
    scope_labels = resolve_scope_labels(
        db, department_id=department_id, semester_id=semester_id, student_id=student_id
    )
    pdf_bytes = await run_in_threadpool(generate_results_report_pdf, scope_labels, report)
    return file_json_response(pdf_bytes, "application/pdf", _export_filename("results", "pdf"))


@router.get("/results/reports/excel", dependencies=[_require_admin])
async def get_results_report_excel(
    department_id: uuid.UUID | None = Query(default=None),
    semester_id: uuid.UUID | None = Query(default=None),
    student_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
):
    report = report_service.get_results_report(
        db, department_id=department_id, semester_id=semester_id, student_id=student_id
    )
    scope_labels = resolve_scope_labels(
        db, department_id=department_id, semester_id=semester_id, student_id=student_id
    )
    excel_bytes = await run_in_threadpool(generate_results_report_excel, scope_labels, report)
    return file_json_response(
        excel_bytes,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        _export_filename("results", "xlsx"),
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


@router.get("/fees/reports/pdf", dependencies=[_require_admin])
async def get_fees_report_pdf(
    department_id: uuid.UUID | None = Query(default=None),
    semester_id: uuid.UUID | None = Query(default=None),
    student_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
):
    report = report_service.get_fees_report(
        db, department_id=department_id, semester_id=semester_id, student_id=student_id
    )
    scope_labels = resolve_scope_labels(
        db, department_id=department_id, semester_id=semester_id, student_id=student_id
    )
    pdf_bytes = await run_in_threadpool(generate_fees_report_pdf, scope_labels, report)
    return file_json_response(pdf_bytes, "application/pdf", _export_filename("fees", "pdf"))


@router.get("/fees/reports/excel", dependencies=[_require_admin])
async def get_fees_report_excel(
    department_id: uuid.UUID | None = Query(default=None),
    semester_id: uuid.UUID | None = Query(default=None),
    student_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
):
    report = report_service.get_fees_report(
        db, department_id=department_id, semester_id=semester_id, student_id=student_id
    )
    scope_labels = resolve_scope_labels(
        db, department_id=department_id, semester_id=semester_id, student_id=student_id
    )
    excel_bytes = await run_in_threadpool(generate_fees_report_excel, scope_labels, report)
    return file_json_response(
        excel_bytes,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        _export_filename("fees", "xlsx"),
    )
