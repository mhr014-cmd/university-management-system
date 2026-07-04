"""
ORM model: answer (see docs/Database_Design.md §6.18).

`selected_option_id` uses `ON DELETE CASCADE` per Database_Design.md
§10's explicit exception (grouped with `question_option`'s own cascade).
`submission_id`/`question_id` are plain `ON DELETE RESTRICT` (the
general default) — deliberately NOT cascaded from `question`, unlike
`question_option`, since an `answer` represents a real student's
recorded response and should not be silently destroyed by an exam-content
edit; in practice this also means a `question` cannot be deleted (even
via the `exam`-level cascade) once real answers reference it.
"""

import uuid

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Answer(Base):
    __tablename__ = "answer"
    __table_args__ = (
        # Database_Design.md §10: unique (submission_id, question_id) —
        # one answer per question per submission.
        UniqueConstraint("submission_id", "question_id", name="uq_answer_submission_question"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exam_submission.id", ondelete="RESTRICT"), nullable=False
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("question.id", ondelete="RESTRICT"), nullable=False
    )
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    selected_option_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("question_option.id", ondelete="CASCADE"), nullable=True
    )
