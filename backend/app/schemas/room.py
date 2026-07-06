"""
Pydantic request/response schemas: room (see docs/API_Contract.md §10.7-10.9).
"""

import uuid

from pydantic import BaseModel, ConfigDict, Field


class RoomCreate(BaseModel):
    name: str = Field(min_length=1)
    building: str | None = None
    # ge=1: a room's capacity, when supplied, must be able to hold at
    # least one person — production-readiness QA pass gap closure
    # (zero/negative previously accepted). Still nullable/optional since
    # capacity itself may be unknown.
    capacity: int | None = Field(default=None, ge=1)


class RoomUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    building: str | None = None
    capacity: int | None = Field(default=None, ge=1)


class RoomRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    building: str | None
    capacity: int | None
