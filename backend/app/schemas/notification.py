"""
Pydantic request/response schemas: notification (see docs/API_Contract.md
Section 8).
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

NotificationType = Literal["result_published", "schedule_change", "attendance_warning", "fee_due", "other"]


class NotificationEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: NotificationType
    message: str
    is_read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationEntry]
    unread_count: int
    total: int


class NotificationReadResponse(BaseModel):
    id: uuid.UUID
    is_read: bool
