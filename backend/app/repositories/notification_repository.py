"""
Data access repository: notification.

All SQLAlchemy queries for `notification` live here, per CLAUDE.md §6 —
the service layer and dispatcher call this module, never the ORM session
directly.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationRepository:
    def create(self, session: Session, *, user_id: uuid.UUID, type: str, message: str) -> Notification:
        notification = Notification(user_id=user_id, type=type, message=message)
        session.add(notification)
        session.flush()
        return notification

    def get(self, session: Session, notification_id: uuid.UUID) -> Notification | None:
        return session.get(Notification, notification_id)

    def list_for_user(
        self,
        session: Session,
        user_id: uuid.UUID,
        *,
        is_read: bool | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Notification], int]:
        # Domain Rule 16: newest first.
        stmt = select(Notification).where(Notification.user_id == user_id)
        if is_read is not None:
            stmt = stmt.where(Notification.is_read == is_read)
        stmt = stmt.order_by(Notification.created_at.desc())
        total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = list(session.scalars(stmt.offset((page - 1) * page_size).limit(page_size)))
        return items, total

    def count_unread(self, session: Session, user_id: uuid.UUID) -> int:
        return (
            session.scalar(
                select(func.count(Notification.id)).where(
                    Notification.user_id == user_id, Notification.is_read.is_(False)
                )
            )
            or 0
        )

    def mark_read(self, session: Session, notification: Notification) -> None:
        notification.is_read = True
        session.add(notification)
        session.flush()
