# Requirement Traceability Matrix
## University Management System (ICT Education)

**Source inputs:** `docs/product_proposal.pdf`, `docs/Requirement_Analysis.md`, `docs/System_Architecture.md`, `docs/Database_Design.md`, `docs/Implementation_Roadmap.md`
**Scope:** Traces every Functional Requirement (FR-001–FR-056) and Non-Functional Requirement (NFR-001–NFR-016) from `Requirement_Analysis.md` through to database tables, backend APIs, frontend pages, and applicable validation rules.

**Priority scale:**
- **Critical** — core grading-rubric feature (API/Web App/DB per proposal §2); system cannot function or pass core grading without it.
- **High** — required feature explicitly specified in the proposal, non-optional module.
- **Medium** — required but lower-impact, or part of the "(Optional)" Fees module (still specified in full — see A-005).
- **Low** — supporting/cross-cutting requirement not independently gradable but needed for correctness.

**Status columns** are all initialized to **Pending** per instruction, to be updated as implementation proceeds through `Implementation_Roadmap.md` milestones.

---

## A. Functional Requirements

| Req ID | Requirement Description | Priority | User Role | Module | Database Tables | Backend API | Frontend Pages | Validation Rules | Testing Status | Implementation Status | Verification Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FR-001 | Log in with email and password; returns access + refresh token | Critical | All | Authentication & Authorization | `user` | `POST /auth/login` | Login | VR-001 | Passed (unit + integration) | Implemented | Verified (M2) |
| FR-002 | Refresh an expired access token without re-entering credentials | Critical | All | Authentication & Authorization | `user` | `POST /auth/refresh` | Login (silent refresh, no dedicated screen) | — | Passed (unit + integration) | Implemented | Verified (M2) |
| FR-003 | Log out and invalidate current session | High | All | Authentication & Authorization | `user` | `POST /auth/logout` | Dashboard (logout action; no dedicated screen) | — | Passed (unit + integration) | Implemented | Verified (M2) |
| FR-004 | Change own password | High | All | Authentication & Authorization | `user` | `PUT /auth/password` | Profile page | VR-002 | Passed (unit + integration) | Implemented | Verified (M2) — note: uses the shared Login-adjacent flow, not a dedicated Profile page yet (Profile page itself lands in a later milestone; the endpoint is complete and tested) |
| FR-005 | Redirect to role-specific dashboard after successful login | High | All | Authentication & Authorization | `user` | `POST /auth/login` (redirect logic is frontend-side) | Dashboard | — | Passed (manual browser verification) | Implemented (redirects to Dashboard; role-specific dashboard *content* is a later milestone — see M2 Known Issues) | Verified (M2) |
| FR-006 | Retrieve own profile | Critical | All | User Management | `user`, `student`, `teacher`, `parent`, `admin` | `GET /users/me` | Profile page | — | Passed (unit + integration) | Implemented | Verified (M3) |
| FR-007 | Update own profile (personal info, profile photo) | Critical | All | User Management | `user`, `student`, `teacher`, `parent`, `admin` | `PUT /users/me` | Profile page | VR-009 | Passed (unit + integration) | Implemented | Verified (M3) |
| FR-008 | Student views academic history alongside profile data | High | Student | User Management | `student`, `enrollment`, `result` | `GET /users/me` | Profile page | — | Pending | Not implemented | Pending — `GET /users/me`'s contracted response (`API_Contract.md` §2.1: id/email/role/profile only) has no academic-history fields; `enrollment`/`result` don't exist as tables until M4/M6/M7. This FR is not deliverable by M3's actual `/users/me` contract as written — carried forward, not silently dropped |
| FR-009 | Admin lists all students | Critical | Admin | User Management | `student`, `user` | `GET /users/students` | Admin: user management | — | Passed (unit + integration) | Implemented | Verified (M3) |
| FR-010 | Admin creates a new student account | Critical | Admin | User Management | `student`, `user` | `POST /users/students` | Admin: user management | VR-001 (email format) | Passed (unit + integration) | Implemented | Verified (M3) |
| FR-011 | Admin or Teacher retrieves a single student's record | Critical | Admin, Teacher | User Management | `student`, `user` | `GET /users/students/{id}` | Admin: user management | — | Passed (unit + integration) | Implemented | Verified (M3) |
| FR-012 | Admin updates a student's record | Critical | Admin | User Management | `student`, `user` | `PUT /users/students/{id}` | Admin: user management | VR-009 | Passed (unit + integration) | Implemented | Verified (M3) |
| FR-013 | Admin deactivates a student account (soft delete) | Critical | Admin | User Management | `student`, `user` | `DELETE /users/students/{id}` | Admin: user management | BR-006 | Passed (unit + integration) | Implemented | Verified (M3) |
| FR-014 | Admin lists all teachers | Critical | Admin | User Management | `teacher`, `user` | `GET /users/teachers` | Admin: user management | — | Passed (unit + integration) | Implemented | Verified (M3) |
| FR-015 | Admin creates a new teacher account | Critical | Admin | User Management | `teacher`, `user` | `POST /users/teachers` | Admin: user management | VR-001 (email format) | Passed (unit + integration) | Implemented | Verified (M3) |
| FR-016 | Admin updates a teacher's record | Critical | Admin | User Management | `teacher`, `user` | `PUT /users/teachers/{id}` | Admin: user management | VR-009 | Passed (unit + integration) | Implemented | Verified (M3) |
| FR-017 | List exams relevant to the caller's role | Critical | All | Exam & Grading | `exam`, `class_session` | `GET /exams` | Exam list | — | Pending | Pending | Pending |
| FR-018 | Teacher creates a new exam (MCQ/short/descriptive/coding), assigns to class, sets per-question marks and time limit | Critical | Teacher | Exam & Grading | `exam`, `question`, `question_option`, `class_session` | `POST /exams` | Teacher: exam builder | VR-003, VR-004 | Pending | Pending | Pending |
| FR-019 | View exam details and questions | Critical | All | Exam & Grading | `exam`, `question`, `question_option` | `GET /exams/{id}` | Exam list, Exam room, Teacher: exam builder | — | Pending | Pending | Pending |
| FR-020 | Teacher updates an exam | Critical | Teacher | Exam & Grading | `exam`, `question`, `question_option` | `PUT /exams/{id}` | Teacher: exam builder | VR-003, VR-004 | Pending | Pending | Pending |
| FR-021 | Teacher or Admin deletes an unpublished exam | Critical | Teacher, Admin | Exam & Grading | `exam` | `DELETE /exams/{id}` | Teacher: exam builder | BR-003 | Pending | Pending | Pending |
| FR-022 | Student submits answers to an exam within the configured time limit | Critical | Student | Exam & Grading | `exam_submission`, `answer` | `POST /exams/{id}/submit` | Exam room | VR-004 (time limit enforcement) | Pending | Pending | Pending |
| FR-023 | Teacher grades a submitted exam, awards partial marks, gives per-question feedback | Critical | Teacher | Exam & Grading | `exam_submission`, `answer`, `question_grade` | `POST /exams/{id}/grade` | Teacher: grading interface | VR-006 | Pending | Pending | Pending |
| FR-024 | Teacher or Admin retrieves all results for a given exam | Critical | Teacher, Admin | Exam & Grading | `exam_submission`, `question_grade` | `GET /exams/{id}/results` | Teacher: grading interface | — | Pending | Pending | Pending |
| FR-025 | Student views marks per question only after results are published | Critical | Student | Exam & Grading | `question_grade`, `result` | `GET /exams/{id}/results` (student-scoped) | Results view | BR-001 | Pending | Pending | Pending |
| FR-026 | Student views own attendance summary, filterable by subject/date, with current percentage | Critical | Student | Attendance | `attendance_record` | `GET /attendance/me` | Attendance page | — | Pending | Pending | Pending |
| FR-027 | Teacher marks attendance for a class and date | Critical | Teacher | Attendance | `attendance_record` | `POST /attendance` | Teacher: attendance marker | VR-005 | Pending | Pending | Pending |
| FR-028 | Teacher or Admin retrieves attendance for a specific class | Critical | Teacher, Admin | Attendance | `attendance_record` | `GET /attendance/{classId}` | Teacher: attendance marker | — | Pending | Pending | Pending |
| FR-029 | Teacher or Admin corrects an existing attendance record | Critical | Teacher, Admin | Attendance | `attendance_record` | `PUT /attendance/{id}` | Teacher: attendance marker | VR-005 | Pending | Pending | Pending |
| FR-030 | Admin generates attendance reports by department or semester | High | Admin | Attendance / Reporting | `attendance_record`, `department`, `semester` | `GET /attendance/reports` | Admin: reports | — | Pending | Pending | Pending |
| FR-031 | System issues low-attendance warnings automatically | High | Student | Attendance | `attendance_record`, `notification` | (derived server-side; surfaces via `GET /attendance/me`, `notification` module) | Attendance page, Notifications panel | BR-008 (threshold undefined — Requirement_Analysis.md §14 item 4) | Pending | Pending | Pending |
| FR-032 | Parent views child's attendance record, receives absence alerts | High | Parent | Attendance / Parent Portal | `attendance_record`, `parent_student_link`, `notification` | `GET /attendance/{classId}` (parent-scoped, per BR-007) | Parent: child attendance/results/schedule/fee view | BR-007 | Pending | Pending | Pending |
| FR-033 | Student views own results across all semesters, incl. grades and GPA | Critical | Student | Results & Transcript | `result`, `semester` | `GET /results/me` | Results view | — | Pending | Pending | Pending |
| FR-034 | Teacher submits graded results for an exam for admin approval | Critical | Teacher | Results & Transcript | `result` | `POST /results/{examId}/submit` | Teacher: grading interface | BR-002 | Pending | Pending | Pending |
| FR-035 | Admin approves and publishes submitted results | Critical | Admin | Results & Transcript | `result` | `POST /results/{id}/approve` | Admin: result approval | BR-002 | Pending | Pending | Pending |
| FR-036 | Student or Admin downloads official PDF transcript with university seal | High | Student, Admin | Results & Transcript | `result`, `student` | `GET /results/{studentId}/transcript` | Results view | — | Pending | Pending | Pending |
| FR-037 | Parent views child's published results | High | Parent | Results & Transcript / Parent Portal | `result`, `parent_student_link` | `GET /results/me` (parent-scoped, per BR-007) | Parent: child attendance/results/schedule/fee view | BR-007 | Pending | Pending | Pending |
| FR-038 | Student or Parent retrieves fee status and payment history | Medium | Student, Parent | Fee Management (Optional) | `fee_structure`, `payment`, `invoice` | `GET /fees/me` | Fee centre | — | Pending | Pending | Pending |
| FR-039 | Admin defines a fee structure per semester or department | Medium | Admin | Fee Management (Optional) | `fee_structure` | `POST /fees` | Admin: fee dashboard | VR-008 | Pending | Pending | Pending |
| FR-040 | Admin records a payment | Medium | Admin | Fee Management (Optional) | `payment` | `POST /fees/payments` | Admin: fee dashboard | VR-008 | Pending | Pending | Pending |
| FR-041 | Admin or Parent retrieves payment history for a specific student | Medium | Admin, Parent | Fee Management (Optional) | `payment`, `parent_student_link` | `GET /fees/payments/{studentId}` | Fee centre, Admin: fee dashboard | BR-007 (for Parent) | Pending | Pending | Pending |
| FR-042 | Student or Admin downloads invoice as PDF | Medium | Student, Admin | Fee Management (Optional) | `invoice` | `GET /fees/invoices/{id}` | Fee centre | — | Pending | Pending | Pending |
| FR-043 | Admin lists all overdue accounts | Medium | Admin | Fee Management (Optional) | `invoice` | `GET /fees/overdue` | Admin: fee dashboard | — | Pending | Pending | Pending |
| FR-044 | System sends due-date reminders and overdue notices | Medium | Student, Parent | Fee Management (Optional) / Notification | `invoice`, `notification` | (derived server-side; surfaces via `notification` module) | Fee centre, Notifications panel | BR-010 (timing undefined — Requirement_Analysis.md §14 item 5) | Pending | Pending | Pending |
| FR-045 | Student or Teacher views own timetable | Critical | Student, Teacher | Scheduling | `schedule_entry`, `class_session` | `GET /schedule/me` | Timetable | — | Passed (unit + integration) | Implemented | Verified (M4) |
| FR-046 | Admin creates a class schedule entry | Critical | Admin | Scheduling | `schedule_entry` | `POST /schedule` | (Admin schedule management — not separately listed as a screen in Requirement_Analysis.md §7; implied within Timetable/Admin scope) | VR-007 | Passed (unit + integration) | Implemented | Verified (M4) |
| FR-047 | Admin updates a schedule entry | Critical | Admin | Scheduling | `schedule_entry` | `PUT /schedule/{id}` | (Admin schedule management — see FR-046 note) | VR-007 | Passed (unit + integration) | Implemented | Verified (M4) |
| FR-048 | Admin removes a class from the schedule | Critical | Admin | Scheduling | `schedule_entry` | `DELETE /schedule/{id}` | (Admin schedule management — see FR-046 note) | — | Passed (unit + integration) | Implemented | Verified (M4) |
| FR-049 | Admin detects scheduling conflicts (double-booked rooms/teachers) before publishing | Critical | Admin | Scheduling | `schedule_entry`, `room`, `teacher` | `GET /schedule/conflicts` | (Admin schedule management — see FR-046 note) | BR-005 | Passed (unit + integration) | Implemented | Verified (M4) |
| FR-050 | Teacher requests a timetable change, routed to Admin for confirmation | High | Teacher, Admin | Scheduling | `schedule_change_request` | `POST /schedule/change-requests`, `POST /schedule/change-requests/{id}/resolve` (gap-fill, not in proposal §6 — see note below, corrected to Milestone 4) | Timetable (Teacher request action) | BR-004 | Passed (unit + integration) | Implemented | Verified (M4) |
| FR-051 | System sends instant notifications when a student's schedule changes | High | Student | Scheduling / Notification | `schedule_entry`, `notification` | (derived server-side; surfaces via `notification` module) | Timetable, Notifications panel | — | Pending | Not implemented | Pending — the `notification` table and dispatch mechanism don't exist until Milestone 9; a schedule-change event has nothing to notify through yet. Not deferred silently — same pattern as M3's FR-008 |
| FR-052 | System generates real-time notifications for result publication, schedule changes, attendance warnings, fee due dates | High | All | Notification | `notification` | (no endpoint listed in proposal §6 — gap, see Requirement_Analysis.md §8 note; addressed as `GET/PUT /notifications*` in Implementation_Roadmap.md M9) | Notifications panel | — | Pending | Pending | Pending |
| FR-053 | Any authenticated user views a notification feed with read/unread state | High | All | Notification | `notification` | (no endpoint listed in proposal §6 — gap; addressed as `GET /notifications`, `PUT /notifications/{id}/read` in Implementation_Roadmap.md M9) | Notifications panel | — | Pending | Pending | Pending |
| FR-054 | Admin generates result reports (grade distributions, pass/fail counts) by department/semester/student | High | Admin | Reporting | `result`, `department`, `semester`, `student` | `GET /results/reports` (gap-fill, added during Project Readiness Audit) | Admin: Reports | — | Pending | Pending | Pending |
| FR-055 | Admin generates fee/revenue reports by department/semester/student | Medium | Admin | Reporting / Fee Management (Optional) | `payment`, `fee_structure`, `invoice`, `department`, `semester`, `student` | `GET /fees/reports` (gap-fill, added during Project Readiness Audit) | Admin: Reports | — | Pending | Pending | Pending |
| FR-056 | Admin manually triggers an overdue fee notice, individually or in bulk | Medium | Admin | Fee Management (Optional) / Notification | `invoice`, `student`, `notification` | `POST /fees/overdue/notify` (gap-fill, added during Project Readiness Audit) | Admin: Fee Dashboard | — | Pending | Pending | Pending |

