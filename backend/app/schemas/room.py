"""
Pydantic request/response schemas: room (see docs/API_Contract.md §10.7-10.9).
"""

import uuid

from pydantic import BaseModel, ConfigDict, Field


class RoomCreate(BaseModel):
    name: str = Field(min_length=1)
    building: str | None = None
    capacity: int | None = None


class RoomRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    building: str | None
    capacity: int | None
