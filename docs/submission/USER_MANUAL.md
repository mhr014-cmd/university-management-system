# User Manual

A walkthrough of every screen in the University Management System, organized by role. All screenshots/URLs assume the frontend is running at `http://localhost:5173`.

## Logging in

Navigate to `/login`. Enter your email and password. On success you're redirected to `/dashboard`, which renders a different view depending on your account's role. Use the eye icon in the password field to reveal/hide what you've typed.

## Demo accounts

If you ran `python -m scripts.seed_demo_data` (see [INSTALLATION.md](INSTALLATION.md)), these accounts are available:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@ictedu.example` | `DemoAdmin123!` |
| Teacher | `teacher1@ictedu.example` | `DemoTeacher123!` |
| Student | `student1@ictedu.example` | `DemoStudent123!` |
| Parent | `parent1@ictedu.example` | `DemoParent123!` |

`student1` is deliberately seeded with low attendance and a published result, to demonstrate both the warning badge and the GPA/transcript flow. `parent1` is linked to `student1`.

---

## Screens common to every role

- **Dashboard** (`/dashboard`) — role-specific summary widgets (see each role's section below).
- **Profile** (`/profile`) — edit your first/last name and (Student/Teacher only) profile photo; email and department are read-only. Change your password here. Student sees an "Academic History" section; Teacher sees an "Assigned Courses" section.
- **Timetable** (`/timetable`) — a read-only weekly grid for Student/Teacher/Parent; a management panel for Admin (see below).
- **Notifications** (`/notifications`) — a chronological feed of every notification addressed to you, with unread items visually distinguished, a "Mark all as read" action, and click-to-navigate deep links (e.g. clicking a "Result published" notification takes you to `/results`).

---

## Student

- **Attendance** (`/attendance`) — overall percentage with a low-attendance warning badge below 80%, a class filter, a date-range filter, and a toggle between a table view and a monthly calendar view.
- **Exams** (`/exams`) — every exam you're eligible for, filtered to your enrolled classes; opens into the **Exam Room** (`/exams/{id}/room`) once an exam is open, showing a live countdown timer computed from the server-recorded start time (not your local clock) and one question at a time (MCQ, short answer, descriptive, or coding).
- **Results** (`/results`) — a semester selector, that semester's GPA, a per-course grade table, and a "Download Transcript (PDF)" button. Correct answers/marks for a given exam only appear once that exam's results are published.
- **Fee Centre** (`/fees`) — outstanding balance, due date, payment history, and a per-invoice "Download Invoice"/"Download Receipt" button (label switches automatically once the invoice is fully paid).
- **Timetable Change Requests** — visible on your own class cards in the Timetable grid isn't a Student action; only Teacher can request a change (see below). Students see the resulting schedule once Admin approves it.

## Teacher

- **Mark Attendance** (`/teacher/attendance-marker`) — pick a class session and date, mark each enrolled student present/absent/late/excused, with toast confirmation on save.
- **Exam Builder** (`/teacher/exam-builder`, and `/teacher/exam-builder/{examId}` to edit) — create/edit/delete a draft exam for any class you teach, add questions (MCQ with options, short answer, descriptive, coding), and Publish once ready. A published exam can no longer be edited or deleted.
- **Grading** (`/teacher/grading/{examId}`) — grade each student's submission question-by-question, with per-question awarded marks and optional feedback text.
- **Timetable** (`/timetable`) — a read-only grid of your own classes; each class card has a "Request Change" button opening a modal where you can propose a new day/time and, optionally, a different room (searchable dropdown). Submitting creates a pending request for Admin.
- **Profile** — includes an "Assigned Courses (this semester)" section, derived from your own schedule.

## Parent

Every Parent screen starts with a **Linked Child** selector — if you have more than one linked child, pick which one's data to view; every table on the page is scoped to that selection and clearly labeled ("Viewing results for: ...", "Viewing attendance for: ...", "Viewing fees for: ...").

- **Dashboard** (`/dashboard`) — selected child's attendance %, fee status, recent results, an honest "Not available" placeholder for Upcoming Exams (no backing data exists for this yet), and a "Latest Notifications" widget.
- **Attendance** (`/attendance`) — the same table/calendar view as Student, plus Print/PDF/Excel/CSV export buttons for the selected child's report.
- **Results** (`/results`) — the same layout as Student's Results page: per-semester GPA, per-course grades with a derived Pass/Fail column, and a transcript download — scoped to the selected child. Overall CGPA is shown as "Not available" (the backend has no cross-semester aggregate; see [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) for why this isn't approximated client-side).
- **Fee Centre** (`/fees`) — outstanding balance, payment history, invoices, and Invoice/Receipt download — scoped to the selected child, with a Print button.
- **Timetable** (`/timetable`) — the selected child's weekly schedule.
- **Notifications** — you receive the same four notification types as your linked child (result published, schedule change, attendance warning, fee due), addressed to your own account.

## Admin

- **User Management** (`/admin/users`) — create/deactivate Student and Teacher accounts, filter by department.
- **Academic Setup** (`/admin/academic-setup/departments`, `.../courses`, `.../rooms`, `.../semesters`) — full CRUD for Departments, Courses, Rooms, and Semesters, each its own page linked by a shared sub-navigation. Deleting an entity still referenced elsewhere (e.g. a Department with existing Courses) is rejected with a clear conflict message rather than silently failing.
- **Timetable — Admin panel** (`/timetable`) — three creation forms (Class Session, Enroll Student, Schedule Entry) using searchable dropdowns for every course/teacher/semester/room/student reference, a **Pending Schedule Change Requests** panel listing every Teacher's open request with its current vs. requested values and Approve/Reject actions (with an optional comment shown to the Teacher), and a manual "Check Conflicts" action.
- **Result Approval** (`/admin/result-approval`) — every Teacher-submitted result grouped by exam, with Approve (publishes it — notifying the Student and every linked Parent) or Reject (requires a comment).
- **Fee Dashboard** (`/admin/fee-dashboard`) — create fee structures (auto-generates one invoice per eligible student and notifies them + their linked parents), record payments, view overdue accounts, and manually trigger overdue notices.
- **Reports** (`/admin/reports`) — Attendance/Results/Fees reports filterable by department/semester/student, each with Print/PDF/Excel export (Attendance additionally offers CSV).

---

## Common workflows, end to end

**Attendance:** Teacher marks attendance on `/teacher/attendance-marker` → the same record is immediately visible to the Student on `/attendance`, to a linked Parent on their own `/attendance` (scoped to that child), and to Admin via `/admin/reports` — all reading the same live-computed percentage, never a cached number.

**Exam → Result:** Teacher builds and publishes an exam → Student takes it in the Exam Room → Teacher grades it → Admin approves it on `/admin/result-approval` → the Student sees it on `/results` and a linked Parent sees it on their own `/results`, and both receive a "Result published" notification.

**Schedule change:** Teacher requests a change from `/timetable` → it appears in Admin's Pending Schedule Change Requests panel → Admin approves or rejects it → the Teacher is notified of the outcome, and on approval the timetable (and anyone viewing it) updates immediately.

**Fees:** Admin creates a fee structure on `/admin/fee-dashboard` → an invoice is auto-generated for every eligible student, and both the Student and their linked Parent are notified → both can view and download it from their own Fee Centre → once Admin records a payment, the invoice's status (and its downloadable PDF) updates to reflect it, and the PDF relabels itself "Receipt" once fully paid.