---

## B. Non-Functional Requirements

| Req ID | Requirement Description | Priority | User Role | Module | Database Tables | Backend API | Frontend Pages | Validation Rules | Testing Status | Implementation Status | Verification Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NFR-001 | Enforce role-based access control at the API layer for every endpoint, not only in the UI | Critical | All | Authentication & Authorization (cross-cutting) | `user` | All protected endpoints (RBAC middleware, `System_Architecture.md` §6) | All pages (client-side hiding is UX only) | — | Passed (unit + integration, incl. 401/403/deactivated-user negative tests) | Implemented (`get_current_user`, `require_roles`; retrofitted onto all 12 M1 reference-data endpoints) | Verified (M2) — applies to every endpoint that exists as of M2; re-verify per-endpoint as later milestones add new protected routes |
| NFR-002 | Student can only access own academic, attendance, and fee data | Critical | Student | Authentication & Authorization (cross-cutting) | `student`, `attendance_record`, `result`, `fee_structure`/`payment`/`invoice` | `GET /users/me`, `GET /attendance/me`, `GET /results/me`, `GET /fees/me` (ownership checks) | Profile page, Attendance page, Results view, Fee centre | — | Pending | Pending | Pending |
| NFR-003 | Parent can only access data belonging to their own linked child/children | Critical | Parent | Authentication & Authorization / Parent Portal (cross-cutting) | `parent_student_link` | `GET /attendance/{classId}`, `GET /results/me`, `GET /fees/payments/{studentId}` (linkage checks, BR-007) | Parent: child attendance/results/schedule/fee view | — | Pending | Pending | Pending |
| NFR-004 | Use JWT bearer tokens with short-lived access tokens and refresh-token rotation | Critical | All | Authentication & Authorization | `user` | `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout` | Login | — | Passed (unit + integration, incl. rotated-token-reuse rejection) | Implemented (`current_refresh_token_jti`/`refresh_token_expires_at` single-active-session design — see `Database_Design.md` §6.1 M2 note) | Verified (M2) |
| NFR-005 | All API endpoints return JSON and are namespaced under `/api/v1` | Critical | All | Authentication & Authorization (cross-cutting) | — | All endpoints | — | — | Pending | Pending | Pending |
| NFR-006 | Database enforces relational integrity (FKs, constraints) across users, courses, exams, attendance, results, fees, schedules | Critical | — (system-level) | All (cross-cutting) | All tables per `Database_Design.md` §5 | — | — | — | Pending | Pending | Pending |
| NFR-007 | Database schema changes managed through versioned Alembic migrations | Critical | — (system-level) | All (cross-cutting) | All tables | — | — | — | Pending | Pending | Pending |
| NFR-008 | Web app is an SPA with loading and error states for all async operations | High | All | User Management / Frontend (cross-cutting) | — | — (frontend concern, backed by all API endpoints) | All pages | — | Pending | Pending | Pending |
| NFR-009 | Notification delivery is near real-time | High | All | Notification | `notification` | (see FR-052/FR-053 gap note) | Notifications panel | — | Pending | Pending | Pending |
| NFR-010 | Frontend code is type-safe (TypeScript) and component-driven | High | — (system-level) | Frontend (cross-cutting) | — | — | All pages | — | Pending | Pending | Pending |
| NFR-011 | Styling follows a consistent utility-first system (TailwindCSS) | Medium | — (system-level) | Frontend (cross-cutting) | — | — | All pages | — | Pending | Pending | Pending |
| NFR-012 | Web frontend deployable via CDN, decoupled from backend API deployment | High | — (system-level) | Deployment (cross-cutting) | — | — | — | — | Pending | Pending | Pending |
| NFR-013 | Delivered project includes sufficient code documentation | Medium | — (system-level) | Documentation (cross-cutting) | — | — | — | — | Pending | Pending | Pending |
| NFR-014 | Result publication and fee overdue actions follow an approval workflow, not immediate visibility | Critical | Teacher, Admin | Results & Transcript / Fee Management | `result`, `invoice` | `POST /results/{examId}/submit`, `POST /results/{id}/approve` | Admin: result approval, Results view | BR-002 | Pending | Pending | Pending |
| NFR-015 | Scheduling subsystem prevents double-booking of rooms/teachers at creation/update time | Critical | Admin | Scheduling | `schedule_entry` | `POST /schedule`, `PUT /schedule/{id}`, `GET /schedule/conflicts` | Timetable | BR-005 | Passed (unit + integration, incl. overlapping-but-different-start-time case) | Implemented | Verified (M4) |
| NFR-016 | Attendance percentage and fee status computable/queryable on demand, not manually recalculated | High | Student, Parent, Admin | Attendance / Fee Management | `attendance_record`, `fee_structure`, `payment`, `invoice` | `GET /attendance/me`, `GET /fees/me` | Attendance page, Fee centre | — | Pending | Pending | Pending |

