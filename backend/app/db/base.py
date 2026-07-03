"""
SQLAlchemy declarative base.

All ORM models (Milestone 1+) inherit from `Base` so Alembic's autogenerate
can discover them via `Base.metadata` (see backend/alembic/env.py).
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
