"""
Pydantic request/response schemas: question_grade, exam results (see
docs/API_Contract.md Section 3.8-3.9).
"""

import uuid
from typing import Literal

from pydantic import BaseModel, Field

ExamSubmissionStatus = Literal["in_progress", "submitted", "graded"]


class GradeInput(BaseModel):
    answer_id: uuid.UUID
    awarded_marks: float = Field(ge=0)
    feedback: str | None = None


class ExamGradeRequest(BaseModel):
    submission_id: uuid.UUID
    grades: list[GradeInput] = Field(min_length=1)


class ExamGradeResponse(BaseModel):
    submission_id: uuid.UUID
    status: ExamSubmissionStatus
    total_awarded_marks: float


class ExamResultsSubmissionSummary(BaseModel):
    student_id: uuid.UUID
    submission_id: uuid.UUID
    total_awarded_marks: float
    status: ExamSubmissionStatus


class ExamResultsResponse(BaseModel):
    exam_id: uuid.UUID
    submissions: list[ExamResultsSubmissionSummary]
