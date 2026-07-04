# Implementation Roadmap
## University Management System (ICT Education)

**Source inputs:** `docs/product_proposal.pdf`, `docs/Requirement_Analysis.md`, `docs/System_Architecture.md`, `docs/Database_Design.md`
**Submission deadline:** July 13, 2026
**Today's date:** July 3, 2026 → **10 calendar days remaining**

> **Schedule risk flag:** The estimated effort below totals roughly 18–20 focused working days for a solo builder covering the full scope (backend + frontend + DB + optional fees module). Against a 10-day runway, this is **not achievable in full** at a sustainable pace. Recommended mitigation: run Milestones 0–7 as the committed core (this alone covers 60/80 project marks: API + Web app + DB design), and treat Milestones 8 (Fees) and parts of 10 (advanced reporting) as stretch scope to cut first if time runs short — consistent with the proposal marking Fees as "(Optional)." This tradeoff should be confirmed with the instructor rather than assumed.

---

## Build Order Rationale

Milestones are sequenced by **data dependency**, not by feature importance: a table/endpoint/page cannot be built before the entities it references exist. The order follows the dependency chain identified in `Database_Design.md`:

```
User/Auth  →  Department/Course/Room/Semester (reference data)
           →  Student/Teacher/Parent/Admin profiles + linking
           →  ClassSession/Enrollment/Scheduling
           →  Attendance   (needs ClassSession)
           →  Exams/Grading (needs ClassSession)
           →  Results       (needs Exams + Semester)
           →  Fees          (needs Department/Semester/Student — independent of Exams/Attendance, can parallelize)
           →  Notifications (cross-cutting, needs events from Results/Attendance/Schedule/Fees to fire)
           →  Reporting/Admin dashboards (needs all prior data)
           →  Hardening/Deployment (last, needs a feature-complete system)
```

---

## Milestone 0 — Project Scaffolding & Environment Setup

**Goal:** Stand up empty-but-runnable backend and frontend projects, database connectivity, and CI-ready structure, so every later milestone has a place to land code.

**Files to create:**
- `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/db/session.py`, `backend/app/db/base.py`
- `backend/alembic.ini`, `backend/alembic/env.py`
- `backend/requirements/` or `pyproject.toml`
- `frontend/src/app/` (root layout, router shell, providers)
- `frontend/package.json`, `frontend/tailwind.config`, `frontend/tsconfig.json`
- `.env.example` (backend and frontend)
- `docs/` (already populated — no changes here)

