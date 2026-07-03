"""
Model registry — importing this package registers every implemented model
on Base.metadata, which Alembic's autogenerate (backend/alembic/env.py)
depends on. Add each model's import here as its milestone lands; models
not yet implemented (still placeholder modules) are not imported.
"""

from app.models.admin import Admin  # noqa: F401
from app.models.class_session import ClassSession  # noqa: F401
from app.models.course import Course  # noqa: F401
from app.models.department import Department  # noqa: F401
from app.models.enrollment import Enrollment  # noqa: F401
from app.models.parent import Parent  # noqa: F401
from app.models.parent_student_link import ParentStudentLink  # noqa: F401
from app.models.room import Room  # noqa: F401
from app.models.schedule_change_request import ScheduleChangeRequest  # noqa: F401
from app.models.schedule_entry import ScheduleEntry  # noqa: F401
from app.models.semester import Semester  # noqa: F401
from app.models.student import Student  # noqa: F401
from app.models.teacher import Teacher  # noqa: F401
from app.models.user import User  # noqa: F401
