"""
Data access repository: user.

All SQLAlchemy queries for the `user` table live here, per CLAUDE.md §6.
No user-creation method here — Milestone 2 has no account-creation
endpoint (that's Milestone 3, User Management); adding one now would be
scope beyond what this milestone needs.
"""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def get_by_email(self, session: Session, email: str) -> User | None:
        return session.scalar(select(User).where(User.email == email))

    def get_by_id(self, session: Session, user_id: uuid.UUID) -> User | None:
        return session.get(User, user_id)

    def set_refresh_token(self, session: Session, user: User, jti: str, expires_at: datetime) -> None:
        user.current_refresh_token_jti = jti
        user.refresh_token_expires_at = expires_at
        session.add(user)
        session.commit()
        session.refresh(user)

    def clear_refresh_token(self, session: Session, user: User) -> None:
        user.current_refresh_token_jti = None
        user.refresh_token_expires_at = None
        session.add(user)
        session.commit()

    def update_password_hash(self, session: Session, user: User, password_hash: str) -> None:
        user.password_hash = password_hash
        session.add(user)
        session.commit()
