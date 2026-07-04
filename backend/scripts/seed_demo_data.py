"""
Seed script: populates development/demo data (Milestone 11).

Implements docs/Database_Design.md Section 11's seed data requirements —
the "clean" baseline profile (items 1-10, 12-19). Item 11's intentional
schedule conflict is deliberately NOT seeded here (per that section's own
note to keep it out of the demo dataset); schedule-conflict behavior is
already covered by backend/tests/unit/test_schedule_service.py and
backend/tests/integration/test_schedule_router.py.

Usage (from backend/, with the venv active, against a database that has
already been migrated to head):
    python -m scripts.seed_demo_data

Reads no credentials from anywhere except the already-configured
DATABASE_URL (via app.db.session) — this script never touches any .env
file (CLAUDE.md Section 8/14 item 13). Idempotent: if the "Computer
Science" department already exists, assumes the seed has already run and
exits without creating duplicates, same idempotency pattern as
seed_admin.py.

Writes directly via the ORM session, not through the service layer — this
mirrors seed_admin.py's own precedent (a one-off data-population script is
not a request the API layer needs to authorize or validate; it runs with
the same trust level as a migration).
"""

import sys
from datetime import date, datetime, time, timedelta, timezone

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.admin import Admin
from app.models.answer import Answer
from app.models.attendance_record import AttendanceRecord
from app.models.class_session import ClassSession
from app.models.course import Course
from app.models.department import Department
from app.models.enrollment import Enrollment
from app.models.exam import Exam
from app.models.exam_submission import ExamSubmission
from app.models.fee_structure import FeeStructure
from app.models.invoice import Invoice
from app.models.notification import Notification
from app.models.parent import Parent
from app.models.parent_student_link import ParentStudentLink
from app.models.payment import Payment
from app.models.question import Question
from app.models.question_grade import QuestionGrade
from app.models.question_option import QuestionOption
from app.models.result import Result
from app.models.room import Room
from app.models.schedule_entry import ScheduleEntry
from app.models.semester import Semester
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.user import User

PAST_SEMESTER_START = date(2025, 9, 1)
PAST_SEMESTER_END = date(2025, 12, 20)
CURRENT_SEMESTER_START = date(2026, 1, 5)
CURRENT_SEMESTER_END = date(2026, 5, 15)


def _user(session, email: str, password: str, role: str) -> User:
    user = User(email=email, password_hash=hash_password(password), role=role)
    session.add(user)
    session.flush()
    return user


