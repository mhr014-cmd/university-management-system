# Requirements Analysis Document
## University Management System (ICT Education)

**Source document:** `docs/product_proposal.pdf` (Version 1.0 — Final Draft)
**Prepared by:** ICT Bangladesh, AI-Powered Software Engineering Batch 26/3
**Submission Deadline:** July 13, 2026

---

## 1. Executive Summary

The University Management System ("ICT Education") is a web/mobile platform with a REST API backend that consolidates university operations — attendance, exams, results, fees, and scheduling — into a single system, replacing disconnected spreadsheets, email-based result distribution, and siloed finance tools.

The system serves four roles: **Student**, **Teacher**, **Admin**, and **Parent**, each with distinct, enforced permissions. The proposal specifies a FastAPI (Python 3.12) + PostgreSQL backend, a React 18 + TypeScript single-page frontend, and JWT-based role authentication.

The project is graded out of 100 marks: 80 for the main deliverable (API, web app, database, code quality) and 20 for assignments/attendance during the course. Fee management and PDF-invoice/transcript downloads are marked **Optional** in the source proposal but are still fully specified with dedicated endpoints and screens — this ambiguity is flagged in Section 14.

This document translates the proposal's narrative and tables into a structured, numbered requirements baseline suitable for design and implementation planning.

**Post-audit note:** A Project Readiness Audit (see the audit findings recorded across this document, `System_Architecture.md`, `Database_Design.md`, `API_Contract.md`, `UI_Wireframes.md`, `Requirement_Traceability_Matrix.md`, and `Implementation_Roadmap.md`) added FR-054–FR-056 to close a gap in the proposal's own Admin "Reports" and "send overdue notices" capabilities, which had incomplete API/screen coverage in the original pass. The requirement count is now 56 FRs and 16 NFRs (72 total).

---

## 2. Functional Requirements

### Authentication & Session
- **FR-001**: The system shall allow any user to log in with email and password via `POST /auth/login`, returning an access token and a refresh token.
- **FR-002**: The system shall allow a client to refresh an expired access token via `POST /auth/refresh` without requiring re-entry of credentials.
- **FR-003**: The system shall allow an authenticated user to log out and invalidate their current session via `POST /auth/logout`.
- **FR-004**: The system shall allow any authenticated user to change their own password via `PUT /auth/password`.
- **FR-005**: The system shall redirect users to a role-specific dashboard immediately after successful login.

### Profile Management
- **FR-006**: The system shall allow any authenticated user to retrieve their own profile via `GET /users/me`.
- **FR-007**: The system shall allow any authenticated user to update their own profile (personal information, profile photo) via `PUT /users/me`.
- **FR-008**: A student shall be able to view their academic history in addition to personal profile data.

### User Management (Admin)
- **FR-009**: An Admin shall be able to list all students via `GET /users/students`.
- **FR-010**: An Admin shall be able to create a new student account via `POST /users/students`.
- **FR-011**: An Admin or Teacher shall be able to retrieve a single student's record via `GET /users/students/{id}`.
- **FR-012**: An Admin shall be able to update a student's record via `PUT /users/students/{id}`.
- **FR-013**: An Admin shall be able to deactivate a student account via `DELETE /users/students/{id}` (soft delete/deactivation, not permanent erasure).
- **FR-014**: An Admin shall be able to list all teachers via `GET /users/teachers`.
- **FR-015**: An Admin shall be able to create a new teacher account via `POST /users/teachers`.
- **FR-016**: An Admin shall be able to update a teacher's record via `PUT /users/teachers/{id}`.

### Exams
- **FR-017**: Any authenticated user shall be able to list exams relevant to their role via `GET /exams`.
- **FR-018**: A Teacher shall be able to create a new exam via `POST /exams`, including MCQ, short answer, descriptive, and coding question types, assigned to a specific class, with per-question marks and an overall time limit.
- **FR-019**: Any authenticated user shall be able to view exam details and questions via `GET /exams/{id}`.
- **FR-020**: A Teacher shall be able to update an exam via `PUT /exams/{id}`.
- **FR-021**: A Teacher or Admin shall be able to delete an exam via `DELETE /exams/{id}`, restricted to exams not yet published.
- **FR-022**: A Student shall be able to submit answers to an exam via `POST /exams/{id}/submit`, with the exam interface enforcing the configured time limit.
- **FR-023**: A Teacher shall be able to grade a submitted exam via `POST /exams/{id}/grade`, awarding partial marks and per-question written feedback.
- **FR-024**: A Teacher or Admin shall be able to retrieve all results for a given exam via `GET /exams/{id}/results`.
- **FR-025**: A Student shall be able to view their marks per question only after results for that exam are published.

