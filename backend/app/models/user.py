"""
ORM model: user (see docs/Database_Design.md §6.1, including the
Milestone 2 design note on current_refresh_token_jti/refresh_token_expires_at).
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, func, true
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

UserRole = Enum("student", "teacher", "parent", "admin", name="user_role")


class User(Base):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    # index=True matches the explicit op.create_index("ix_user_role", ...) in
    # alembic/versions/0003_user.py — this table-level Index was previously
    # only present in the migration, not reflected on the model column,
    # which made `alembic revision --autogenerate` log a false-positive
    # "Detected removed index" against a real database (Milestone 2 review).
    role: Mapped[str] = mapped_column(UserRole, nullable=False, index=True)
    # server_default=true() matches the migration's DDL-level default
    # exactly (Milestone 2 review: the model previously declared only the
    # Python-side `default=True`, which Alembic doesn't compare by default,
    # so the two had silently diverged without ever showing up as an
    # autogenerate diff). Both defaults are kept: `default=True` gives an
    # ORM-constructed User object a value before it's ever flushed/inserted;
    # `server_default=true()` is what a raw INSERT relies on if one is ever
    # issued outside the ORM.
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    current_refresh_token_jti: Mapped[str | None] = mapped_column(String, nullable=True)
    refresh_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