def main() -> int:
    session = SessionLocal()
    try:
        if session.query(Department).filter_by(name="Computer Science").first() is not None:
            print("Seed data already present (found 'Computer Science' department) — nothing to do.")
            return 0

        # --- 1. Departments -------------------------------------------------
        cs = Department(name="Computer Science", code="CS")
        ba = Department(name="Business Administration", code="BA")
        session.add_all([cs, ba])
        session.flush()

        # --- 2. Semesters ----------------------------------------------------
        past_semester = Semester(name="Fall 2025", start_date=PAST_SEMESTER_START, end_date=PAST_SEMESTER_END)
        current_semester = Semester(
            name="Spring 2026", start_date=CURRENT_SEMESTER_START, end_date=CURRENT_SEMESTER_END
        )
        session.add_all([past_semester, current_semester])
        session.flush()

        # --- 3. Rooms ----------------------------------------------------------
        rooms = [
            Room(name="Room 101", building="Main", capacity=30),
            Room(name="Room 102", building="Main", capacity=25),
            Room(name="Lab A", building="Annex", capacity=20),
            Room(name="Lab B", building="Annex", capacity=20),
        ]
        session.add_all(rooms)
        session.flush()

        # --- 4. Admin ------------------------------------------------------
        admin_user = _user(session, "admin@ictedu.example", "DemoAdmin123!", "admin")
        admin = Admin(user_id=admin_user.id, first_name="Ayesha", last_name="Rahman")
        session.add(admin)
        session.flush()

        # --- 5. Teachers ------------------------------------------------------
        teacher_specs = [
            ("teacher1@ictedu.example", "Karim", "Hossain", cs),
            ("teacher2@ictedu.example", "Nusrat", "Jahan", cs),
            ("teacher3@ictedu.example", "Farid", "Ahmed", ba),
        ]
        teachers = []
        for email, first, last, dept in teacher_specs:
            user = _user(session, email, "DemoTeacher123!", "teacher")
            teacher = Teacher(user_id=user.id, department_id=dept.id, first_name=first, last_name=last)
            session.add(teacher)
            session.flush()
            teachers.append(teacher)
        teacher_cs_1, teacher_cs_2, teacher_ba_1 = teachers

        # --- 6. Students ------------------------------------------------------
        student_specs = [
            ("student1@ictedu.example", "Sami", "Islam", cs),
            ("student2@ictedu.example", "Tania", "Akter", cs),
            ("student3@ictedu.example", "Rafiq", "Chowdhury", cs),
            ("student4@ictedu.example", "Mim", "Sultana", cs),
            ("student5@ictedu.example", "Nabil", "Hasan", ba),
            ("student6@ictedu.example", "Priya", "Das", ba),
            ("student7@ictedu.example", "Zayan", "Karim", ba),
            ("student8@ictedu.example", "Anika", "Rahman", ba),
        ]
        students = []
        for email, first, last, dept in student_specs:
            user = _user(session, email, "DemoStudent123!", "student")
            student = Student(
                user_id=user.id, department_id=dept.id, first_name=first, last_name=last,
                enrollment_date=PAST_SEMESTER_START,
            )
            session.add(student)
            session.flush()
            students.append(student)
        (
            student_low_attendance,
            student_overdue_fee,
            student_cs_3,
            student_cs_4,
            student_ba_1,
            student_ba_2,
            student_ba_3,
            student_ba_4,
        ) = students

        # --- 7. Parents ---------------------------------------------------
        parent1_user = _user(session, "parent1@ictedu.example", "DemoParent123!", "parent")
        parent1 = Parent(user_id=parent1_user.id, first_name="Habib", last_name="Islam")
        parent2_user = _user(session, "parent2@ictedu.example", "DemoParent123!", "parent")
        parent2 = Parent(user_id=parent2_user.id, first_name="Rina", last_name="Das")
        session.add_all([parent1, parent2])
        session.flush()

        # parent1 linked to a single child; parent2 linked to two children
        # (exercises the M:N parent_student_link relationship).
        session.add_all(
            [
                ParentStudentLink(parent_id=parent1.id, student_id=student_low_attendance.id),
                ParentStudentLink(parent_id=parent2.id, student_id=student_ba_1.id),
                ParentStudentLink(parent_id=parent2.id, student_id=student_ba_2.id),
            ]
        )
        session.flush()

        # --- 8. Courses -----------------------------------------------------
        course_specs = [
            ("Intro to Programming", "CS101", 3, cs),
            ("Database Systems", "CS201", 3, cs),
            ("Data Structures", "CS202", 4, cs),
            ("Principles of Management", "BA101", 3, ba),
            ("Financial Accounting", "BA201", 3, ba),
        ]
        courses = []
        for name, code, credit_hours, dept in course_specs:
            course = Course(department_id=dept.id, name=name, code=code, credit_hours=credit_hours)
            session.add(course)
            session.flush()
            courses.append(course)
        course_intro_prog, course_db_systems, course_data_structures, course_mgmt, course_accounting = courses

        # --- 9. Class sessions (current semester, one section per course) ---
        class_session_specs = [
            (course_intro_prog, teacher_cs_1),
            (course_db_systems, teacher_cs_2),
            (course_data_structures, teacher_cs_1),
            (course_mgmt, teacher_ba_1),
            (course_accounting, teacher_ba_1),
        ]
        class_sessions = []
        for course, teacher in class_session_specs:
            cs_row = ClassSession(
                course_id=course.id, teacher_id=teacher.id, semester_id=current_semester.id, section_label="A"
            )
            session.add(cs_row)
            session.flush()
            class_sessions.append(cs_row)
        (
            cs_intro_prog,
            cs_db_systems,
            cs_data_structures,
            cs_mgmt,
            cs_accounting,
        ) = class_sessions

        # A past-semester class session too, so Results has a closed
        # semester to attach published results to.
        cs_intro_prog_past = ClassSession(
            course_id=course_intro_prog.id, teacher_id=teacher_cs_1.id, semester_id=past_semester.id,
            section_label="A",
        )
        session.add(cs_intro_prog_past)
        session.flush()

        # --- 10. Enrollments --------------------------------------------------
        cs_students = [student_low_attendance, student_overdue_fee, student_cs_3, student_cs_4]
        ba_students = [student_ba_1, student_ba_2, student_ba_3, student_ba_4]
        for student in cs_students:
            session.add(Enrollment(student_id=student.id, class_session_id=cs_intro_prog.id))
            session.add(Enrollment(student_id=student.id, class_session_id=cs_db_systems.id))
            session.add(Enrollment(student_id=student.id, class_session_id=cs_intro_prog_past.id))
        for student in ba_students:
            session.add(Enrollment(student_id=student.id, class_session_id=cs_mgmt.id))
            session.add(Enrollment(student_id=student.id, class_session_id=cs_accounting.id))
        session.flush()

        # --- 11. Schedule entries (one per current-semester class session) --
        session.add_all(
            [
                ScheduleEntry(
                    class_session_id=cs_intro_prog.id, room_id=rooms[0].id, teacher_id=teacher_cs_1.id,
                    day_of_week="Mon", start_time=time(9, 0), end_time=time(10, 0),
                ),
                ScheduleEntry(
                    class_session_id=cs_db_systems.id, room_id=rooms[1].id, teacher_id=teacher_cs_2.id,
                    day_of_week="Tue", start_time=time(10, 0), end_time=time(11, 0),
                ),
                ScheduleEntry(
                    class_session_id=cs_data_structures.id, room_id=rooms[2].id, teacher_id=teacher_cs_1.id,
                    day_of_week="Wed", start_time=time(9, 0), end_time=time(10, 30),
                ),
                ScheduleEntry(
                    class_session_id=cs_mgmt.id, room_id=rooms[3].id, teacher_id=teacher_ba_1.id,
                    day_of_week="Mon", start_time=time(11, 0), end_time=time(12, 0),
                ),
                ScheduleEntry(
                    class_session_id=cs_accounting.id, room_id=rooms[3].id, teacher_id=teacher_ba_1.id,
                    day_of_week="Thu", start_time=time(11, 0), end_time=time(12, 0),
                ),
            ]
        )
        session.flush()

        # --- 12/13. Exams + Questions/Options, one per lifecycle state -----
        exam_draft = Exam(
            class_session_id=cs_intro_prog.id, created_by_teacher_id=teacher_cs_1.id, title="Quiz 1 (Draft)",
            exam_type="mcq", time_limit_minutes=20, status="draft",
        )
        exam_scheduled = Exam(
            class_session_id=cs_db_systems.id, created_by_teacher_id=teacher_cs_2.id, title="Midterm (Scheduled)",
            exam_type="written", time_limit_minutes=60, status="scheduled",
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        exam_open = Exam(
            class_session_id=cs_data_structures.id, created_by_teacher_id=teacher_cs_1.id, title="Quiz 2 (Open)",
            exam_type="mixed", time_limit_minutes=30, status="open",
        )
        exam_published = Exam(
            class_session_id=cs_intro_prog_past.id, created_by_teacher_id=teacher_cs_1.id, title="Final Exam",
            exam_type="mcq", time_limit_minutes=45, status="published",
        )
        session.add_all([exam_draft, exam_scheduled, exam_open, exam_published])
        session.flush()

        q_draft = Question(
            exam_id=exam_draft.id, question_text="What is a variable?", question_type="short_answer",
            marks=5, order_index=0,
        )
        session.add(q_draft)

        q_scheduled_1 = Question(
            exam_id=exam_scheduled.id, question_text="Explain database normalization.", question_type="descriptive",
            marks=10, order_index=0,
        )
        q_scheduled_2 = Question(
            exam_id=exam_scheduled.id, question_text="Write a SQL query to join two tables.",
            question_type="coding", marks=10, order_index=1,
        )
        session.add_all([q_scheduled_1, q_scheduled_2])

        q_open = Question(
            exam_id=exam_open.id, question_text="A stack is LIFO.", question_type="mcq", marks=5, order_index=0,
        )
        session.add(q_open)
        session.flush()
        q_open_opt_true = QuestionOption(question_id=q_open.id, option_text="True", is_correct=True)
        q_open_opt_false = QuestionOption(question_id=q_open.id, option_text="False", is_correct=False)
        session.add_all([q_open_opt_true, q_open_opt_false])

        q_published = Question(
            exam_id=exam_published.id, question_text="2 + 2 = ?", question_type="mcq", marks=5, order_index=0,
        )
        session.add(q_published)
        session.flush()
        q_published_opt_correct = QuestionOption(question_id=q_published.id, option_text="4", is_correct=True)
        q_published_opt_wrong = QuestionOption(question_id=q_published.id, option_text="3", is_correct=False)
        session.add_all([q_published_opt_correct, q_published_opt_wrong])
        session.flush()

        # --- 14. ExamSubmissions/Answers/QuestionGrades ---------------------
        now = datetime.now(timezone.utc)

        # Fully graded submission (backs the published Result below).
        submission_graded = ExamSubmission(
            exam_id=exam_published.id, student_id=student_low_attendance.id, started_at=now - timedelta(days=90),
            submitted_at=now - timedelta(days=90) + timedelta(minutes=10), status="graded",
        )
        session.add(submission_graded)
        session.flush()
        answer_graded = Answer(
            submission_id=submission_graded.id, question_id=q_published.id,
            selected_option_id=q_published_opt_correct.id,
        )
        session.add(answer_graded)
        session.flush()
        session.add(
            QuestionGrade(
                answer_id=answer_graded.id, graded_by_teacher_id=teacher_cs_1.id, awarded_marks=5,
                feedback="Correct.", graded_at=now - timedelta(days=89),
            )
        )

        # Ungraded/pending submission on the still-open exam.
        submission_pending = ExamSubmission(
            exam_id=exam_open.id, student_id=student_cs_3.id, started_at=now - timedelta(minutes=20),
            submitted_at=now - timedelta(minutes=5), status="submitted",
        )
        session.add(submission_pending)
        session.flush()
        session.add(Answer(submission_id=submission_pending.id, question_id=q_open.id, selected_option_id=q_open_opt_true.id))
        session.flush()

        # --- 15. AttendanceRecords -------------------------------------------
        # student_low_attendance: enough absences to cross below the 80%
        # warning threshold (Requirement_Analysis.md §14 item 4, resolved
        # Milestone 5) on cs_intro_prog. 3 present + 3 absent = 50%.
        attendance_dates = [PAST_SEMESTER_START + timedelta(weeks=w) for w in range(6)]
        for i, day in enumerate(attendance_dates):
            status = "present" if i < 3 else "absent"
            session.add(
                AttendanceRecord(
                    student_id=student_low_attendance.id, class_session_id=cs_intro_prog.id,
                    marked_by_teacher_id=teacher_cs_1.id, attendance_date=day, status=status,
                )
            )
        # A healthy attendance history for the other CS students.
        for student in (student_overdue_fee, student_cs_3, student_cs_4):
            for day in attendance_dates:
                session.add(
                    AttendanceRecord(
                        student_id=student.id, class_session_id=cs_intro_prog.id,
                        marked_by_teacher_id=teacher_cs_1.id, attendance_date=day, status="present",
                    )
                )
        session.flush()

        # --- 16. Results: submitted, published, rejected --------------------
        session.add(
            Result(
                student_id=student_low_attendance.id, course_id=course_intro_prog.id, semester_id=past_semester.id,
                exam_id=exam_published.id, submitted_by_teacher_id=teacher_cs_1.id, approved_by_admin_id=admin.id,
                grade_letter="A", grade_point=4.0, status="published",
                submitted_at=now - timedelta(days=89), approved_at=now - timedelta(days=88),
            )
        )
        session.add(
            Result(
                student_id=student_cs_3.id, course_id=course_db_systems.id, semester_id=current_semester.id,
                exam_id=None, submitted_by_teacher_id=teacher_cs_2.id, approved_by_admin_id=None,
                grade_letter="B", grade_point=3.0, status="submitted", submitted_at=now - timedelta(days=1),
            )
        )
        session.add(
            Result(
                student_id=student_cs_4.id, course_id=course_data_structures.id, semester_id=current_semester.id,
                exam_id=None, submitted_by_teacher_id=teacher_cs_1.id, approved_by_admin_id=admin.id,
                grade_letter="D", grade_point=1.0, status="rejected",
                submitted_at=now - timedelta(days=5), approved_at=now - timedelta(days=4),
            )
        )
        session.flush()

        # --- 17. FeeStructures (one per department/semester combination) ---
        fee_cs_current = FeeStructure(
            department_id=cs.id, semester_id=current_semester.id, name="CS Tuition — Spring 2026", amount=15000,
            due_date=current_semester.start_date + timedelta(days=30),
        )
        fee_ba_current = FeeStructure(
            department_id=ba.id, semester_id=current_semester.id, name="BA Tuition — Spring 2026", amount=12000,
            due_date=current_semester.start_date + timedelta(days=30),
        )
        fee_cs_past_overdue = FeeStructure(
            department_id=cs.id, semester_id=past_semester.id, name="CS Tuition — Fall 2025", amount=14000,
            due_date=PAST_SEMESTER_START + timedelta(days=30),
        )
        session.add_all([fee_cs_current, fee_ba_current, fee_cs_past_overdue])
        session.flush()

        # --- 18. Payments/Invoices: fully paid, partially paid, overdue -----
        # Fully paid: student_cs_3 pays fee_cs_current in full.
        invoice_paid = Invoice(
            student_id=student_cs_3.id, fee_structure_id=fee_cs_current.id, status="paid", issued_at=now,
        )
        session.add(invoice_paid)
        session.add(
            Payment(
                student_id=student_cs_3.id, fee_structure_id=fee_cs_current.id, recorded_by_admin_id=admin.id,
                amount=15000, payment_date=now, payment_method="bank_transfer",
            )
        )

        # Partially paid: student_cs_4 pays half of fee_cs_current.
        invoice_partial = Invoice(
            student_id=student_cs_4.id, fee_structure_id=fee_cs_current.id, status="partially_paid", issued_at=now,
        )
        session.add(invoice_partial)
        session.add(
            Payment(
                student_id=student_cs_4.id, fee_structure_id=fee_cs_current.id, recorded_by_admin_id=admin.id,
                amount=7500, payment_date=now, payment_method="cash",
            )
        )

        # Overdue: student_overdue_fee has an unpaid invoice on the past,
        # already-due fee structure — no payment recorded at all.
        invoice_overdue = Invoice(
            student_id=student_overdue_fee.id, fee_structure_id=fee_cs_past_overdue.id, status="unpaid",
            issued_at=datetime.combine(PAST_SEMESTER_START, datetime.min.time(), tzinfo=timezone.utc),
        )
        session.add(invoice_overdue)
        session.flush()

        # --- 19. Notifications: one per type, mixed read/unread -------------
        session.add_all(
            [
                Notification(
                    user_id=admin_user.id, type="result_published", message="Result published: DB Systems Fall 2025",
                    is_read=False,
                ),
                Notification(
                    user_id=teachers[0].user_id, type="schedule_change",
                    message="Schedule change: Intro to Programming moved to Room 101", is_read=True,
                ),
                Notification(
                    user_id=parent1_user.id, type="attendance_warning",
                    message="Attendance warning: Intro to Programming below 80%", is_read=False,
                ),
                Notification(
                    user_id=parent1_user.id, type="fee_due", message="Fee due: 14000.00 due 2025-10-01",
                    is_read=True,
                ),
            ]
        )

        session.commit()
        print("Seed data created successfully.")
        print(f"  Admin login: admin@ictedu.example / DemoAdmin123!")
        print(f"  Teacher login: teacher1@ictedu.example / DemoTeacher123!")
        print(f"  Student login: student1@ictedu.example / DemoStudent123! (low attendance, published result)")
        print(f"  Parent login: parent1@ictedu.example / DemoParent123! (linked to student1)")
        return 0
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
