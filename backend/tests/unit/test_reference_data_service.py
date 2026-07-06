"""
Unit tests: app.services.reference_data_service — DepartmentService,
CourseService, RoomService, SemesterService update()/delete() (Version
2.3 — Academic Setup; list/create were already covered indirectly via
tests/integration/test_reference_data_rbac.py, but this domain never had
a dedicated unit test file until now).

Runs against a real (disposable, SAVEPOINT-isolated) database session —
see tests/conftest.py — since these methods are thin enough that the
value is in exercising the real IntegrityError -> 409 translation and the
real ON DELETE RESTRICT behavior, not in mocking the repository layer.
"""

from datetime import date

import pytest
from fastapi import HTTPException

from tests.conftest import requires_test_database

from app.schemas.course import CourseUpdate
from app.schemas.department import DepartmentUpdate
from app.schemas.room import RoomUpdate
from app.schemas.semester import SemesterUpdate
from app.services.reference_data_service import CourseService, DepartmentService, RoomService, SemesterService

pytestmark = requires_test_database

department_service = DepartmentService()
course_service = CourseService()
room_service = RoomService()
semester_service = SemesterService()


class TestDepartmentUpdate:
    def test_updates_name_and_code(self, db_session, make_department):
        department = make_department(name="Old Name", code="OLD")
        updated = department_service.update(db_session, department.id, DepartmentUpdate(name="New Name", code="NEW"))
        assert updated.name == "New Name"
        assert updated.code == "NEW"

    def test_partial_update_leaves_other_field_untouched(self, db_session, make_department):
        department = make_department(name="Keep Name", code="OLD2")
        updated = department_service.update(db_session, department.id, DepartmentUpdate(code="NEW2"))
        assert updated.name == "Keep Name"
        assert updated.code == "NEW2"

    def test_duplicate_code_returns_409(self, db_session, make_department):
        make_department(name="Existing", code="DUPCODE")
        target = make_department(name="Target", code="OTHERCODE")
        with pytest.raises(HTTPException) as exc:
            department_service.update(db_session, target.id, DepartmentUpdate(code="DUPCODE"))
        assert exc.value.status_code == 409

    def test_unknown_id_returns_404(self, db_session):
        import uuid

        with pytest.raises(HTTPException) as exc:
            department_service.update(db_session, uuid.uuid4(), DepartmentUpdate(name="X"))
        assert exc.value.status_code == 404


class TestDepartmentDelete:
    def test_deletes_unreferenced_department(self, db_session, make_department):
        department = make_department()
        department_service.delete(db_session, department.id)
        assert department_service.list(db_session, 1, 20)[1] >= 0  # no error; row is gone
        with pytest.raises(HTTPException) as exc:
            department_service.get(db_session, department.id)
        assert exc.value.status_code == 404

    def test_referenced_department_returns_409(self, db_session, make_department, make_course):
        department = make_department()
        make_course(department=department)
        with pytest.raises(HTTPException) as exc:
            department_service.delete(db_session, department.id)
        assert exc.value.status_code == 409


class TestCourseUpdate:
    def test_updates_fields(self, db_session, make_course):
        course = make_course(name="Old Course", code="OLDC", credit_hours=3)
        updated = course_service.update(
            db_session, course.id, CourseUpdate(name="New Course", code="NEWC", credit_hours=4)
        )
        assert updated.name == "New Course"
        assert updated.code == "NEWC"
        assert updated.credit_hours == 4

    def test_invalid_department_id_returns_422(self, db_session, make_course):
        import uuid

        course = make_course()
        with pytest.raises(HTTPException) as exc:
            course_service.update(db_session, course.id, CourseUpdate(department_id=uuid.uuid4()))
        assert exc.value.status_code == 422

    def test_duplicate_code_returns_409(self, db_session, make_course):
        make_course(code="DUPCOURSE")
        target = make_course(code="OTHERCOURSE")
        with pytest.raises(HTTPException) as exc:
            course_service.update(db_session, target.id, CourseUpdate(code="DUPCOURSE"))
        assert exc.value.status_code == 409


