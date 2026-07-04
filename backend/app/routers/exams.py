"""
API router: exams (see docs/API_Contract.md Section 3).
"""

import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.middleware.rbac import require_roles
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.exam import ExamCreate, ExamListItem, ExamRead, ExamUpdate
from app.schemas.grading import ExamGradeRequest, ExamGradeResponse, ExamResultsResponse
from app.schemas.submission import ExamStartResponse, ExamSubmitRequest, ExamSubmitResponse
from app.services.exam_service import ExamService
from app.services.grading_service import GradingService

router = APIRouter(prefix="/exams", tags=["exams"])

exam_service = ExamService()
grading_service = GradingService()

_require_teacher = Depends(require_roles("teacher"))
_require_student = Depends(require_roles("student"))
_require_teacher_or_admin = Depends(require_roles("teacher", "admin"))


@router.get("", response_model=PaginatedResponse[ExamListItem])
def list_exams(
    class_session_id: uuid.UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = exam_service.list_exams(
        db, current_user, page, page_size, class_session_id=class_session_id, status_filter=status_filter
    )
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=ExamRead, status_code=status.HTTP_201_CREATED, dependencies=[_require_teacher])
def create_exam(payload: ExamCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return exam_service.create_exam(db, current_user, payload)


@router.get("/{exam_id}", response_model=ExamRead)
def get_exam(exam_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return exam_service.get_exam(db, current_user, exam_id)


@router.put("/{exam_id}", response_model=ExamRead, dependencies=[_require_teacher])
def update_exam(
    exam_id: uuid.UUID, payload: ExamUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return exam_service.update_exam(db, current_user, exam_id, payload)


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[_require_teacher_or_admin])
def delete_exam(exam_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    exam_service.delete_exam(db, current_user, exam_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{exam_id}/start", response_model=ExamStartResponse, dependencies=[_require_student])
def start_exam(
    exam_id: uuid.UUID, response: Response, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    result, created = exam_service.start_exam(db, current_user, exam_id)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return result


@router.post(
    "/{exam_id}/submit",
    response_model=ExamSubmitResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_require_student],
)
def submit_exam(
    exam_id: uuid.UUID,
    payload: ExamSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return exam_service.submit_exam(db, current_user, exam_id, payload)


@router.post("/{exam_id}/grade", response_model=ExamGradeResponse, dependencies=[_require_teacher])
def grade_exam(
    exam_id: uuid.UUID,
    payload: ExamGradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return grading_service.grade_submission(db, current_user, exam_id, payload)


@router.get("/{exam_id}/results", response_model=ExamResultsResponse, dependencies=[_require_teacher_or_admin])
def get_exam_results(exam_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return grading_service.get_results(db, current_user, exam_id)
