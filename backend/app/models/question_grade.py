"""
ORM model: question_grade (see docs/Database_Design.md §6.19).

VR-006 (`awarded_marks <= question.marks`) is deliberately NOT a
CheckConstraint here — Database_Design.md §10 notes it "requires
comparing against question.marks" (a different table), so it is enforced
at the service layer (`grading_service`-equivalent logic in
`app/services/exam_service.py`), never relied on as a DB constraint alone
per CLAUDE.md §10.
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class QuestionGrade(Base):
    __tablename__ = "question_grade"
    __table_args__ = (
        # Database_Design.md §10: question_grade.awarded_marks >= 0.
        CheckConstraint("awarded_marks >= 0", name="ck_question_grade_awarded_marks_non_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    answer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("answer.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
    )
    graded_by_teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teacher.id", ondelete="RESTRICT"), nullable=False
    )
    awarded_marks: Mapped[float] = mapped_column(Numeric, nullable=False)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    graded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
