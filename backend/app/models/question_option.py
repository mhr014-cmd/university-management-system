"""
ORM model: question_option (see docs/Database_Design.md §6.16).

`question_id` uses `ON DELETE CASCADE`, per Database_Design.md §10's
explicit exception (same rationale as `question.exam_id`).
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class QuestionOption(Base):
    __tablename__ = "question_option"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("question.id", ondelete="CASCADE"), nullable=False
    )
    option_text: Mapped[str] = mapped_column(String, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
