"""
Pydantic request/response schemas: user profile ("/users/me", see
docs/API_Contract.md §2.1-2.2). Named user.py to match the placeholder
module Milestone 0 actually scaffolded — Implementation_Roadmap.md's M3
file list names this `user_profile.py`; that reference was corrected to
`user.py` in the same change that added this file (see
docs/Implementation_Roadmap.md).
"""

import uuid

from pydantic import BaseModel, EmailStr, Field


class UserProfile(BaseModel):
    first_name: str
    last_name: str
    profile_photo_url: str | None = None
    # None for Parent/Admin, who have no department_id (Database_Design.md
    # §6.4/§6.5) — per UI_Wireframes.md §3, the field simply isn't rendered
    # for those roles.
    department_id: uuid.UUID | None = None
    # Additive display field (production-polish audit): the Profile page's
    # read-only Department field previously rendered the raw department_id
    # UUID — see department_name below.
    department_name: str | None = None


class MeRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: str
    profile: UserProfile


class MeUpdate(BaseModel):
    # VR-009: role, is_active, and department_id are deliberately absent
    # from this schema — there is no field for them to be smuggled through,
    # not just a runtime check that rejects them. Admin-only account
    # management uses StudentUpdate/TeacherUpdate instead.
    first_name: str | None = Field(default=None, min_length=1)
    last_name: str | None = Field(default=None, min_length=1)
    profile_photo_url: str | None = None


class ChildEntry(BaseModel):
    """GET /users/me/children (Parent-only, production-polish audit): closes
    the long-standing gap where no endpoint enumerated a Parent's linked
    children, forcing the Parent Dashboard to require a manually-typed
    student_id instead of a real child selector."""

    id: uuid.UUID
    first_name: str
    last_name: str
    department_id: uuid.UUID


class MyChildrenResponse(BaseModel):
    children: list[ChildEntry]