### Attendance
- **FR-026**: A Student shall be able to view their own attendance summary via `GET /attendance/me`, filterable by subject or date, showing current percentage.
- **FR-027**: A Teacher shall be able to mark attendance for a class and date via `POST /attendance`.
- **FR-028**: A Teacher or Admin shall be able to retrieve attendance for a specific class via `GET /attendance/{classId}`.
- **FR-029**: A Teacher or Admin shall be able to correct an existing attendance record via `PUT /attendance/{id}`.
- **FR-030**: An Admin shall be able to generate attendance reports (by department or semester) via `GET /attendance/reports`.
- **FR-031**: The system shall issue low-attendance warnings to students automatically based on the tracked percentage.
- **FR-032**: A Parent shall be able to view their child's attendance record and receive automatic alerts for absences.

### Results & Transcripts
- **FR-033**: A Student shall be able to view their own results across all semesters via `GET /results/me`, including grades and GPA per semester.
- **FR-034**: A Teacher shall be able to submit graded results for a given exam for admin approval via `POST /results/{examId}/submit`.
- **FR-035**: An Admin shall be able to approve and publish submitted results via `POST /results/{id}/approve`.
- **FR-036**: A Student or Admin shall be able to download an official PDF transcript (with university seal) via `GET /results/{studentId}/transcript`.
- **FR-037**: A Parent shall be able to view their child's published results.

### Fees (Optional)
- **FR-038**: A Student or Parent shall be able to retrieve fee status and payment history via `GET /fees/me`.
- **FR-039**: An Admin shall be able to define a fee structure (per semester or department) via `POST /fees`.
- **FR-040**: An Admin shall be able to record a payment via `POST /fees/payments`.
- **FR-041**: An Admin or Parent shall be able to retrieve payment history for a specific student via `GET /fees/payments/{studentId}`.
- **FR-042**: A Student or Admin shall be able to download an invoice as PDF via `GET /fees/invoices/{id}`.
- **FR-043**: An Admin shall be able to list all overdue accounts via `GET /fees/overdue`.
- **FR-044**: The system shall send due-date reminders and overdue notices to students and parents.

### Scheduling
- **FR-045**: A Student or Teacher shall be able to view their own timetable via `GET /schedule/me`.
- **FR-046**: An Admin shall be able to create a class schedule entry via `POST /schedule`.
- **FR-047**: An Admin shall be able to update a schedule entry via `PUT /schedule/{id}`.
- **FR-048**: An Admin shall be able to remove a class from the schedule via `DELETE /schedule/{id}`.
- **FR-049**: An Admin shall be able to detect scheduling conflicts (double-booked rooms or teachers) via `GET /schedule/conflicts` before publishing a timetable.
- **FR-050**: A Teacher shall be able to request a change to their timetable; the request shall be routed to Admin for confirmation before taking effect.
- **FR-051**: The system shall send instant notifications to students when their schedule changes.

### Notifications
- **FR-052**: The system shall generate real-time notifications for: result publication, schedule changes, low-attendance warnings, and fee due dates.
- **FR-053**: Any authenticated user shall be able to view a notification feed with read/unread state.

