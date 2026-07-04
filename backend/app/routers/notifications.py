"""
API router: notifications (see docs/API_Contract.md Section 8).
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.notification import NotificationListResponse, NotificationReadResponse
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])

notification_service = NotificationService()


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    is_read: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return notification_service.list_notifications(db, current_user, is_read=is_read, page=page, page_size=page_size)


@router.put("/{notification_id}/read", response_model=NotificationReadResponse)
def mark_notification_read(
    notification_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return notification_service.mark_as_read(db, current_user, notification_id)
