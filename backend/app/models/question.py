"""
ORM model: question (see docs/Database_Design.md §6.15).

`exam_id` uses `ON DELETE CASCADE`, per Database_Design.md §10's explicit
exception: deleting a (necessarily unpublished, per BR-003) draft exam
should remove its draft questions.
"""

import uuid

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

QuestionType = Enum("mcq", "short_answer", "descriptive", "coding", name="question_type")


class Question(Base):
    __tablename__ = "question"
    __table_args__ = (
        # Database_Design.md §10: question.marks > 0 (VR-003).
        CheckConstraint("marks > 0", name="ck_question_marks_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # index=True: Database_Design.md §9 "index on exam_id" — fetching exam
    # questions in order.
    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exam.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(QuestionType, nullable=False)
    marks: Mapped[float] = mapped_column(Numeric, nullable=False)
    hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
