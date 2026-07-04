"""
Pydantic request/response schemas: exam_submission, answer (see
docs/API_Contract.md Section 3.6-3.7, and Section 3.6's Derived
`POST /exams/{id}/start` addition).
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

ExamSubmissionStatus = Literal["in_progress", "submitted", "graded"]


class ExamStartResponse(BaseModel):
    submission_id: uuid.UUID
    exam_id: uuid.UUID
    status: ExamSubmissionStatus
    started_at: datetime


class AnswerInput(BaseModel):
    question_id: uuid.UUID
    answer_text: str | None = None
    selected_option_id: uuid.UUID | None = None


class ExamSubmitRequest(BaseModel):
    answers: list[AnswerInput]


class ExamSubmitResponse(BaseModel):
    submission_id: uuid.UUID
    exam_id: uuid.UUID
    status: ExamSubmissionStatus
    submitted_at: datetime
