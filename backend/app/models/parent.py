"""
ORM model: parent (see docs/Database_Design.md §6.4).

Milestone 3 scope note: this model and its table are implemented because
Database_Design.md requires them and later milestones (Attendance, Results,
Fees) depend on parent_student_link existing for BR-007/NFR-003 scoping.
Milestone 3 itself ships no REST endpoint to create a Parent account or a
ParentStudentLink row, and no seed data for them either — the proposal
never defines a parent-to-student linkage mechanism (Requirement_Analysis.md
§14 item 8, still unresolved), and seeding Parent accounts is
`backend/scripts/seed_demo_data.py`'s job (a later milestone per
Implementation_Roadmap.md), not seed_admin.py's. The table exists and is
migration-verified in M3; it stays empty until a later milestone populates
or exposes it. See PROJECT_PROGRESS.md's Milestone 3 entry for the full
rationale and the user's explicit decision on this scope boundary.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Parent(Base):
    __tablename__ = "parent"
    __table_args__ = (UniqueConstraint("user_id", name="uq_parent_user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="RESTRICT"), nullable=False
    )
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
