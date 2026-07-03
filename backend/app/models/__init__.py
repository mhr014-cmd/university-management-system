"""
Model registry — importing this package registers every implemented model
on Base.metadata, which Alembic's autogenerate (backend/alembic/env.py)
depends on. Add each model's import here as its milestone lands; models
not yet implemented (still placeholder modules) are not imported.
"""

from app.models.course import Course  # noqa: F401
from app.models.department import Department  # noqa: F401
from app.models.room import Room  # noqa: F401
from app.models.semester import Semester  # noqa: F401
