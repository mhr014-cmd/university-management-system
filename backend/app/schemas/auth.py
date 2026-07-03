"""
Pydantic request/response schemas: auth (see docs/API_Contract.md §1).
"""

import uuid

from pydantic import BaseModel, EmailStr, Field, model_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class AuthenticatedUser(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: AuthenticatedUser


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1)
    # Minimum length only — VR-002's "minimum complexity standard" is
    # explicitly undefined by the proposal (Requirement_Analysis.md §14
    # item 13); 8 is a conservative placeholder baseline, not a decided
    # policy. Revisit if/when that ambiguity is formally resolved.
    new_password: str = Field(min_length=8)

    @model_validator(mode="after")
    def check_passwords_differ(self) -> "PasswordChangeRequest":
        if self.current_password == self.new_password:
            raise ValueError("new_password must differ from current_password")
        return self


class PasswordChangeResponse(BaseModel):
    message: str = "Password updated successfully"
