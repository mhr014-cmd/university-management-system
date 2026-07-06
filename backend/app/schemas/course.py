"""
Pydantic request/response schemas: course (see docs/API_Contract.md §10.4-10.6).
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CourseCreate(BaseModel):
    department_id: uuid.UUID
    name: str = Field(min_length=1)
    code: str = Field(min_length=1)
    credit_hours: int


class CourseUpdate(BaseModel):
    department_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1)
    code: str | None = Field(default=None, min_length=1)
    credit_hours: int | None = None


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    department_id: uuid.UUID
    name: str
    code: str
    credit_hours: int
    created_at: datetime
    updated_at: datetime
