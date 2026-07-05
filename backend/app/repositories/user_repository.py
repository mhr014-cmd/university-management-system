"""
Data access repository: user (and role-profile tables — student, teacher,
parent, admin).

All SQLAlchemy queries for the `user` table and its 1:1 role-profile
tables live here, per CLAUDE.md §6. Milestone 3 extends this same module
(rather than adding student_repository.py/teacher_repository.py) per the
design already established by this file's Milestone 2 docstring and
Implementation_Roadmap.md's Milestone 3 file list, which names only this
one repository file for the whole user domain.

No transaction commits for the create/update methods below — the service
layer owns transaction boundaries (e.g. creating a `user` row and its
profile row atomically), per CLAUDE.md §6. `session.flush()` is used
instead, so generated defaults (id, timestamps) are available to the
caller without ending the transaction.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.admin import Admin
from app.models.parent import Parent
from app.models.parent_student_link import ParentStudentLink
from app.models.student import Student
from app.models.teacher import Teacher
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

    def create_user(self, session: Session, *, email: str, password_hash: str, role: str) -> User:
        user = User(email=email, password_hash=password_hash, role=role)
        session.add(user)
        session.flush()
        return user

    # --- student -----------------------------------------------------

    def get_student_profile_by_user_id(self, session: Session, user_id: uuid.UUID) -> Student | None:
        return session.scalar(select(Student).where(Student.user_id == user_id))

    def get_student_with_user(self, session: Session, student_id: uuid.UUID) -> tuple[Student, User] | None:
        row = session.execute(
            select(Student, User).join(User, Student.user_id == User.id).where(Student.id == student_id)
        ).first()
        return (row[0], row[1]) if row else None

    def list_students_with_user(
        self, session: Session, page: int, page_size: int, department_id: uuid.UUID | None = None
    ) -> tuple[list[tuple[Student, User]], int]:
        stmt = select(Student, User).join(User, Student.user_id == User.id)
        if department_id is not None:
            stmt = stmt.where(Student.department_id == department_id)
        stmt = stmt.order_by(Student.last_name, Student.first_name)
        total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = session.execute(stmt.offset((page - 1) * page_size).limit(page_size)).all()
        return [(row[0], row[1]) for row in rows], total

    def list_students_by_ids(self, session: Session, student_ids: list[uuid.UUID]) -> list[Student]:
        """Batch name lookup for a set of student IDs — one query regardless
        of how many IDs are passed, so callers building a display-name map
        for a report/list response never fall into a per-row N+1 pattern."""
        if not student_ids:
            return []
        return list(session.scalars(select(Student).where(Student.id.in_(student_ids))))

    def create_student(
        self,
        session: Session,
        *,
        user_id: uuid.UUID,
        department_id: uuid.UUID,
        first_name: str,
        last_name: str,
        enrollment_date: date,
    ) -> Student:
        student = Student(
            user_id=user_id,
            department_id=department_id,
            first_name=first_name,
            last_name=last_name,
            enrollment_date=enrollment_date,
        )
        session.add(student)
        session.flush()
        return student

    # --- teacher -------------------------------------------------------

    def get_teacher_profile_by_user_id(self, session: Session, user_id: uuid.UUID) -> Teacher | None:
        return session.scalar(select(Teacher).where(Teacher.user_id == user_id))

    def get_teacher_with_user(self, session: Session, teacher_id: uuid.UUID) -> tuple[Teacher, User] | None:
        row = session.execute(
            select(Teacher, User).join(User, Teacher.user_id == User.id).where(Teacher.id == teacher_id)
        ).first()
        return (row[0], row[1]) if row else None

    def list_teachers_with_user(
        self, session: Session, page: int, page_size: int, department_id: uuid.UUID | None = None
    ) -> tuple[list[tuple[Teacher, User]], int]:
        stmt = select(Teacher, User).join(User, Teacher.user_id == User.id)
        if department_id is not None:
            stmt = stmt.where(Teacher.department_id == department_id)
        stmt = stmt.order_by(Teacher.last_name, Teacher.first_name)
        total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = session.execute(stmt.offset((page - 1) * page_size).limit(page_size)).all()
        return [(row[0], row[1]) for row in rows], total

    def create_teacher(
        self,
        session: Session,
        *,
        user_id: uuid.UUID,
        department_id: uuid.UUID,
        first_name: str,
        last_name: str,
        hire_date: date | None,
    ) -> Teacher:
        teacher = Teacher(
            user_id=user_id,
            department_id=department_id,
            first_name=first_name,
            last_name=last_name,
            hire_date=hire_date,
        )
        session.add(teacher)
        session.flush()
        return teacher

    # --- parent / admin (read-only in Milestone 3 — see app/models/parent.py) --

    def get_parent_profile_by_user_id(self, session: Session, user_id: uuid.UUID) -> Parent | None:
        return session.scalar(select(Parent).where(Parent.user_id == user_id))

    def get_admin_profile_by_user_id(self, session: Session, user_id: uuid.UUID) -> Admin | None:
        return session.scalar(select(Admin).where(Admin.user_id == user_id))

    def parent_has_linked_student(self, session: Session, parent_id: uuid.UUID, student_id: uuid.UUID) -> bool:
        # BR-007/NFR-003: a Parent's data access is scoped strictly to
        # their own linked child/children — used by Milestone 5's
        # GET /attendance/{classId} Parent-scoped ownership check.
        return (
            session.scalar(
                select(ParentStudentLink.id).where(
                    ParentStudentLink.parent_id == parent_id, ParentStudentLink.student_id == student_id
                )
            )
            is not None
        )

    def list_parent_user_ids_for_student(self, session: Session, student_id: uuid.UUID) -> list[uuid.UUID]:
        # Reverse of parent_has_linked_student — used by Milestone 9's
        # notification dispatcher to fan out a fee_due notification to
        # every Parent linked to the invoiced student.
        stmt = (
            select(Parent.user_id)
            .join(ParentStudentLink, ParentStudentLink.parent_id == Parent.id)
            .where(ParentStudentLink.student_id == student_id)
        )
        return list(session.scalars(stmt))

    def list_linked_students(self, session: Session, parent_id: uuid.UUID) -> list[Student]:
        """All students linked to a given Parent (production-polish audit:
        backs GET /users/me/children, so the Parent Dashboard/Portal can
        show linked children by name instead of requiring a manually
        typed student_id)."""
        stmt = (
            select(Student)
            .join(ParentStudentLink, ParentStudentLink.student_id == Student.id)
            .where(ParentStudentLink.parent_id == parent_id)
            .order_by(Student.first_name, Student.last_name)
        )
        return list(session.scalars(stmt))
