"""
Shared helper: human-readable report-scope labels (Department/Semester/
Student), for PDF/Excel export headers.

`attendance_service.AttendanceService.get_report_scope_labels` already
implements this exact resolution for the Attendance report export
(Version 1.2 reporting infrastructure) — left untouched per CLAUDE.md's
"no unnecessary refactoring" rule rather than retrofitted to call this
module. This standalone function exists so the Results/Fees report
exports (added later, reusing the same PDF/Excel scaffolding in
app/pdf/shared.py and app/excel/shared.py) can share identical label
logic without duplicating it a second time inline.
"""

import uuid

from sqlalchemy.orm import Session

from app.repositories.reference_data_repository import DepartmentRepository, SemesterRepository
from app.repositories.user_repository import UserRepository

department_repo = DepartmentRepository()
semester_repo = SemesterRepository()
user_repo = UserRepository()


def resolve_scope_labels(
    session: Session,
    *,
    department_id: uuid.UUID | None,
    semester_id: uuid.UUID | None,
    student_id: uuid.UUID | None,
) -> dict[str, str]:
    department_label = "All Departments"
    if department_id is not None:
        department = department_repo.get(session, department_id)
        if department is not None:
            department_label = department.name

    semester_label = "All Semesters"
    if semester_id is not None:
        semester = semester_repo.get(session, semester_id)
        if semester is not None:
            semester_label = semester.name

    student_label = "All Students"
    if student_id is not None:
        row = user_repo.get_student_with_user(session, student_id)
        if row is not None:
            student, _user = row
            student_label = f"{student.first_name} {student.last_name}"

    return {"department": department_label, "semester": semester_label, "student": student_label}
