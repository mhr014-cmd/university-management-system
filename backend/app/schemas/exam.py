"""
Pydantic request/response schemas: exam, question, question_option (see
docs/API_Contract.md Section 3.1-3.5).
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ExamType = Literal["mcq", "written", "practical_coding", "mixed"]
ExamStatus = Literal["draft", "scheduled", "open", "closed", "published"]
QuestionType = Literal["mcq", "short_answer", "descriptive", "coding"]

# BR-003: forward-only status progression, resolved during the Milestone 6
# pre-implementation review (PUT /exams/{id} carries transitions — see
# UI_Wireframes.md Section 13's "Publish Exam" wording, no separate
# transition endpoint exists).
EXAM_STATUS_ORDER: list[ExamStatus] = ["draft", "scheduled", "open", "closed", "published"]


class QuestionOptionCreate(BaseModel):
    option_text: str = Field(min_length=1)
    is_correct: bool = False


class QuestionCreate(BaseModel):
    question_text: str = Field(min_length=1)
    question_type: QuestionType
    marks: float = Field(gt=0)
    hint: str | None = None
    order_index: int
    options: list[QuestionOptionCreate] = Field(default_factory=list)


class ExamCreate(BaseModel):
    class_session_id: uuid.UUID
    title: str = Field(min_length=1)
    exam_type: ExamType
    time_limit_minutes: int = Field(gt=0)
    questions: list[QuestionCreate] = Field(default_factory=list)


class ExamUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    exam_type: ExamType | None = None
    time_limit_minutes: int | None = Field(default=None, gt=0)
    # BR-003 status transition, resolved during pre-implementation review —
    # see EXAM_STATUS_ORDER above. Optional: a PUT may edit content only,
    # transition status only, or both in one call.
    status: ExamStatus | None = None
    # Replace-all semantics, per API_Contract.md Section 3.4's note that
    # "question list replacement semantics [are] defined at implementation" —
    # if provided, the exam's full question set is replaced.
    questions: list[QuestionCreate] | None = None


class QuestionOptionRead(BaseModel):
    id: uuid.UUID
    option_text: str
    # None when hidden from a Student caller pre-publish (BR-001) — the
    # service layer decides visibility, not this schema.
    is_correct: bool | None


class QuestionRead(BaseModel):
    id: uuid.UUID
    question_text: str
    question_type: QuestionType
    marks: float
    hint: str | None
    order_index: int
    options: list[QuestionOptionRead] | None = None
    # Populated only for the requesting Student's own graded answer, and
    # only once exam.status = published (BR-001/FR-025) — never populated
    # for Teacher/Admin callers or for other students' data.
    awarded_marks: float | None = None
    feedback: str | None = None


class ExamRead(BaseModel):
    id: uuid.UUID
    class_session_id: uuid.UUID
    created_by_teacher_id: uuid.UUID
    title: str
    exam_type: ExamType
    time_limit_minutes: int
    status: ExamStatus
    scheduled_at: datetime | None
    created_at: datetime
    updated_at: datetime
    questions: list[QuestionRead]


class ExamListItem(BaseModel):
    id: uuid.UUID
    title: str
    class_session_id: uuid.UUID
    exam_type: ExamType
    time_limit_minutes: int
    status: ExamStatus
    scheduled_at: datetime | None