**APIs:** `GET /health` (basic liveness check; not part of the proposal's spec but needed to verify deployment wiring)

**Database tables:** none yet (empty database, Alembic initialized with a baseline revision)

**Frontend pages:** blank routed shell (Login placeholder only)

**Estimated completion time:** 0.5 day

**Dependencies:** none (first milestone)

---

## Milestone 1 — Core Reference Data Model

**Goal:** Implement the foundational, low-churn entities that everything else references: `Department`, `Course`, `Room`, `Semester`. No business logic yet — this is pure schema + basic Admin CRUD to unblock later milestones.

**Files to create:**
- `backend/app/models/department.py`, `course.py`, `room.py`, `semester.py`
- `backend/app/schemas/department.py`, `course.py`, `room.py`, `semester.py`
- `backend/app/routers/reference_data.py` (or split per entity)
- `backend/app/services/reference_data_service.py`
- `backend/alembic/versions/0002_core_reference_data.py` (corrected from `0001_core_reference_data.py` — revision `0001` is consumed by Milestone 0's baseline migration; the actual implemented migration always used `0002`, this entry was simply never updated to match. Found during the Milestone 4 pre-implementation review while fixing the same class of stale-reference issue across every later milestone's entry.)

**APIs:** Not explicitly listed in the proposal's API spec (§6 has no `/departments`, `/courses`, `/rooms`, `/semesters` endpoints — this is a gap in the source proposal, consistent with `Requirement_Analysis.md` §14). Minimal internal/admin CRUD is required regardless for the system to function; treat as an implementation necessity, not a proposal deviation.

**Database tables:** `department`, `course`, `room`, `semester`

**Frontend pages:** none dedicated (these are managed as lookup data, likely surfaced only as dropdowns inside later Admin screens)

**Estimated completion time:** 0.5 day

**Dependencies:** Milestone 0

---

## Milestone 2 — Authentication & Authorization

**Goal:** Implement the `User` entity, JWT login/refresh/logout, password change, and the RBAC + ownership-check middleware that every subsequent endpoint relies on.

**Milestone 2 scope note (added during M2 review):** the "ownership-check" half of the Goal/file-list wording above describes the eventual capability this milestone's dependency chain enables, not something delivered *in* M2 itself. M2 has no `/me`-scoped or parent-linked endpoints — those first appear in Milestone 3 (`GET /users/me`, per `Requirement_Traceability_Matrix.md` NFR-002) and later milestones. `backend/app/middleware/rbac.py` therefore implements only role checks (`require_roles`) in M2; ownership/linkage checks belong in the service layer of whichever milestone first introduces an ownership-scoped resource, per `CLAUDE.md` §6 ("verify ownership/linkage in the service layer on every request"), not in this shared RBAC module. This is a deliberate scope boundary, not an oversight — there is nothing to check ownership of yet.

**Files to create:**
- `backend/app/models/user.py`
- `backend/app/schemas/auth.py`
- `backend/app/core/security.py` (password hashing, JWT encode/decode)
- `backend/app/middleware/auth.py` (token verification dependency)
- `backend/app/middleware/rbac.py` (role-check dependency; ownership checks are implemented per-endpoint at the service layer per `CLAUDE.md` §6, not in this shared module — see the Milestone 2 note below)
- `backend/app/routers/auth.py`
- `backend/app/services/auth_service.py`
- `backend/app/repositories/user_repository.py` (per `CLAUDE.md` §6 layering — routers/services never touch the ORM session directly; not originally enumerated here, same precedent as Milestone 1)
- `backend/alembic/versions/0003_user.py` (corrected from `0002_user.py` — revision `0002` was already consumed by Milestone 1's `0002_core_reference_data`, a stale artifact from before real sequential migrations existed)
- `frontend/src/auth/` (auth context, token storage, route guards)
- `frontend/src/pages/Login/`

**APIs:**
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `PUT /auth/password`

**Database tables:** `user`

**Frontend pages:** Login

**Estimated completion time:** 1.5 days

**Dependencies:** Milestone 0 (needs the DB/session wiring; does **not** need Milestone 1)

---

## Milestone 3 — User Management & Profiles (Student, Teacher, Parent, Admin)

**Goal:** Implement role-specific profile tables, self-service profile endpoints, and Admin-driven account lifecycle (create/update/deactivate) for Students and Teachers. Seed the first Admin account here (per `Database_Design.md` §11, item 4).

**Milestone 3 scope note (added during M3 pre-implementation review):** the `parent` and `parent_student_link` tables are created in this milestone (required by `Database_Design.md` and by later milestones' `BR-007`/`NFR-003` Parent-scoping needs), but **no REST endpoint creates a Parent account or a `ParentStudentLink` row** — the proposal never defines a parent-to-student linkage mechanism (`Requirement_Analysis.md` §14 item 8, still unresolved) and no endpoint for it appears in this milestone's own API list below. Confirmed with the user: the `parent`/`parent_student_link` tables are created and migration-verified in Milestone 3 but stay empty — seeding Parent accounts is `backend/scripts/seed_demo_data.py`'s job (a later milestone per this document), and a REST-driven creation/linking flow is deferred until a future milestone (or the ambiguity in §14 item 8 is resolved) if ever required. Similarly, `POST /users/students`/`/teachers`'s "password... or omitted if invite-based provisioning" clause is not implemented — confirmed with the user that Admin always supplies an initial password directly; no invite/email-dispatch mechanism exists in the codebase yet (that would be Milestone 9, Notifications, scope).

**Files to create:**
- `backend/app/models/student.py`, `teacher.py`, `parent.py`, `admin.py`, `parent_student_link.py`
- `backend/app/schemas/student.py`, `teacher.py`, `user.py` (corrected from `user_profile.py` — Milestone 0 had already scaffolded this placeholder as `user.py`, not `user_profile.py`; no separate `schemas/parent.py`/`admin.py` were added since Admin has no dedicated CRUD endpoints and Parent's `/users/me` profile shape is covered by the shared `UserProfile` schema in `user.py`)
- `backend/app/routers/users.py`
- `backend/app/services/user_service.py`
- `backend/app/repositories/user_repository.py` (extends the same file Milestone 2 created — no separate `student_repository.py`/`teacher_repository.py`, per that file's own Milestone 2 docstring)
- `backend/alembic/versions/0004_role_profiles.py` (corrected from `0003_role_profiles.py` — revision `0003` was already consumed by Milestone 2's `0003_user.py`, the same class of stale-reference issue already fixed once for M2's own migration filename)
- `backend/scripts/seed_admin.py` (bootstrap the first Admin — cannot be self-registered)
- `frontend/src/pages/Profile/`
- `frontend/src/pages/Admin/UserManagement/`
- `frontend/src/features/users/` (React Query hooks)

**APIs:**
- `GET /users/me`
- `PUT /users/me`
- `GET /users/students`
- `POST /users/students`
- `GET /users/students/{id}`
- `PUT /users/students/{id}`
- `DELETE /users/students/{id}`
- `GET /users/teachers`
- `POST /users/teachers`
- `PUT /users/teachers/{id}`

**Database tables:** `student`, `teacher`, `parent`, `admin`, `parent_student_link`

**Frontend pages:** Profile page, Admin: user management

**Estimated completion time:** 2 days

**Dependencies:** Milestone 1 (student/teacher reference `department_id`), Milestone 2 (extends `User`)

---

## Milestone 4 — Scheduling & Timetable

**Goal:** Implement `ClassSession`, `Enrollment`, `ScheduleEntry`, and `ScheduleChangeRequest`, including conflict detection — this unblocks Attendance and Exams, both of which are scoped to a `ClassSession`.

**Milestone 4 scope note (added during M4 pre-implementation review):** `class_session` and `enrollment` are both required tables (referenced as foreign keys throughout `API_Contract.md` — `POST /schedule`, exams, attendance) but neither has a creation endpoint anywhere in the proposal or this document's original API list. Unlike Milestone 3's Parent-linking gap, this one is load-bearing for M4's own stated deliverables: without a way to create a `class_session`, `POST /schedule` can never be exercised, and M5/M6 both explicitly depend on `class_session` existing. Confirmed with the user (Option 1 of two presented): add minimal Admin-only creation endpoints — `POST /schedule/class-sessions` and `POST /schedule/enrollments` — as Derived Engineering Additions, same precedent as Milestone 1's reference-data CRUD ("implementation necessity, not a proposal deviation"). Documented in `API_Contract.md` §7.8-7.9 and `Proposal_vs_Engineering_Additions.md`.

**Files to create:**
- `backend/app/models/class_session.py`, `enrollment.py`, `schedule_entry.py`, `schedule_change_request.py`
- `backend/app/schemas/schedule.py`
- `backend/app/routers/schedule.py`
- `backend/app/services/schedule_service.py` (includes conflict-detection logic — BR-005)
- `backend/app/repositories/schedule_repository.py`
- `backend/alembic/versions/0005_scheduling.py` (corrected from `0004_scheduling.py` — revision `0004` was already consumed by Milestone 3's `0004_role_profiles.py`, the same class of stale-reference issue already fixed for M2's and M3's own migration filenames)
- `frontend/src/pages/Timetable/`
- `frontend/src/features/schedule/`

**APIs:**
- `GET /schedule/me`
- `POST /schedule`
- `PUT /schedule/{id}`
- `DELETE /schedule/{id}`
- `GET /schedule/conflicts`
- `POST /schedule/change-requests` *(gap-fill — not in the proposal's §6 API spec; supports FR-050/BR-004. Was previously missing from this list even though `schedule_change_request.py` above and `API_Contract.md` §7.6 both already scoped it to this milestone — corrected during the M4 pre-implementation review, not newly added scope.)*
- `POST /schedule/change-requests/{id}/resolve` *(gap-fill, same note as above; `API_Contract.md` §7.7)*
- `POST /schedule/class-sessions` *(Derived addition, confirmed with the user during the M4 pre-implementation review — see the scope note above; `API_Contract.md` §7.8)*
- `POST /schedule/enrollments` *(Derived addition, same note; `API_Contract.md` §7.9)*

**Database tables:** `class_session`, `enrollment`, `schedule_entry`, `schedule_change_request`

**Frontend pages:** Timetable (weekly grid)

**Estimated completion time:** 2 days

**Dependencies:** Milestone 1 (Course, Room, Semester), Milestone 3 (Teacher, Student for enrollment)

---

## Milestone 5 — Attendance

**Goal:** Implement attendance marking, correction, per-student summaries, and the low-attendance warning trigger.

**Milestone 5 scope note (added during M5 pre-implementation review):** two items resolved before coding, confirmed with the user:
1. **BR-008's threshold** (previously undefined, `Requirement_Analysis.md` §14 item 4) is **80%**, resolved from two independent "Below 80%" mockups in `UI_Wireframes.md`. `GET /attendance/me` surfaces a computed `low_attendance_warning` boolean; actual notification dispatch is Milestone 9 scope (the `notification` module doesn't exist yet — same pattern as M3's FR-008 and M4's FR-051).
2. **`GET /schedule/class-sessions/{class_session_id}/roster`** (Derived Engineering Addition) — `UI_Wireframes.md` §15 requires the Attendance Marker's roster to load with enrolled students pre-populated, but no endpoint anywhere provided this. Implemented via the schedule router/service (operates on `enrollment`/`class_session`, both Scheduling-owned), not the attendance domain, even though it's needed by this milestone.

**Files to create:**
- `backend/app/models/attendance_record.py`
- `backend/app/schemas/attendance.py`
- `backend/app/routers/attendance.py`
- `backend/app/services/attendance_service.py` (percentage calculation, warning trigger — BR-008)
- `backend/app/repositories/attendance_repository.py`
- `backend/alembic/versions/0006_attendance.py` (already correctly numbered — the M4 pre-implementation review's roadmap-wide migration numbering fix was applied proactively)
- `frontend/src/pages/Attendance/` (student view)
- `frontend/src/pages/Teacher/AttendanceMarker/`
- `frontend/src/features/attendance/`
- `backend/app/repositories/schedule_repository.py`, `backend/app/services/schedule_service.py`, `backend/app/routers/schedule.py`, `backend/app/schemas/schedule.py` (extended, not new files — the roster endpoint above)

**APIs:**
- `GET /attendance/me`
- `POST /attendance`
- `GET /attendance/{classId}`
- `PUT /attendance/{id}`
- `GET /attendance/reports`
- `GET /schedule/class-sessions/{class_session_id}/roster` *(Derived addition, confirmed with the user during the Milestone 5 pre-implementation review — see the scope note above; `API_Contract.md` §7.10)*

**Database tables:** `attendance_record`

**Frontend pages:** Attendance page (Student), Teacher: attendance marker

**Estimated completion time:** 1.5 days

**Dependencies:** Milestone 4 (`class_session`, `enrollment`)

---

## Milestone 6 — Exams & Grading

**Goal:** Implement the exam builder, exam-taking flow, submission, and grading — the largest single feature area.

**Files to create:**
- `backend/app/models/exam.py`, `question.py`, `question_option.py`, `exam_submission.py`, `answer.py`, `question_grade.py`
- `backend/app/schemas/exam.py`, `submission.py`, `grading.py`
- `backend/app/routers/exams.py`
- `backend/app/services/exam_service.py` (status transitions — BR-003), `grading_service.py` (VR-006 marks-cap check)
- `backend/app/repositories/exam_repository.py`
- `backend/alembic/versions/0007_exams.py` (corrected from `0006_exams.py` — see the Milestone 4 pre-implementation review's roadmap-wide migration numbering fix)
- `frontend/src/pages/ExamList/`
- `frontend/src/pages/ExamRoom/` (timed exam interface)
- `frontend/src/pages/Teacher/ExamBuilder/`
- `frontend/src/pages/Teacher/GradingInterface/`
- `frontend/src/features/exams/`

**APIs:**
- `GET /exams`
- `POST /exams`
- `GET /exams/{id}`
- `PUT /exams/{id}`
- `DELETE /exams/{id}`
- `POST /exams/{id}/submit`
- `POST /exams/{id}/grade`
- `GET /exams/{id}/results`

**Database tables:** `exam`, `question`, `question_option`, `exam_submission`, `answer`, `question_grade`

**Frontend pages:** Exam list, Exam room, Teacher: exam builder, Teacher: grading interface

**Estimated completion time:** 3.5 days

**Dependencies:** Milestone 4 (`class_session`), Milestone 3 (Teacher/Student)

---

## Milestone 7 — Results & Transcripts

**Goal:** Implement the result submission → approval → publication workflow and PDF transcript generation.

**Files to create:**
- `backend/app/models/result.py`
- `backend/app/schemas/result.py`
- `backend/app/routers/results.py`
- `backend/app/services/result_service.py` (workflow state machine — BR-002)
- `backend/app/pdf/transcript_generator.py`
- `backend/alembic/versions/0008_results.py` (corrected from `0007_results.py` — see the Milestone 4 pre-implementation review's roadmap-wide migration numbering fix)
- `frontend/src/pages/ResultsView/`
- `frontend/src/pages/Admin/ResultApproval/`
- `frontend/src/features/results/`

**APIs:**
- `GET /results/me`
- `POST /results/{examId}/submit`
- `POST /results/{id}/approve`
- `GET /results/{studentId}/transcript`

**Database tables:** `result`

**Frontend pages:** Results view (Student), Admin: result approval

**Estimated completion time:** 2 days

**Dependencies:** Milestone 6 (results are derived from graded exams), Milestone 1 (Semester)

---

## Milestone 8 — Fees (Optional)

**Goal:** Implement fee structure definition, payment recording, invoicing, and overdue tracking. Marked Optional in the proposal — see the schedule-risk note at the top of this document regarding cut priority.

**Files to create:**
- `backend/app/models/fee_structure.py`, `payment.py`, `invoice.py`
- `backend/app/schemas/fee.py`
- `backend/app/routers/fees.py`
- `backend/app/services/fee_service.py`
- `backend/app/pdf/invoice_generator.py`
- `backend/alembic/versions/0009_fees.py` (corrected from `0008_fees.py` — see the Milestone 4 pre-implementation review's roadmap-wide migration numbering fix)
- `frontend/src/pages/FeeCentre/` (Student/Parent)
- `frontend/src/pages/Admin/FeeDashboard/`
- `frontend/src/features/fees/`

**APIs:**
- `GET /fees/me`
- `POST /fees`
- `POST /fees/payments`
- `GET /fees/payments/{studentId}`
- `GET /fees/invoices/{id}`
- `GET /fees/overdue`

**Database tables:** `fee_structure`, `payment`, `invoice`

**Frontend pages:** Fee centre, Admin: fee dashboard

**Estimated completion time:** 2 days

**Dependencies:** Milestone 1 (Department, Semester), Milestone 3 (Student), Milestone 3 (`parent_student_link` for Parent access) — **independent of Milestones 4–7**, can be built in parallel by a second contributor if the team is not solo.

**Note:** `POST /fees/overdue/notify` (FR-056, gap-fill) is deferred to Milestone 10, not built here, because it writes to the `notification` table, which doesn't exist until Milestone 9.

---

## Milestone 9 — Notifications

**Goal:** Implement the cross-cutting notification module — generation, storage, and the notification feed UI. This milestone closes the endpoint gap flagged in `Requirement_Analysis.md` §14 (item 3), so notification API endpoints must first be defined even though the proposal's §6 omits them.

**Files to create:**
- `backend/app/models/notification.py`
- `backend/app/schemas/notification.py`
- `backend/app/routers/notifications.py` (new — not in proposal §6, required to satisfy the Notifications feature/screen)
- `backend/app/notifications/dispatcher.py` (event hooks triggered from Result/Attendance/Schedule/Fee services)
- `backend/alembic/versions/0010_notifications.py` (corrected from `0009_notifications.py` — see the Milestone 4 pre-implementation review's roadmap-wide migration numbering fix)
- `frontend/src/pages/Notifications/`
- `frontend/src/features/notifications/`

**APIs (proposed, filling the identified gap):**
- `GET /notifications`
- `PUT /notifications/{id}/read`

**Database tables:** `notification`

**Frontend pages:** Notifications panel

**Estimated completion time:** 1 day

**Dependencies:** Milestones 5, 7, 8, 4 (needs event sources: attendance warnings, result publication, fee due dates, schedule changes) — build last among feature milestones since it listens to all of them.

---

## Milestone 10 — Dashboards & Reporting

**Goal:** Implement role-specific dashboards (summary widgets) and Admin reporting (attendance/result/fee reports by department/semester/student — FR-030, FR-054, FR-055), plus the manual overdue-notify action (FR-056), tying together all previously built data.

**Files to create:**
- `backend/app/routers/reports.py` (hosts `GET /results/reports`, `GET /fees/reports`; `GET /attendance/reports` already lives in `routers/attendance.py` per Milestone 5)
- `backend/app/services/report_service.py`
- `frontend/src/pages/Dashboard/` (role-composed widgets, per `System_Architecture.md` §3.3)
- `frontend/src/pages/Admin/Reports/`

**APIs:**
- `GET /attendance/reports` (already listed in Milestone 5)
- `GET /results/reports` (gap-fill, FR-054 — see `API_Contract.md` §9.1)
- `GET /fees/reports` (gap-fill, FR-055 — see `API_Contract.md` §9.2)
- `POST /fees/overdue/notify` (gap-fill, FR-056 — see `API_Contract.md` §6.7; lives in `routers/fees.py`, not `routers/reports.py`)

**Database tables:** none new (aggregation queries over existing tables)

**Frontend pages:** Dashboard (all roles), Admin: Reports (FR-054, FR-055)

**Estimated completion time:** 1.5 days

**Dependencies:** Milestones 3, 4, 5, 6, 7, 8, 9 (dashboard widgets pull from every domain)

---

## Milestone 11 — Hardening, Testing & Deployment

**Goal:** Close out non-functional requirements: error handling consistency, logging, security review, test coverage, and deployment to the target environments described in `System_Architecture.md` §8.

**Files to create:**
- `backend/app/middleware/error_handlers.py`
- `backend/app/middleware/logging.py`
- `backend/tests/` (unit + integration tests per domain module)
- `frontend/tests/`
- `infra/docker/Dockerfile.backend`, `Dockerfile.frontend`
- `infra/ci/pipeline.yml`
- `backend/scripts/seed_demo_data.py` (per `Database_Design.md` §11 seed data requirements)

**APIs:** none new — hardening of existing endpoints only (consistent error shapes, rate limiting on `/auth/login` per `System_Architecture.md` §11)

**Database tables:** none new

**Frontend pages:** none new — cross-cutting QA pass on all previously built screens

**Estimated completion time:** 2 days

**Dependencies:** all prior milestones (this is the final, whole-system pass)

---

## Summary Table

| # | Milestone | Est. Time | Cumulative | Depends On |
|---|---|---|---|---|
| 0 | Project Scaffolding | 0.5 day | 0.5 | — |
| 1 | Core Reference Data | 0.5 day | 1.0 | M0 |
| 2 | Authentication & Authorization | 1.5 days | 2.5 | M0 |
| 3 | User Management & Profiles | 2 days | 4.5 | M1, M2 |
| 4 | Scheduling & Timetable | 2 days | 6.5 | M1, M3 |
| 5 | Attendance | 1.5 days | 8.0 | M4 |
| 6 | Exams & Grading | 3.5 days | 11.5 | M3, M4 |
| 7 | Results & Transcripts | 2 days | 13.5 | M1, M6 |
| 8 | Fees (Optional) | 2 days | 15.5 | M1, M3 (parallelizable with M4–M7) |
| 9 | Notifications | 1 day | 16.5 | M4, M5, M7, M8 |
| 10 | Dashboards & Reporting | 1.5 days | 18.0 | M3, M4, M5, M6, M7, M8, M9 |
| 11 | Hardening & Deployment | 2 days | 20.0 | All |

**Total estimated effort:** ~20 working days solo (or ~13–14 days if Milestone 8 runs in parallel with a second contributor, given its independence from M4–M7).

**Against the 10-day runway to July 13, 2026:** prioritize Milestones 0–7 and 11 as the committed path (core API + web app + DB, satisfying the 80-mark project rubric's first three line items), treating Milestone 8 (Fees) as the first cut and Milestone 10 (advanced reporting) as the second cut if the timeline slips further. This prioritization should be confirmed with the instructor given the "(Optional)" labeling ambiguity already flagged in `Requirement_Analysis.md` §14.