### Reporting
*(Added during Project Readiness Audit — see §14 items 15–16. The proposal's Admin "Reports" feature (§5: "Generate attendance, result, and fee reports by department, semester, or individual student") was only partially captured: attendance reporting became FR-030, but result and fee reporting were missed. This section closes that gap.)*
- **FR-054**: An Admin shall be able to generate result reports (grade distributions, pass/fail counts) by department, semester, or individual student.
- **FR-055**: An Admin shall be able to generate fee/revenue reports (collected, outstanding, overdue totals) by department, semester, or individual student.
- **FR-056**: An Admin shall be able to trigger an overdue fee notice for an individual student or in bulk for all currently overdue accounts (proposal §5: Admin "send[s] overdue notices" — a manual capability distinct from the automatic reminders in FR-044).

---

## 3. Non-Functional Requirements

- **NFR-001 (Access Control)**: The system shall enforce role-based access control (Student, Teacher, Admin, Parent) at the API layer for every endpoint, not only in the UI.
- **NFR-002 (Data Isolation)**: The system shall ensure a student can only access their own academic, attendance, and fee data — never another student's, a teacher's, or administrative records.
- **NFR-003 (Data Isolation — Parent)**: The system shall ensure a parent can only access data belonging to their own linked child/children.
- **NFR-004 (Authentication Security)**: The system shall use JWT bearer tokens for authentication, with short-lived access tokens and a refresh-token rotation mechanism.
- **NFR-005 (API Format)**: All API endpoints shall return JSON responses and shall be namespaced under `/api/v1`.
- **NFR-006 (Data Integrity)**: The database design shall enforce relational integrity (foreign keys, constraints) between users, courses, exams, attendance, results, fees, and schedules.
- **NFR-007 (Schema Evolution)**: Database schema changes shall be managed through versioned migrations (Alembic), not manual/ad-hoc changes.
- **NFR-008 (Usability)**: The web application shall be a single-page application providing loading and error states for all asynchronous operations (per React Query usage).
- **NFR-009 (Real-Time Behavior)**: Notification delivery (result publishing, schedule changes, attendance warnings, fee due dates) shall be near real-time.
- **NFR-010 (Maintainability)**: Frontend code shall be type-safe (TypeScript) and component-driven to remain maintainable at scale.
- **NFR-011 (Consistency)**: Styling shall follow a consistent utility-first system (TailwindCSS) to avoid visual inconsistency across screens.
- **NFR-012 (Deployment)**: The web frontend shall be deployable via CDN distribution, decoupled from the backend API deployment.
- **NFR-013 (Documentation)**: The delivered project shall include code documentation sufficient for the "Code quality, documentation, and deployment" grading component.
- **NFR-014 (Auditability)**: Result publication and fee overdue actions shall follow an approval workflow (submit → approve/reject) rather than being immediately visible/final, to prevent unreviewed data reaching students/parents.
- **NFR-015 (Conflict Prevention)**: The scheduling subsystem shall prevent double-booking of rooms or teachers at the point of schedule creation/update.
- **NFR-016 (Availability of Core Data)**: Attendance percentage and fee status shall be computable/queryable on demand rather than requiring manual recalculation.

---

## 4. User Roles

| Role | Description |
|---|---|
| **Student** | Primary end user; consumes exams, attendance, results, fees, schedule, and notifications for themselves only. |
| **Teacher** | Manages the academic side: exam creation/grading, attendance marking, result submission, schedule change requests. |
| **Admin** | System controller: user lifecycle, result approval, fee structures, timetable publishing, reporting. |
| **Parent** | Read-only access to their own child's attendance, results, schedule, and (optionally) fee status. |

---

## 5. Permissions of Each Role

### Student
- View/update own profile, photo, password
- View upcoming exams; sit exams in-app (MCQ, written, coding)
- View own marks per question after publication
- View own attendance by subject/date and percentage; receive low-attendance warnings
- View own results/GPA per semester; download own transcript PDF
- View own fee status, invoices, payment history; receive due-date reminders
- View own timetable; receive schedule-change notifications
- Receive and read own notifications
- **Cannot** access other students', teachers', or admin data

### Teacher
- Manage own profile; view assigned courses/departments and teaching history
- Create/update/delete (if unpublished) exams; define question types, marks, time limits
- Grade exam submissions; award partial marks; give per-question feedback
- Mark and correct attendance for their classes; view per-student attendance history; generate department/semester reports
- Submit graded results for admin approval (cannot publish directly)
- View own schedule; request schedule changes (requires admin confirmation)
- **Cannot** approve/publish results, manage users, or manage fees

### Admin
- Onboard/update/deactivate student and teacher accounts
- Review and approve (or reject) submitted results before publication
- Define fee structures, track payments, view financial dashboard, send overdue notices (optional feature)
- Create/update/delete schedule entries; detect and resolve conflicts
- Generate attendance, result, and fee reports by department/semester/student
- **Full administrative access**, but should still operate within defined workflows (e.g., result approval, not bypassing teacher submission)

### Parent
- View own child's attendance record; receive absence alerts
- View own child's published results, upcoming exams, and timetable
- View own child's fee status and payment history; receive overdue notifications (optional feature)
- **Read-only** — no create/update/delete permissions anywhere in the system
- **Cannot** access data for children not linked to their account

---

## 6. Required Modules

1. **Authentication & Authorization Module** — login, token refresh, logout, password change, RBAC enforcement
2. **User Management Module** — student/teacher/parent account CRUD, profile management
3. **Exam & Grading Module** — exam builder, exam-taking interface, grading workflow
4. **Attendance Module** — marking, correction, summaries, percentage calculation, reporting
5. **Results & Transcript Module** — result submission, approval workflow, GPA computation, PDF transcript generation
6. **Fee Management Module (Optional)** — fee structure definition, payment recording, invoicing, overdue tracking
7. **Scheduling / Timetable Module** — schedule CRUD, conflict detection, change-request workflow
8. **Notification Module** — real-time alerts across results, attendance, schedule, and fees
9. **Reporting Module** — attendance/result/fee reports by department, semester, or student (Admin) (FR-030, FR-054, FR-055, FR-056)
10. **Parent Portal Module** — read-only aggregation of a linked child's attendance, results, schedule, fees

---

## 7. Required Pages

| Page | Primary Role(s) |
|---|---|
| Login | All |
| Dashboard (role-specific widgets) | All |
| Profile page | All |
| Exam list | Student, Teacher |
| Exam room (timed exam interface) | Student |
| Results view (grades, GPA, transcript download) | Student |
| Attendance page (calendar/table + percentage) | Student |
| Fee centre (balance, history, invoice download) | Student, Parent |
| Timetable (weekly grid) | Student, Teacher |
| Admin: user management | Admin |
| Admin: result approval | Admin |
| Admin: fee dashboard | Admin |
| Teacher: exam builder | Teacher |
| Teacher: grading interface | Teacher |
| Teacher: attendance marker | Teacher |
| Notifications panel | All |
| Parent: child attendance/results/schedule/fee view | Parent (implied, not explicitly named as a distinct screen in the proposal — see Section 14) |
| Admin: Reports | Admin (implied, not explicitly named as a distinct screen in the proposal — added to close the gap for FR-054/FR-055; see Section 14) |

---

## 8. Required REST APIs

Base URL: `/api/v1`

### Authentication
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `PUT /auth/password`

### Users & Profiles
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

### Exams & Grading
- `GET /exams`
- `POST /exams`
- `GET /exams/{id}`
- `PUT /exams/{id}`
- `DELETE /exams/{id}`
- `POST /exams/{id}/submit`
- `POST /exams/{id}/grade`
- `GET /exams/{id}/results`

### Attendance
- `GET /attendance/me`
- `POST /attendance`
- `GET /attendance/{classId}`
- `PUT /attendance/{id}`
- `GET /attendance/reports`

### Results & Transcripts
- `GET /results/me`
- `POST /results/{examId}/submit`
- `POST /results/{id}/approve`
- `GET /results/{studentId}/transcript`

### Fees (Optional)
- `GET /fees/me`
- `POST /fees`
- `POST /fees/payments`
- `GET /fees/payments/{studentId}`
- `GET /fees/invoices/{id}`
- `GET /fees/overdue`
- `POST /fees/overdue/notify` *(gap-fill — see note below; supports FR-056)*

### Scheduling
- `GET /schedule/me`
- `POST /schedule`
- `PUT /schedule/{id}`
- `DELETE /schedule/{id}`
- `GET /schedule/conflicts`
- `POST /schedule/change-requests` *(gap-fill — see note below; supports FR-050)*
- `POST /schedule/change-requests/{id}/resolve` *(gap-fill — see note below; supports FR-050)*

### Reports *(gap-fill — see note below; supports FR-054, FR-055)*
- `GET /results/reports`
- `GET /fees/reports`

**Note:** Several endpoints listed above with a *(gap-fill)* marker are not present in Section 6 of the original proposal, despite being required by features the proposal describes elsewhere:
- No notification-management endpoints (`GET /notifications`, `PUT /notifications/{id}/read`) are listed despite the Notifications feature (§3) and screen (§7) being explicitly required.
- No schedule-change-request endpoints are listed despite the Teacher "request schedule changes" feature (§4) being explicitly required.
- No result-reports or fee-reports endpoints are listed despite the Admin "Reports" feature (§5: "Generate attendance, result, and fee reports...") explicitly naming result and fee reporting alongside attendance reporting (only attendance reporting received an endpoint, `GET /attendance/reports`).
- No endpoint is listed for an Admin to manually trigger an overdue notice, despite §5 stating Admin capability to "send overdue notices."

See Section 14 — Unclear Items for the full discussion of each gap.

---

## 9. Business Rules

- **BR-001**: A student can only view exam question marks after the teacher has published results for that exam (FR-025).
- **BR-002**: Results must pass through a two-step workflow: Teacher submits → Admin approves → published to student/parent. Results are not visible to students until approved (FR-034, FR-035).
- **BR-003**: An exam can only be deleted while it is unpublished; once published it becomes immutable/deletion-restricted (FR-021).
- **BR-004**: Teachers cannot directly edit their own schedule; changes must be requested and confirmed by an Admin (FR-050).
- **BR-005**: The scheduling system must prevent double-booking of the same room or teacher for overlapping time slots (FR-049, NFR-015).
- **BR-006**: Student account "deletion" is a deactivation, not permanent erasure, preserving historical academic records (FR-013).
- **BR-007**: A parent's data access is scoped strictly to their own linked child/children (NFR-003).
- **BR-008**: Low-attendance warnings must be triggered automatically once a student's attendance percentage crosses an institution-defined threshold — **80%, resolved during the Milestone 5 pre-implementation review** (see Section 14 item 4 for the evidentiary basis). "Triggered" means the percentage crossing the threshold is computed and surfaced in `GET /attendance/me`'s response; actual notification dispatch depends on the `notification` module (Milestone 9) and is not implemented until then.
- **BR-009**: Pass mark for the overall course/project is 50/100; distinction is 80/100 and above (course grading rule, not a system business rule, but referenced for context).
- **BR-010**: Fee overdue notices and reminders are triggered relative to a due date (exact timing/frequency not specified — see Section 14).

---

## 10. Validation Rules

*(The proposal does not specify field-level validation rules explicitly; the following are inferred minimums necessary to satisfy the stated features and must be confirmed with stakeholders before implementation — see Section 12/14.)*

- **VR-001**: Login requires a syntactically valid email and non-empty password.
- **VR-002**: Password change requires the new password to differ from the current password and meet a minimum complexity standard (standard undefined by proposal).
- **VR-003**: Exam questions must have a positive, non-zero mark value assigned per the "Set marks per question" feature.
- **VR-004**: Exam time limits must be a positive duration.
- **VR-005**: Attendance can only be marked for a valid, existing class/session and date (no future-dated attendance beyond the current session, no duplicate marking for the same student/class/date).
- **VR-006**: Grading (partial marks) cannot exceed the maximum marks defined for a question.
- **VR-007**: Schedule entries must have a valid start/end time where start precedes end, and must reference an existing room/teacher/class.
- **VR-008**: Fee payment amounts must be positive and should not push a student's paid total beyond the defined fee structure amount (unless overpayment is explicitly permitted — unclear, see Section 14).
- **VR-009**: Role-restricted fields (e.g., account role, deactivation status) must not be editable via `PUT /users/me` (self-service profile update) — only via Admin-scoped endpoints.

---

## 11. Constraints

- **C-001**: Backend must be built with FastAPI (Python 3.12), PostgreSQL, SQLAlchemy, and Alembic — technology stack is fixed by the proposal, not open to substitution.
- **C-002**: Frontend must be built with React 18 + TypeScript, styled with TailwindCSS, and use React Query for API communication — also fixed.
- **C-003**: Authentication must use JWT bearer tokens with role-based access enforced at the API level (not only client-side).
- **C-004**: The API must be versioned under `/api/v1`.
- **C-005**: Submission deadline is **July 13, 2026** — a hard project constraint.
- **C-006**: Grading weights are fixed (Working API 30, Web app UI/RBAC 30, DB design 15, Code quality/docs/deployment 5, Assignment 10, Attendance 6, Participation 4) and should guide effort allocation.
- **C-007**: The frontend must be deployable independently from the backend (served from a CDN), implying a decoupled architecture with no server-side rendering dependency on the API.

---

## 12. Assumptions

- **A-001**: "Class" and "course" are related but distinct entities (a course has multiple class sessions); the proposal uses both terms without a formal data model, so this relationship must be defined during design.
- **A-002**: A student belongs to exactly one department/program at a time; the proposal references "department" and "semester" as organizing dimensions without defining their relationship to student/course entities.
- **A-003**: A parent account can be linked to one or more student accounts (siblings), though the proposal only describes "their child" in the singular.
- **A-004**: GPA calculation follows a standard weighted-average formula based on per-subject grades and credit hours; the proposal does not define the exact formula, so a conventional university GPA scheme is assumed.
- **A-005**: "Optional" features (Fee Management, PDF invoice/transcript downloads) are assumed to still be implemented since they have full endpoint and screen specifications — treated as a stretch/bonus scope rather than something to omit entirely.
- **A-006**: Coding-type exam questions are assumed to require only text-based code submission and manual/rubric-based teacher grading — no automated code execution or judge system is assumed, since none is described.
- **A-007**: Notifications are assumed to require at least in-app delivery (notification panel); email/SMS/push delivery is not confirmed as in-scope.
- **A-008**: "Admin" is treated as a single flat role; the proposal does not distinguish between super-admin and department-level admin.
- **A-009**: The Teacher "Profile & courses" feature's requirement to "view assigned courses and departments, see their full teaching history" (§4) is assumed to be satisfied by combining the existing `GET /users/me` (department), `GET /schedule/me` (current and, with a `semester_id` filter, past class assignments), and `GET /exams` (Teacher-scoped) endpoints, rather than requiring a new dedicated endpoint — no separate FR/endpoint was added for this, since the capability is fully reachable through existing, already-specified endpoints.

---

## 13. Risks

- **R-001 (Scope size vs. deadline)**: The full feature set (4 roles, 6+ modules, ~35 API endpoints, ~16 screens) is substantial for the stated deadline; risk of incomplete delivery if not prioritized carefully against the grading breakdown.
- **R-002 (Undefined thresholds/rules)**: Several business rules (attendance warning threshold, overdue notice timing, GPA formula, overpayment handling) are unspecified, risking incorrect assumptions that diverge from grader/stakeholder expectations.
- **R-003 (Approval workflow complexity)**: The result submit→approve→publish workflow and schedule request→confirm workflow add state-machine complexity that is easy to under-implement (e.g., missing reject/revision paths).
- **R-004 (RBAC enforcement gaps)**: With four roles and ~35 endpoints, inconsistent enforcement of role checks at the API layer is a realistic risk, particularly for nested resources like `/fees/payments/{studentId}` (Admin, Parent) where parent-child linkage must be verified, not just role.
- **R-005 (PDF generation complexity)**: Transcript and invoice PDF generation (with university seal) adds a non-trivial technical dependency not covered by the core tech stack description.
- **R-006 (Real-time notification infrastructure)**: "Instant"/"real-time" notifications imply WebSocket or push infrastructure not mentioned in the technology stack, which is a build risk if underestimated.
- **R-007 (Optional scope ambiguity)**: Marking Fee Management as "Optional" while grading it under the 30-mark "Web application" and 30-mark "API" line items (which do not exclude fees) creates risk of misallocating effort — see also Section 14.
- **R-008 (Coding-question grading)**: In-app "practical coding" exams imply a code editor/sandbox UI; without a defined execution environment, grading is manual only, which should be validated with the instructor.

---

## 14. Anything Unclear in the Proposal

1. **"Optional" features are inconsistently scoped.** Fee Management (Admin) and Fee status (Parent) are labeled "(Optional)" in Section 5, and Fees endpoints are listed under "Fees (Optional)" in Section 6, yet the grading breakdown in Section 2 does not carve out separate marks for fees — it's folded into the general "API" (30) and "Web application" (30) marks. It is unclear whether omitting fee management would cause a proportional mark deduction or is truly zero-risk to skip.
2. **No dedicated Parent portal screen is listed** in Section 7's "Web application screens," even though Section 5 defines three Parent-facing features (attendance summary, results & schedule, fee status). It's unclear whether Parent views reuse the Student screens in read-only mode or require entirely separate screens.
3. **No notification API endpoints are specified** in Section 6, despite Notifications being a required feature (Section 3) and a required screen (Section 7). It's unclear how notifications are created, fetched, or marked read/unread via the API.
4. ~~**Low-attendance warning threshold is not defined**~~ **Resolved during the Milestone 5 pre-implementation review.** The proposal's own §6 API spec never states a number, but `UI_Wireframes.md` shows "Below 80%" as the warning threshold in two independent mockups (the Attendance page's percentage badge and the Notifications panel's example alert) — treated as the de facto documented value rather than an arbitrary implementation choice. BR-008/FR-031 implement 80% as the threshold.
5. **Fee due-date reminder and overdue notice timing/frequency is not defined** (e.g., how many days before/after due date).
6. **GPA calculation formula is not defined** — whether it's credit-weighted, simple average, or follows a specific grading scale (4.0, letter grades, percentage).
7. **The relationship between "class," "course," "subject," and "department" is not formally defined** — these terms are used interchangeably across sections without a clear entity model.
8. **Parent-to-student linkage mechanism is not described** — how a parent account gets associated with a specific student account is not specified (admin-created link? invite code? self-registration?).
9. **"Practical coding" exam questions** — it is unclear whether any code execution/auto-grading is expected, or if these are graded manually like written questions.
10. **Mobile app scope is stated on the cover page** ("Platform: Web/Mobile App + REST API") but Section 7 only describes a web SPA; no native/mobile-specific requirements, screens, or technology are given anywhere in the document. It's unclear if "Mobile" refers to a responsive web app or a separate native/hybrid app.
11. **"Code quality, documentation, and deployment — 5 marks (Optional)"** — the word "Optional" next to a marked grading line item is contradictory; unclear if these 5 marks are skippable or just lower priority.
12. **Data retention / deactivation behavior is not specified** — when a student or teacher account is "deactivated," it's unclear whether their historical data (results, attendance) remains visible to Admin/reports or is also hidden.
13. **No password policy, session/token expiry durations, or rate-limiting requirements are specified.**
14. **No non-functional performance targets are given** (expected concurrent users, response time SLAs, uptime requirements) despite the system being described as "production-grade."
15. **The Admin "Reports" feature (§5) has no dedicated screen or full API coverage.** The proposal states Admin can "Generate attendance, result, and fee reports by department, semester, or individual student," but §7 (Web application screens) names no "Reports" screen, and §6 (API) only provides `GET /attendance/reports` — result and fee reporting have no corresponding endpoint in the original proposal. Resolved during the Project Readiness Audit by adding FR-054/FR-055, gap-fill endpoints `GET /results/reports` and `GET /fees/reports`, and an "Admin: Reports" screen (see Requirement_Traceability_Matrix.md and API_Contract.md).
16. **The Admin "send overdue notices" capability (§5) has no backing endpoint or explicit manual/automatic distinction.** FR-044 (automatic due-date reminders/overdue notices) and the manually-triggered "send overdue notices" phrase in §5's Fee management row could be the same feature or two different ones — the proposal doesn't distinguish. Resolved during the Project Readiness Audit by treating them as two capabilities: FR-044 (automatic) and FR-056 (manual, Admin-triggered, individual or bulk) with a new gap-fill endpoint `POST /fees/overdue/notify`.
17. **Attendance percentage formula is not defined** — whether "late" counts toward presence, and whether "excused" absences count against the denominator at all, is left unspecified. **Resolved during the Milestone 5 implementation as a documented engineering assumption** (no wireframe or contract evidence exists for this one, unlike BR-008's threshold): `present` and `late` both count as attended; `excused` is excluded from both the numerator and denominator entirely (an excused absence neither helps nor hurts the percentage); `absent` counts against it. Implemented in `backend/app/services/attendance_service.py`. Revisit if the actual institution's policy is ever specified.
