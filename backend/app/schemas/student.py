"""
Pydantic request/response schemas: student (see docs/API_Contract.md §2.3-2.7).
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class StudentCreate(BaseModel):
    email: EmailStr
    # Admin always supplies an initial password in Milestone 3 — invite-based
    # provisioning (API_Contract.md's "or omitted if invite-based
    # provisioning is used") is deferred; no invite/email-dispatch mechanism
    # exists yet (that's Milestone 9, Notifications). Same min_length=8
    # placeholder baseline as PasswordChangeRequest (schemas/auth.py) —
    # VR-002's complexity standard is still undefined by the proposal.
    password: str = Field(min_length=8)
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    department_id: uuid.UUID
    enrollment_date: date


class StudentUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1)
    last_name: str | None = Field(default=None, min_length=1)
    department_id: uuid.UUID | None = None
    is_active: bool | None = None


class StudentRead(BaseModel):
    # Not from_attributes=True: fields span both `student` and `user`
    # (email, is_active), so the service layer constructs this explicitly
    # rather than reading it off a single ORM object.
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
