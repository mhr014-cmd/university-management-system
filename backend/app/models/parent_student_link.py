"""
ORM model: parent_student_link (see docs/Database_Design.md §6.6).

Milestone 3 leaves this table empty — see the scope note in
app/models/parent.py.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ParentStudentLink(Base):
    __tablename__ = "parent_student_link"
    __table_args__ = (UniqueConstraint("parent_id", "student_id", name="uq_parent_student_link_parent_student"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parent.id", ondelete="RESTRICT"), nullable=False
    )
    # index=True: Database_Design.md §9 calls for a standalone index on
    # student_id (reverse lookup — "which parents belong to a student"),
    # separate from the composite unique index above.
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    relationship_type: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
