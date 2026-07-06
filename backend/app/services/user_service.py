"""
Business logic service: user profiles and Admin-driven account lifecycle
(see docs/Requirement_Analysis.md FR-006–FR-016, VR-001, VR-009, BR-006).

Calls UserRepository/DepartmentRepository, never the ORM session directly,
per CLAUDE.md §6.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.user import User
from app.repositories.reference_data_repository import DepartmentRepository
from app.repositories.schedule_repository import ScheduleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.student import StudentCreate, StudentRead, StudentUpdate
from app.schemas.teacher import TeacherCreate, TeacherRead, TeacherUpdate
from app.schemas.user import ChildEntry, MeRead, MeUpdate, MyChildrenResponse, UserProfile

user_repo = UserRepository()
department_repo = DepartmentRepository()
schedule_repo = ScheduleRepository()

_STUDENT_NOT_FOUND = "Student not found"
_TEACHER_NOT_FOUND = "Teacher not found"
_INVALID_DEPARTMENT = "department_id does not reference an existing department"


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def _forbidden(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _invalid_department() -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=_INVALID_DEPARTMENT)


def _duplicate_email() -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists.")


def _student_to_read(student: Student, user: User) -> StudentRead:
    return StudentRead(
        id=student.id,
        user_id=user.id,
        email=user.email,
        first_name=student.first_name,
        last_name=student.last_name,
        department_id=student.department_id,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def _teacher_to_read(teacher: Teacher, user: User) -> TeacherRead:
    return TeacherRead(
        id=teacher.id,
        user_id=user.id,
        email=user.email,
        first_name=teacher.first_name,
        last_name=teacher.last_name,
        department_id=teacher.department_id,
        is_active=user.is_active,
        created_at=user.created_at,
    )


class UserService:
    # --- self-service profile (FR-006, FR-007, VR-009) ------------------

    def get_me(self, session: Session, user: User) -> MeRead:
        profile = self._get_own_profile(session, user)
        return MeRead(id=user.id, email=user.email, role=user.role, profile=profile)

    def update_me(self, session: Session, user: User, payload: MeUpdate) -> MeRead:
        # VR-009 is enforced structurally: MeUpdate has no role/is_active/
        # department_id field for a caller to even attempt to set — there is
        # nothing here to reject at runtime, only fields that are always safe.
        if user.role == "student":
            profile_row = user_repo.get_student_profile_by_user_id(session, user.id)
        elif user.role == "teacher":
            profile_row = user_repo.get_teacher_profile_by_user_id(session, user.id)
        elif user.role == "parent":
            profile_row = user_repo.get_parent_profile_by_user_id(session, user.id)
        else:
            profile_row = user_repo.get_admin_profile_by_user_id(session, user.id)

        if payload.first_name is not None:
            profile_row.first_name = payload.first_name
        if payload.last_name is not None:
            profile_row.last_name = payload.last_name
        # profile_photo_url only exists on student/teacher (Database_Design.md
        # §6.2/§6.3) — parent/admin (§6.4/§6.5) have no such column, so the
        # field is accepted by the schema (uniform request shape per
        # API_Contract.md §2.2) but has nowhere to persist for those two
        # roles and is silently ignored for them, documented here rather
        # than surfaced as a validation error the contract doesn't specify.
        if payload.profile_photo_url is not None and user.role in ("student", "teacher"):
            profile_row.profile_photo_url = payload.profile_photo_url

        session.add(profile_row)
        session.commit()
        session.refresh(profile_row)
        return self.get_me(session, user)

    # --- GET /users/me/children (Parent-only, production-polish audit) --

    def get_my_children(self, session: Session, user: User) -> MyChildrenResponse:
        parent = user_repo.get_parent_profile_by_user_id(session, user.id)
        students = user_repo.list_linked_students(session, parent.id)
        return MyChildrenResponse(
            children=[
                ChildEntry(
                    id=s.id, first_name=s.first_name, last_name=s.last_name, department_id=s.department_id
                )
                for s in students
            ]
        )

    def _get_own_profile(self, session: Session, user: User) -> UserProfile:
        if user.role == "student":
            student = user_repo.get_student_profile_by_user_id(session, user.id)
            department = department_repo.get(session, student.department_id)
            return UserProfile(
                first_name=student.first_name,
                last_name=student.last_name,
                profile_photo_url=student.profile_photo_url,
                department_id=student.department_id,
                department_name=department.name if department else None,
            )
        if user.role == "teacher":
            teacher = user_repo.get_teacher_profile_by_user_id(session, user.id)
            department = department_repo.get(session, teacher.department_id)
            return UserProfile(
                first_name=teacher.first_name,
                last_name=teacher.last_name,
                profile_photo_url=teacher.profile_photo_url,
                department_id=teacher.department_id,
                department_name=department.name if department else None,
            )
        if user.role == "parent":
            parent = user_repo.get_parent_profile_by_user_id(session, user.id)
            return UserProfile(first_name=parent.first_name, last_name=parent.last_name)
        admin = user_repo.get_admin_profile_by_user_id(session, user.id)
        return UserProfile(first_name=admin.first_name, last_name=admin.last_name)

    # --- Admin: student management (FR-009–FR-013) ----------------------

    def list_students(
        self, session: Session, page: int, page_size: int, department_id: uuid.UUID | None = None
    ) -> tuple[list[StudentRead], int]:
        rows, total = user_repo.list_students_with_user(session, page, page_size, department_id)
        return [_student_to_read(student, user) for student, user in rows], total

    def get_student(self, session: Session, current_user: User, student_id: uuid.UUID) -> StudentRead:
        row = user_repo.get_student_with_user(session, student_id)
        if row is None:
            raise _not_found(_STUDENT_NOT_FOUND)
        if current_user.role == "teacher":
            teacher = user_repo.get_teacher_profile_by_user_id(session, current_user.id)
            if not schedule_repo.teacher_teaches_student(session, teacher.id, student_id):
                raise _forbidden("You may only view students enrolled in one of your class sessions.")
        return _student_to_read(*row)

    def create_student(self, session: Session, payload: StudentCreate) -> StudentRead:
        if department_repo.get(session, payload.department_id) is None:
            raise _invalid_department()
        try:
            # Single transaction: user + student rows are created and
            # committed together, so a failure anywhere (e.g. duplicate
            # email) leaves neither row behind.
            user = user_repo.create_user(
                session, email=payload.email, password_hash=hash_password(payload.password.get_secret_value()), role="student"
            )
            student = user_repo.create_student(
                session,
                user_id=user.id,
                department_id=payload.department_id,
                first_name=payload.first_name,
                last_name=payload.last_name,
                enrollment_date=payload.enrollment_date,
            )
            session.commit()
        except IntegrityError:
            session.rollback()
            raise _duplicate_email()
        session.refresh(user)
        session.refresh(student)
        return _student_to_read(student, user)

    def update_student(self, session: Session, student_id: uuid.UUID, payload: StudentUpdate) -> StudentRead:
        row = user_repo.get_student_with_user(session, student_id)
        if row is None:
            raise _not_found(_STUDENT_NOT_FOUND)
        student, user = row

        if payload.department_id is not None:
            if department_repo.get(session, payload.department_id) is None:
                raise _invalid_department()
            student.department_id = payload.department_id
        if payload.first_name is not None:
            student.first_name = payload.first_name
        if payload.last_name is not None:
            student.last_name = payload.last_name
        if payload.is_active is not None:
            user.is_active = payload.is_active

        session.add(student)
        session.add(user)
        session.commit()
        session.refresh(student)
        session.refresh(user)
        return _student_to_read(student, user)

    def deactivate_student(self, session: Session, student_id: uuid.UUID) -> StudentRead:
        row = user_repo.get_student_with_user(session, student_id)
        if row is None:
            raise _not_found(_STUDENT_NOT_FOUND)
        student, user = row
        # BR-006: deactivation only, never a row deletion — historical
        # Attendance/Result/Payment records stay intact. Idempotent: calling
        # this again on an already-deactivated student is not an error
        # (chosen consistently over 409, per API_Contract.md §2.7's note
        # that either is acceptable as long as it's decided once).
        user.is_active = False
        session.add(user)
        session.commit()
        session.refresh(user)
        return _student_to_read(student, user)

    # --- Admin: teacher management (FR-014–FR-016) -----------------------

    def list_teachers(
        self, session: Session, page: int, page_size: int, department_id: uuid.UUID | None = None
    ) -> tuple[list[TeacherRead], int]:
        rows, total = user_repo.list_teachers_with_user(session, page, page_size, department_id)
        return [_teacher_to_read(teacher, user) for teacher, user in rows], total

    def create_teacher(self, session: Session, payload: TeacherCreate) -> TeacherRead:
        if department_repo.get(session, payload.department_id) is None:
            raise _invalid_department()
        try:
            user = user_repo.create_user(
                session, email=payload.email, password_hash=hash_password(payload.password.get_secret_value()), role="teacher"
            )
            teacher = user_repo.create_teacher(
                session,
                user_id=user.id,
                department_id=payload.department_id,
                first_name=payload.first_name,
                last_name=payload.last_name,
                hire_date=payload.hire_date,
            )
            session.commit()
        except IntegrityError:
            session.rollback()
            raise _duplicate_email()
        session.refresh(user)
        session.refresh(teacher)
        return _teacher_to_read(teacher, user)

    def update_teacher(self, session: Session, teacher_id: uuid.UUID, payload: TeacherUpdate) -> TeacherRead:
        row = user_repo.get_teacher_with_user(session, teacher_id)
        if row is None:
            raise _not_found(_TEACHER_NOT_FOUND)
        teacher, user = row

        if payload.department_id is not None:
            if department_repo.get(session, payload.department_id) is None:
                raise _invalid_department()
            teacher.department_id = payload.department_id
        if payload.first_name is not None:
            teacher.first_name = payload.first_name
        if payload.last_name is not None:
            teacher.last_name = payload.last_name
        if payload.is_active is not None:
            user.is_active = payload.is_active

        session.add(teacher)
        session.add(user)
        session.commit()
        session.refresh(teacher)
        session.refresh(user)
        return _teacher_to_read(teacher, user)
