"""
Pydantic request/response schemas: question_grade, exam results, and the
Derived submission-detail view for grading (see docs/API_Contract.md
Section 3.8-3.10).
"""

import uuid
from typing import Literal

from pydantic import BaseModel, Field

ExamSubmissionStatus = Literal["in_progress", "submitted", "graded"]


class SubmissionQuestionDetail(BaseModel):
    question_id: uuid.UUID
    question_text: str
    question_type: str
    marks: float
    order_index: int
    # answer_id is None if the student left this question unanswered — no
    # `answer` row exists to grade in that case.
    answer_id: uuid.UUID | None
    answer_text: str | None
    selected_option_id: uuid.UUID | None
    # Resolved display label for selected_option_id (Milestone 11 final-
    # polish fix — Teacher grading view previously rendered the raw MCQ
    # option UUID instead of what the student actually chose).
    selected_option_text: str | None
    awarded_marks: float | None
    feedback: str | None


class ExamSubmissionDetailResponse(BaseModel):
    submission_id: uuid.UUID
    exam_id: uuid.UUID
    student_id: uuid.UUID
    status: ExamSubmissionStatus
    questions: list[SubmissionQuestionDetail]


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
    # Additive display field (final-polish pass): the Teacher Grading
    # Interface previously rendered a truncated student_id UUID prefix
    # instead of the student's name.
    student_name: str
    submission_id: uuid.UUID
    total_awarded_marks: float
    status: ExamSubmissionStatus


class ExamResultsResponse(BaseModel):
    exam_id: uuid.UUID
    submissions: list[ExamResultsSubmissionSummary]
