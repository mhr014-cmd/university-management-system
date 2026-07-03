"""
ORM model: room (see docs/Database_Design.md §6.11).

Note: unlike most tables in this schema, `room` has no created_at/updated_at
columns — this matches Database_Design.md exactly, not an oversight.
"""

import uuid

from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Room(Base):
    __tablename__ = "room"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    building: Mapped[str | None] = mapped_column(String, nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
