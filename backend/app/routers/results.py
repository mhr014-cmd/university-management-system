"""
API router: results (see docs/API_Contract.md Section 5).
"""

import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.core.file_response import file_json_response
from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.middleware.rbac import require_roles
from app.models.user import User
from app.pdf.transcript_generator import generate_transcript_pdf
from app.schemas.result import (
    PendingResultsResponse,
    ResultApprovalRequest,
    ResultApprovalResponse,
    ResultSubmitRequest,
    ResultSubmitResponse,
    ResultsMeResponse,
    TeacherExamResultsResponse,
)
from app.services.result_service import ResultService

router = APIRouter(prefix="/results", tags=["results"])

result_service = ResultService()

_require_teacher = Depends(require_roles("teacher"))
_require_admin = Depends(require_roles("admin"))
_require_student_or_parent = Depends(require_roles("student", "parent"))


@router.get("/me", response_model=ResultsMeResponse, dependencies=[_require_student_or_parent])
def get_my_results(
    semester_id: uuid.UUID | None = Query(default=None),
    student_id: uuid.UUID | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return result_service.get_my_results(db, current_user, semester_id=semester_id, student_id=student_id)


@router.post("/{exam_id}/submit", response_model=ResultSubmitResponse, status_code=201, dependencies=[_require_teacher])
def submit_results(
    exam_id: uuid.UUID,
    payload: ResultSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return result_service.submit_results(db, current_user, exam_id, payload)


@router.get(
    "/exam/{exam_id}",
    response_model=TeacherExamResultsResponse,
    dependencies=[_require_teacher],
)
def get_results_for_exam(
    exam_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return result_service.get_results_for_exam(db, current_user, exam_id)


@router.get("/pending", response_model=PendingResultsResponse, dependencies=[_require_admin])
def get_pending_results(
    status_filter: str = Query(default="submitted", alias="status"),
    db: Session = Depends(get_db),
):
    return result_service.get_pending_results(db, status_filter)


@router.post("/{result_id}/approve", response_model=ResultApprovalResponse, dependencies=[_require_admin])
def approve_or_reject_result(
    result_id: uuid.UUID,
    payload: ResultApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return result_service.approve_or_reject(db, current_user, result_id, payload)


@router.get("/{student_id}/transcript")
async def get_transcript(
    student_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student_name, semesters = result_service.get_transcript_data(db, current_user, student_id)
    pdf_bytes = await run_in_threadpool(generate_transcript_pdf, student_name, semesters)
    # Base64 JSON envelope, not a raw application/pdf response — see
    # app/core/file_response.py's docstring (third-party download-manager
    # interception, confirmed via live runtime debugging).
    return file_json_response(pdf_bytes, "application/pdf", "transcript.pdf")
