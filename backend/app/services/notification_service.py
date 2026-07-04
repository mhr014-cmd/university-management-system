"""
Business logic service: notification (see docs/API_Contract.md Section 8.1-8.2).

Not explicitly named in Implementation_Roadmap.md's Milestone 9 file list
(only `app/notifications/dispatcher.py` is) — added because CLAUDE.md §6's
layering rule (routers never contain business logic, always delegate to a
service) is binding regardless of what a milestone's file list happens to
spell out, same precedent as Milestone 2's un-listed `user_repository.py`.
`dispatcher.py` remains the separate write-side event-hook module called
by other domains' services; this module is the read-side service for the
`notifications` router itself (`GET /notifications`, `PUT /notifications/{id}/read`).
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import NotificationEntry, NotificationListResponse, NotificationReadResponse

notification_repo = NotificationRepository()


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class NotificationService:
    # --- GET /notifications (FR-053) ----------------------------------------

    def list_notifications(
        self, session: Session, current_user: User, *, is_read: bool | None, page: int, page_size: int
    ) -> NotificationListResponse:
        # Domain Rules 6-9 / NFR-002-NFR-003: always scoped to the caller's
        # own user_id — there is no "view all" mode for any role, since
        # Admin's access is not documented as an exception.
        items, total = notification_repo.list_for_user(
            session, current_user.id, is_read=is_read, page=page, page_size=page_size
        )
        unread_count = notification_repo.count_unread(session, current_user.id)
        return NotificationListResponse(
            items=[NotificationEntry.model_validate(n) for n in items], unread_count=unread_count, total=total
        )

    # --- PUT /notifications/{id}/read (FR-053) ------------------------------

    def mark_as_read(
        self, session: Session, current_user: User, notification_id: uuid.UUID
    ) -> NotificationReadResponse:
        notification = notification_repo.get(session, notification_id)
        # Ownership-hiding convention: a notification belonging to another
        # user is hidden as 404, not exposed via 403.
        if notification is None or notification.user_id != current_user.id:
            raise _not_found("Notification not found")

        # Domain Rule 11: idempotent — marking an already-read notification
        # again is a no-op success, not an error.
        if not notification.is_read:
            notification_repo.mark_read(session, notification)
            session.commit()
            session.refresh(notification)

        return NotificationReadResponse(id=notification.id, is_read=notification.is_read)
