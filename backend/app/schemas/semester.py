"""
Pydantic request/response schemas: semester (see docs/API_Contract.md §10.10-10.12).
"""

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SemesterCreate(BaseModel):
    name: str = Field(min_length=1)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def check_date_order(self) -> "SemesterCreate":
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        return self


class SemesterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    start_date: date | None = None
    end_date: date | None = None
    # No cross-field model_validator here (unlike SemesterCreate) — a
    # partial update may supply only one of start_date/end_date, so the
    # start<end check needs the row's existing value for whichever field
    # wasn't sent. Enforced in SemesterService.update() instead.


class SemesterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    start_date: date
    end_date: date
