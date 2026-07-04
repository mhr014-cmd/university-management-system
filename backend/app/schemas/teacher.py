"""
Pydantic request/response schemas: teacher (see docs/API_Contract.md §2.8-2.10).
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class TeacherCreate(BaseModel):
    email: EmailStr
    # Same provisioning decision as StudentCreate — see its comment.
    password: str = Field(min_length=8)
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    department_id: uuid.UUID
    hire_date: date | None = None


class TeacherUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1)
    last_name: str | None = Field(default=None, min_length=1)
    department_id: uuid.UUID | None = None
    is_active: bool | None = None


class TeacherRead(BaseModel):
    # Not from_attributes=True — see StudentRead's comment; same reasoning.
    id: uuid.UUID
    user_id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    department_id: uuid.UUID
    is_active: bool
    # Milestone 10, Admin Dashboard Recent User Signups widget (additive;
    # no business logic or schema change — `user.created_at` already existed).
    created_at: datetime