---

## Summary Counts

| Category | Count |
|---|---|
| Functional Requirements (FR) traced | 56 |
| Non-Functional Requirements (NFR) traced | 16 |
| **Total requirements traced** | **72** |
| Critical priority | 33 |
| High priority | 22 |
| Medium priority | 17 |
| Low priority | 0 |

*(FR-054–FR-056 were added during the Project Readiness Audit to close the Admin Reports/overdue-notify gap — see `Requirement_Analysis.md` §14 items 15–16.)*

All rows above are initialized with:
- **Testing Status:** Pending
- **Implementation Status:** Pending
- **Verification Status:** Pending

These three columns must be updated in place as each requirement moves through the milestones defined in `Implementation_Roadmap.md` — do not delete or renumber rows as statuses change, to preserve traceability history.

## Known Gaps Affecting Traceability

The following items are cross-referenced from `Requirement_Analysis.md` §14 because they directly affect the "Backend API" or "Frontend Pages" columns above and could not be resolved without inventing scope:

- **FR-052, FR-053, NFR-009**: No notification-management endpoints (`GET /notifications`, `PUT /notifications/{id}/read`) are listed in the proposal's §6 API spec, despite being required by the corresponding features. Marked with a gap note rather than a fabricated endpoint; `Implementation_Roadmap.md` Milestone 9 proposes the missing endpoints as an implementation necessity.
- **FR-050**: No schedule-change-request endpoint is listed in the proposal's §6 API spec. Marked with a gap note rather than a fabricated endpoint; `Implementation_Roadmap.md` **Milestone 4** (not Milestone 9 — corrected during the M4 pre-implementation review; this line previously grouped FR-050 with the Milestone 9 notification gaps above, which was inconsistent with `API_Contract.md` §7.6-7.7's own text stating both endpoints are "implemented per Implementation_Roadmap.md Milestone 4," and with `schedule_change_request.py` being an M4 file) proposes `POST /schedule/change-requests` and `POST /schedule/change-requests/{id}/resolve` as an implementation necessity.
- **FR-046–FR-049**: No dedicated "Admin schedule management" screen is named in `Requirement_Analysis.md` §7; scheduling admin actions are assumed to live within the Timetable page's admin-mode, consistent with how Section 7 does not enumerate a separate screen for it.
- **`class_session`/`enrollment` creation (no FR number — not a proposal requirement):** `POST /schedule/class-sessions` and `POST /schedule/enrollments` (Milestone 4) are Derived Engineering Additions, not traceable to any proposal FR — both `class_session` and `enrollment` are referenced as foreign keys throughout the Scheduling/Exams/Attendance endpoints above but had no creation endpoint anywhere in the source documents, and without them `POST /schedule` (FR-046) cannot be exercised. Confirmed with the user during the Milestone 4 pre-implementation review; see `Proposal_vs_Engineering_Additions.md` for the full classification.
- **FR-032, FR-037, FR-038, FR-041**: Parent-facing data access reuses Student-facing endpoints in a parent-scoped mode (per `System_Architecture.md` §6), since the proposal does not define separate Parent-only endpoints for attendance/results — only fees has explicit Parent access in the Access column (`Requirement_Analysis.md` §8).
- **FR-031, BR-008**: Low-attendance warning threshold is undefined; traceability to a specific validation/business rule is recorded but the rule's parameter is not yet confirmed.
- **FR-054, FR-055**: No result-reports or fee-reports endpoints, and no "Reports" screen, are listed in the proposal's §6/§7, despite the Admin "Reports" feature (§5) explicitly naming result and fee reporting alongside attendance reporting. Identified and closed during the Project Readiness Audit — see `Requirement_Analysis.md` §14 item 15.
- **FR-056**: No endpoint is listed for an Admin to manually "send overdue notices" (§5), distinct from FR-044's automatic reminders. Identified and closed during the Project Readiness Audit — see `Requirement_Analysis.md` §14 item 16.
