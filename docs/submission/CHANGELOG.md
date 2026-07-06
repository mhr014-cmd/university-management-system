# Changelog

> This is a condensed, submission-ready version history. The complete, unabridged changelog — every file touched and every documentation cross-reference for all 12 milestones — is the repository root's [`CHANGELOG.md`](../../CHANGELOG.md); this document summarizes the same history plus the work completed since its last entry.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/), newest first.

---

## Since v2.0.0 (post-release hardening — not yet tagged)

Four sequential passes, each reviewed and verified (full backend + frontend test suite, lint, type-check, build) before the next began:

### Academic Setup (reference-data management)
- New Admin screens for full Department/Course/Room/Semester CRUD (previously list/create only), each its own page with a shared sub-navigation.
- New shared `SearchableSelect` component (type-to-filter dropdown, full keyboard support — Escape/Arrow Up/Down/Enter) replacing raw-UUID text inputs across the Admin scheduling forms.
- Backend `update()`/`delete()` added for all four reference-data entities, using the existing `ON DELETE RESTRICT` FK policy (translated to `409 Conflict` by the service layer) rather than introducing soft-delete.

### Production-readiness gap-closure pass (Teacher/Parent portal audit)
- Fixed a genuine bug: resolving a Teacher's schedule change request updated the timetable but never notified the Teacher of the outcome — now notifies on both approval and rejection.
- Extended `notify_result_published`/`notify_schedule_change` to fan out to every linked Parent, not just the Student (closing a gap between the proposal's stated intent and the actual notification dispatch).
- Added an Admin approval queue UI (`GET /schedule/change-requests` + a Pending Requests panel) — the backend create/resolve endpoints existed with no way for Admin to see pending requests at all.
- Added a room-change option to the Teacher's schedule change-request form (the backend already accepted it; the UI never collected it).
- Extended Parent access (ownership-checked) to attendance report PDF/Excel/CSV, transcript PDF, and invoice/receipt PDF downloads — previously Admin/Student-only.
- Added a CSV attendance-report export (PDF/Excel already existed).
- Built dedicated Parent Results and Fee Centre pages (role-branched, same pattern as the pre-existing Timetable page) — Parent previously only had partial dashboard widgets for this data.
- Labeled the invoice PDF "Fee Receipt" instead of "Fee Invoice" once an invoice is fully paid (no duplicate generator).
- Added a "Latest Notifications" widget to the Parent Dashboard.
- Explicitly **not** built, and documented as such: a Communication/Messaging module, a Progress Report generator, Teacher Remarks on the Results page (no backing column exists), and an overall CGPA figure (no backend aggregate exists) — each would have been new scope, not gap-closure.

### Lead QA / production-readiness audit
- Three parallel audits (UI/UX + accessibility across all 4 roles' pages; backend RBAC/ownership/security/data-integrity; end-to-end workflow + React Query cache-invalidation correctness).
- Found and fixed two genuine input-validation gaps: `CourseCreate`/`CourseUpdate.credit_hours` and `RoomCreate`/`RoomUpdate.capacity` had no lower bound (0 or negative was accepted) — fixed with a Pydantic `Field(ge=1)` constraint, no schema/migration change.
- Everything else audited came back clean: no dead UI, no accessibility gaps, no RBAC/ownership gaps, no orphan-record risk, no stale-cache bugs in any of the four core workflows (attendance, exam→result, schedule-change, fees).

### Documentation
- This submission package (`docs/submission/`) — README, installation, user manual, architecture/database/API summaries, test report, deployment guide, project structure, and this changelog.

**Test suite after all of the above:** 477 backend tests (was 380 at v2.0.0), 61 frontend tests (was 7 at v2.0.0), all passing — see [TEST_REPORT.md](TEST_REPORT.md).

---

## [2.0.0] — Final Milestone-Program Release

All 12 milestones (M0–M11) delivered, reviewed, and approved sequentially. **68 REST endpoints, 26 database tables, 10 Alembic migrations (single head), 380 backend tests, 7 frontend tests.**

### Milestone 11 — Hardening, Testing & Deployment
- Login rate limiting (5 attempts/60s/IP), production-only API-docs gating (`/docs`/`/redoc`/`/openapi.json`), a frontend error boundary, an ESLint config, three interaction-critical frontend component tests (exam timer, grading form, result-approval workflow), a fully idempotent demo-data seed script, and real CI pipelines for both backend and frontend (replacing earlier placeholders).
- Removed an orphaned, never-routed Parent "Child View" placeholder page.

### Milestone 10 — Dashboards & Reporting
- `GET /results/reports`, `GET /fees/reports` (Admin, filterable by department/semester/student), `POST /fees/overdue/notify` (manual bulk/selected overdue notice).
- All four role-specific Dashboard pages, the Admin Reports page (Attendance/Results/Fees tabs).

### Milestone 9 — Notifications
- `notification` table + `GET /notifications` / `PUT /notifications/{id}/read`.
- Four automatic, event-driven notification triggers: `result_published`, `schedule_change`, `attendance_warning` (only on a genuine threshold crossing), `fee_due`.
- Notifications page (chronological feed, unread styling, deep links) and a persistent unread-count bell in the app shell.

### Milestone 8 — Fees (Optional Module)
- `fee_structure`, `invoice`, `payment` tables.
- Fee structure creation with automatic per-eligible-student invoice generation; payment recording with strict overpayment/already-paid rejection; overdue-account listing; PDF invoice download.
- Student Fee Centre page; Admin Fee Dashboard.

### Milestone 7 — Results & Transcripts
- `result` table; submit → approve/reject → publish workflow with 15 enforced domain rules; credit-hour-weighted per-semester GPA; PDF transcript generation (introduced ReportLab to the stack).
- Student Results View; Admin Result Approval queue.

### Milestone 6 — Exam Grading
- Per-question grading (awarded marks + feedback) with VR-006 (`awarded_marks <= question.marks`) enforced at the service layer.
- Teacher Grading Interface.

### Milestone 5 — Attendance
- `attendance_record` table; marking, correction, `GET /attendance/me`/`{classId}`, department/semester/student-filterable Admin reporting; automatic low-attendance-warning threshold logic (introduced in M9's notification module, scoped here).
- Teacher Attendance Marker; Student/Parent Attendance page (table + monthly calendar view).

### Milestone 4 — Exams & Exam-Taking
- `exam`, `question`, `question_option`, `exam_submission`, `answer` tables; exam builder (MCQ/short-answer/descriptive/coding); timed exam-taking with a server-recorded start time (never a client clock).
- Teacher Exam Builder; Student Exam List and Exam Room.

### Milestone 3 — Scheduling
- `class_session`, `enrollment`, `schedule_entry`, `schedule_change_request` tables; room/teacher overlap-conflict detection at both the database (unique index) and service (overlap-math) level; Teacher schedule change-request workflow.
- Timetable page (role-branching grid/management view).

### Milestone 2 — Reference Data & RBAC Retrofit
- `department`, `course`, `room`, `semester` tables (list/create initially); RBAC dependency wiring standardized across every existing endpoint.

### Milestone 1 — Users & Profiles
- `user`/`student`/`teacher`/`parent`/`admin`/`parent_student_link` tables; Admin-managed Student/Teacher account lifecycle; self-service profile.

### Milestone 0 — Foundations
- FastAPI + SQLAlchemy + Alembic + PostgreSQL project skeleton; JWT authentication (login/refresh/logout/password change); React + TypeScript + Vite + TailwindCSS + React Query frontend skeleton; the layered Router→Service→Repository architecture established and enforced from this point forward.

---

For the full file-by-file, requirement-by-requirement detail behind every milestone above — including every documented design decision, every "Known Issues" note at the time it was written, and every cross-referenced documentation change — see the root [`CHANGELOG.md`](../../CHANGELOG.md) and `PROJECT_PROGRESS.md`.
