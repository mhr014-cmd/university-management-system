"""
Pydantic request/response schemas: result (see docs/API_Contract.md
Section 5).
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ResultStatus = Literal["submitted", "published", "rejected"]
ApprovalDecision = Literal["approve", "reject"]


class ResultCourseEntry(BaseModel):
    course_id: uuid.UUID
    course_name: str
    grade_letter: str
    grade_point: float


class ResultSemesterEntry(BaseModel):
    semester_id: uuid.UUID
    semester_name: str
    gpa: float
    courses: list[ResultCourseEntry]


class ResultsMeResponse(BaseModel):
    # student_id (the resolved target student — the caller's own id for a
    # Student, the queried child's id for a Parent) was added during
    # Milestone 7 frontend implementation: GET /results/{studentId}/transcript
    # needs a student_id, but nothing returned the calling Student's own
    # student.id anywhere, so the frontend had no way to construct that
    # URL for a "download my own transcript" action. Same class of fix as
    # Milestone 5's GET /attendance/{classId} `id` field addition.
    student_id: uuid.UUID
    semesters: list[ResultSemesterEntry]


class ResultSubmitEntry(BaseModel):
    student_id: uuid.UUID
    # grade_letter stays free text, not a fixed Literal/enum — per
    # report_service.py's own documented rationale, no letter-grade-boundary
    # scheme is hard-coded anywhere (Teacher-supplied, API_Contract.md §5.2).
    # max_length is a sanity bound only, not a grading-scale definition.
    grade_letter: str = Field(min_length=1, max_length=10)
    # le=4.0 matches Requirement_Analysis.md A-004's "conventional university
    # GPA scheme" assumption (standard 4.0 scale) — prevents an out-of-range
    # value (e.g. grade_point=99) from silently corrupting the GPA
    # computation and the printed transcript.
    grade_point: float = Field(ge=0, le=4.0)


class ResultSubmitRequest(BaseModel):
    results: list[ResultSubmitEntry] = Field(min_length=1)


class ResultSubmitResponse(BaseModel):
    exam_id: uuid.UUID
    status: ResultStatus
    submitted_at: datetime


class ResultApprovalRequest(BaseModel):
    decision: ApprovalDecision
    comment: str | None = None


class ResultApprovalResponse(BaseModel):
    id: uuid.UUID
    status: ResultStatus
    approved_at: datetime | None


class PendingResultDetailEntry(BaseModel):
    result_id: uuid.UUID
    student_id: uuid.UUID
    student_name: str
    grade_letter: str | None
    grade_point: float | None


class PendingResultQueueEntry(BaseModel):
    exam_id: uuid.UUID | None
    exam_title: str | None
    course_id: uuid.UUID
    course_name: str
    submitted_by_teacher_id: uuid.UUID
    submitted_by_teacher_name: str
    submitted_at: datetime
    status: ResultStatus
    results: list[PendingResultDetailEntry]


class PendingResultsResponse(BaseModel):
    items: list[PendingResultQueueEntry]