class TestCourseDelete:
    def test_deletes_unreferenced_course(self, db_session, make_course):
        course = make_course()
        course_service.delete(db_session, course.id)
        with pytest.raises(HTTPException) as exc:
            course_service.get(db_session, course.id)
        assert exc.value.status_code == 404

    def test_referenced_course_returns_409(self, db_session, make_course, make_class_session, make_teacher_user):
        course = make_course()
        _teacher_user, teacher = make_teacher_user("course-delete-teacher@example.com", "some-password")
        make_class_session(course=course, teacher=teacher)
        with pytest.raises(HTTPException) as exc:
            course_service.delete(db_session, course.id)
        assert exc.value.status_code == 409


class TestRoomUpdate:
    def test_updates_fields(self, db_session, make_room):
        room = make_room(name="Old Room", building="Old Building", capacity=10)
        updated = room_service.update(
            db_session, room.id, RoomUpdate(name="New Room", building="New Building", capacity=20)
        )
        assert updated.name == "New Room"
        assert updated.building == "New Building"
        assert updated.capacity == 20

    def test_duplicate_name_returns_409(self, db_session, make_room):
        make_room(name="DupRoom")
        target = make_room(name="OtherRoom")
        with pytest.raises(HTTPException) as exc:
            room_service.update(db_session, target.id, RoomUpdate(name="DupRoom"))
        assert exc.value.status_code == 409


class TestRoomDelete:
    def test_deletes_unreferenced_room(self, db_session, make_room):
        room = make_room()
        room_service.delete(db_session, room.id)
        with pytest.raises(HTTPException) as exc:
            room_service.get(db_session, room.id)
        assert exc.value.status_code == 404

    def test_referenced_room_returns_409(
        self, db_session, make_room, make_class_session, make_schedule_entry, make_teacher_user
    ):
        room = make_room()
        _teacher_user, teacher = make_teacher_user("room-delete-teacher@example.com", "some-password")
        class_session = make_class_session(teacher=teacher)
        make_schedule_entry(class_session, teacher, room=room)
        with pytest.raises(HTTPException) as exc:
            room_service.delete(db_session, room.id)
        assert exc.value.status_code == 409


class TestSemesterUpdate:
    def test_updates_fields(self, db_session, make_semester):
        semester = make_semester(name="Old Semester", start_date=date(2026, 1, 1), end_date=date(2026, 4, 1))
        updated = semester_service.update(
            db_session, semester.id, SemesterUpdate(name="New Semester", start_date=date(2026, 2, 1))
        )
        assert updated.name == "New Semester"
        assert updated.start_date == date(2026, 2, 1)
        assert updated.end_date == date(2026, 4, 1)  # untouched

    def test_start_after_existing_end_returns_422(self, db_session, make_semester):
        semester = make_semester(start_date=date(2026, 1, 1), end_date=date(2026, 4, 1))
        with pytest.raises(HTTPException) as exc:
            semester_service.update(db_session, semester.id, SemesterUpdate(start_date=date(2026, 5, 1)))
        assert exc.value.status_code == 422

    def test_duplicate_name_returns_409(self, db_session, make_semester):
        make_semester(name="DupSemester")
        target = make_semester(name="OtherSemester")
        with pytest.raises(HTTPException) as exc:
            semester_service.update(db_session, target.id, SemesterUpdate(name="DupSemester"))
        assert exc.value.status_code == 409


class TestSemesterDelete:
    def test_deletes_unreferenced_semester(self, db_session, make_semester):
        semester = make_semester()
        semester_service.delete(db_session, semester.id)
        with pytest.raises(HTTPException) as exc:
            semester_service.get(db_session, semester.id)
        assert exc.value.status_code == 404

    def test_referenced_semester_returns_409(self, db_session, make_semester, make_class_session, make_teacher_user):
        semester = make_semester()
        _teacher_user, teacher = make_teacher_user("semester-delete-teacher@example.com", "some-password")
        make_class_session(semester=semester, teacher=teacher)
        with pytest.raises(HTTPException) as exc:
            semester_service.delete(db_session, semester.id)
        assert exc.value.status_code == 409
