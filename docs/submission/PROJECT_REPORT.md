# University Management System (ICT Education)
## Project Report

**Author:** Mahabbat Hossain
**Project type:** Full-stack web application (REST API + Single-Page Application)

> This report describes the system exactly as implemented. Every figure (endpoint count, table count, test count) is drawn from the current codebase and cross-referenced against [`TEST_REPORT.md`](TEST_REPORT.md), [`API_DOCUMENTATION.md`](API_DOCUMENTATION.md), and [`DATABASE_DESIGN.md`](DATABASE_DESIGN.md) in this same documentation package. No feature described below is planned, partial, or aspirational — where a capability was deliberately not built, it is named explicitly in the Limitations section rather than omitted.

---

## 1. Abstract

Universities routinely manage attendance, examinations, results, fees, and scheduling using disconnected tools — spreadsheets for attendance, email for result distribution, siloed finance software for fees — producing data that is difficult to audit, easy to lose, and impossible to view holistically. This project implements the **University Management System (ICT Education)**, a role-based web platform that consolidates these operations into a single system serving four roles — Student, Teacher, Parent, and Admin — each restricted to exactly the data and actions their role permits, enforced at the server, not merely hidden in the interface.

The system is built as a decoupled two-tier application: a FastAPI (Python 3.12) REST API backend, layered strictly into Router, Service, and Repository tiers, backed by a PostgreSQL database managed through SQLAlchemy and Alembic; and a React 18 + TypeScript single-page frontend using TanStack React Query for all server-state management. The implementation comprises 82 REST endpoints across 11 domains, 26 relationally-constrained database tables, and a verified test suite of 477 backend tests and 61 frontend component tests, all passing. Core capabilities include JWT-based authentication with role-based access control and per-request ownership verification, class scheduling with conflict detection and a Teacher-initiated change-request/Admin-approval workflow, attendance tracking with live-computed percentages and automatic low-attendance alerts, timed exam-taking with per-question grading across four question types, a result submission-approval-publication workflow with credit-weighted GPA and PDF transcripts, an optional fee module with auto-generated invoices and payment tracking, and an event-driven notification system reaching both students and their linked parents. The report documents the system's requirements, architecture, database design, module structure, security model, and verified test results, and honestly identifies the capabilities intentionally left out of scope.

## 2. Introduction

Academic institutions require coordinated management of several interdependent processes: who is enrolled in which class, whether they attended it, how they performed in assessments, whether their fees are current, and where and when each class meets. When these processes are tracked in separate, uncoordinated tools, three problems recur: data duplication (the same fact — a student's enrollment, say — recorded in more than one place, able to drift out of sync), weak accountability (no single audit trail for who approved a result or recorded a payment), and inconsistent access control (a spreadsheet shared over email has no way to guarantee a parent only sees their own child's record).

This project addresses those problems directly by building a single system of record, accessible through a versioned REST API, with every business rule and every access-control decision enforced server-side. The system was developed following a proposal-driven, milestone-based process: a written requirements analysis and architecture design preceded implementation, and every deviation from the original proposal — every endpoint, page, or capability added because implementation revealed a genuine gap — is separately documented and justified rather than silently introduced.

## 3. Objectives

1. Replace spreadsheet- and email-based attendance, result, and fee tracking with one authoritative system of record.
2. Enforce role-based access control and per-record ownership (a Parent's own linked children, a Teacher's own classes) at the API layer, never trusting the frontend alone to hide unauthorized data or actions.
3. Provide a complete academic workflow lifecycle for exams (draft → open → published) and results (submitted → approved/rejected → published), with every state transition validated server-side.
4. Compute derived figures — attendance percentage, GPA, outstanding fee balance — live from underlying records at query time, so they can never silently drift out of sync with the data they represent.
5. Deliver role-appropriate dashboards and screens for all four roles, each surfacing only the data and actions relevant to that role.
6. Achieve verifiable correctness through automated testing covering every documented business rule, validation rule, and RBAC/ownership boundary, rather than relying on manual inspection alone.
7. Produce a system that is independently deployable (frontend as static assets, backend as a containerized service) and continuously verified via CI on every change.

## 4. Problem Statement

Given a university that currently manages student records, attendance, results, fees, and scheduling using a mixture of spreadsheets, email, and disconnected finance tools, design and implement a single web-based system that:

- Gives each of Student, Teacher, Parent, and Admin a role-appropriate view of exactly the data they are authorized to see.
- Makes every workflow (attendance marking, exam grading, result approval, fee invoicing) an explicit, auditable, state-machine-driven process rather than an informal one.
- Prevents unauthorized access or modification through server-side enforcement, not client-side convenience checks alone.
- Ensures every reported figure (a percentage, a balance, a grade average) is always computed from — and therefore always consistent with — the underlying source records.

## 5. Literature Review

Institutional record-keeping for the processes this system addresses is typically handled by one of three approaches in practice:

- **General-purpose office tools** (spreadsheets, email, shared documents) — flexible and low-cost, but with no access control finer than "who has the file," no server-side validation of business rules, and no single source of truth once a value is copied between documents.
- **Commercial/open-source Learning Management Systems** (e.g. Moodle) — strong for course content delivery and assessment, but not designed as an institution-wide system of record for attendance, fees, and administrative scheduling in one place.
- **Commercial Student Information System / ERP platforms** (e.g. Ellucian Banner, PeopleSoft Campus Solutions) — comprehensive but heavyweight, typically licensed, and architected for large-scale multi-institution deployment rather than a single institution's specific, scoped workflow.

This project occupies a deliberately narrower niche than either category: a purpose-built, single-institution system covering exactly the processes named in the project proposal (attendance, exams/results, fees, scheduling, notifications), built with a modern, decoupled REST-API-plus-SPA architecture rather than a monolithic server-rendered application, and with role-based access control as a first-class, server-enforced design constraint from the outset rather than an added-on permissions layer.

## 6. Methodology

The system was built through a **sequential, milestone-based development process**: requirements analysis and architecture design were written and reviewed before implementation began, and implementation proceeded through discrete milestones (foundations → users → reference data/RBAC → scheduling → exams → attendance → grading → results → fees → notifications → dashboards/reporting → hardening/testing/deployment), each reviewed before the next started.

Within each milestone, the same discipline was applied at the code level:

- **Investigate before implementing** — the current architecture and any ambiguity in the requirement was resolved (and documented) before writing code.
- **Layered implementation** — every backend change respects the Router → Service → Repository boundary; every frontend change respects the Page → Feature-hook → Component boundary.
- **Test-driven verification** — every business rule and validation rule added a corresponding test in the same change, not deferred to a later pass.
- **Documentation kept synchronized** — any capability added beyond the original written proposal was logged, classified, and justified in the same change that introduced it, producing a complete paper trail of what was built and why.
- **Disposable-database testing discipline** — integration tests always run against a throwaway PostgreSQL database, created and destroyed per verification run, never against a developer's real data.

Following the milestone program's completion, two further verification passes were carried out: a **production-readiness gap-closure pass** (a full audit of the Teacher and Parent portals against the original proposal, closing every genuine gap found), and a **QA/security audit pass** (a systematic review of UI/UX, RBAC, data integrity, and cache-correctness across the whole application), each fixing only the concrete issues actually found.

## 7. System Analysis

The system serves four actors with distinct, overlapping needs:

| Actor | Primary needs |
|---|---|
| **Student** | View their own timetable, attendance, exams, results, and fee status; take exams within a time limit |
| **Teacher** | Manage their own classes' attendance and exams; grade submissions; request schedule changes |
| **Parent** | View their linked children's attendance, results, timetable, and fee status — read-only, never able to modify academic data |
| **Admin** | Manage accounts and reference data; approve results and schedule-change requests; manage fee structures and payments; view aggregate reports |

Cutting across all four actors is a single, consistent requirement: **any data or action available to a user must be exactly the data or action their role (and, where applicable, their specific ownership of a record) authorizes** — a Parent must never be able to view an unrelated student's data by guessing an ID; a Teacher must never be able to grade or mark attendance for a class they do not teach.

The analysis identified reference data (Department, Course, Room, Semester) as a distinct, shared domain underlying scheduling, enrollment, and fee-structure scoping — modeled and implemented as its own consistent CRUD domain rather than duplicated inline wherever a department or course needed to be referenced.

## 8. Requirement Analysis

Requirements were captured formally before implementation as functional requirements (FR-xxx), non-functional requirements (NFR-xxx), business rules (BR-xxx), and validation rules (VR-xxx) in `docs/Requirement_Analysis.md`, with any ambiguity in the original proposal explicitly logged and resolved rather than silently assumed. The summary below reflects what was actually implemented.

### 8.1 Functional Requirements (implemented)

- **Authentication** — login issuing access/refresh JWTs, token refresh, logout (refresh-token invalidation), authenticated password change.
- **User management** — Admin-managed Student and Teacher account creation, update, and deactivation; self-service profile view/update for every role; Parent-to-Student linking (many-to-many, one parent may link multiple children).
- **Reference data** — full CRUD for Department, Course, Room, and Semester (Admin-managed; read access for every authenticated role).
- **Scheduling** — class-session and enrollment creation; schedule-entry creation/update/deletion with room/teacher conflict detection; a Teacher-initiated schedule change-request workflow with an Admin approval queue and outcome notification.
- **Attendance** — Teacher marking and correction of attendance per class session/date; a student's own (or, for Parent, their linked child's) attendance view with per-class and overall percentage; Admin reporting by department/semester/student, exportable to PDF/Excel/CSV.
- **Exams** — exam creation/edit/delete (draft only)/publish by a Teacher, covering MCQ, short-answer, descriptive, and coding question types; timed exam-taking by a Student with a server-recorded start time; per-question teacher grading with awarded marks and optional feedback.
- **Results** — Teacher submission of a course's results (gated on the exam being fully graded); an Admin approval queue with approve (publish, with mandatory notification) or reject (with a mandatory comment); credit-hour-weighted per-semester GPA; PDF transcript download (Student, own linked Parent, or Admin).
- **Fees (optional module, implemented)** — Admin-defined fee structures with automatic per-eligible-student invoice generation; payment recording with strict rejection of overpayment or payment against an already-settled invoice; overdue-account listing; PDF invoice download that relabels itself "Receipt" once the invoice is fully paid.
- **Notifications** — four automatic, event-driven triggers (result published, schedule change, attendance warning, fee due), each reaching both the directly affected Student and every linked Parent; a notification feed with unread tracking and mark-as-read.
- **Reporting** — Admin attendance/results/fees aggregate reports, filterable by department/semester/student.
- **Dashboards** — a role-specific summary view for each of the four roles.

### 8.2 Non-functional Requirements (implemented)

- **Security** — passwords hashed with bcrypt; JWT access tokens short-lived, refresh tokens rotated on use; all authorization decisions re-verified server-side on every request (never cached from login); login rate-limited; interactive API documentation automatically disabled in production.
- **Data integrity** — all foreign keys enforced at the database level; hard-delete with `ON DELETE RESTRICT` for reference/catalog data, deactivation (not deletion) for identity records with historical dependents; every schema change shipped as a reviewed Alembic migration, never manual DDL.
- **Consistency** — attendance percentage, GPA, and outstanding balance always computed at query time from underlying records, never stored as a separately-maintained cached value.
- **Maintainability** — a strict layered backend architecture and a feature-sliced frontend, enforced without exception across all 11 backend domains, verified continuously by a 538-test combined suite and CI on every push.
- **Auditability** — sensitive actions (result approval, payment recording, account creation/deactivation, schedule changes) logged as discrete, structured audit events.
- **API versioning** — all endpoints served under `/api/v1`, allowing a future breaking version to be introduced without disrupting existing frontend deployments.

## 9. ER Diagram Explanation

The complete entity-relationship diagram (text format) is in [`DATABASE_DESIGN.md`](DATABASE_DESIGN.md) and, in full column-level detail, in `docs/Database_Design.md` §4. In summary, the schema's 26 tables form five connected clusters:

1. **Identity cluster** — `user` is the base identity (email, password hash, role, active flag); `student`, `teacher`, `parent`, and `admin` each extend it in a 1:1 relationship with their own profile fields. `parent_student_link` is the many-to-many join enabling a Parent to be linked to multiple children.
2. **Academic-structure cluster** — `department` owns `course`; `course` is scheduled as one or more `class_session` rows (each taught by one teacher, in one semester); `enrollment` joins `student` to `class_session`.
3. **Scheduling cluster** — `schedule_entry` places a `class_session` into a `room` at a specific day/time with an assigned teacher; `schedule_change_request` records a Teacher's proposed change to one `schedule_entry`, with a pending/approved/rejected lifecycle.
4. **Assessment cluster** — `exam` belongs to a `class_session`; `question`/`question_option` belong to the exam; `exam_submission` links a `student` to an `exam`; `answer` belongs to a submission and question; `question_grade` records a teacher's awarded marks/feedback per answer; `result` is the authoritative, one-per-student-per-course-per-semester grade record, independent of (but referencing) the exam that most recently produced it.
5. **Operational cluster** — `attendance_record` (student + class session + date), `fee_structure`/`invoice`/`payment` (fee lifecycle), and `notification` (one row per addressed user per event).

Every foreign key in the diagram is enforced at the database level, not merely assumed by application code — the referential-integrity policy (restrict vs. cascade) is documented per relationship in `docs/Database_Design.md` §10.

## 10. Database Design

See [`DATABASE_DESIGN.md`](DATABASE_DESIGN.md) for the full summary (table list by domain, key relationships, referential-integrity policy, uniqueness constraints, and indexing rationale) and `docs/Database_Design.md` for the complete column-by-column specification. In brief: PostgreSQL, accessed exclusively through the SQLAlchemy ORM, normalized to Third Normal Form, with **26 tables** managed by **10 sequential Alembic migrations** forming a single linear history with zero drift against the current ORM models (verified by an empty `alembic revision --autogenerate` diff). Every table has a surrogate UUID primary key and `created_at`/`updated_at` audit columns. Duplicate-prevention for the records where it matters most — one attendance record per student/class/date, one result per student/course/semester, one enrollment per student/class session — is enforced by a real database unique constraint, not just an application-level check.

## 11. System Architecture

See [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md) for the full summary and `docs/System_Architecture.md` for the complete rationale. In brief: a decoupled client-server architecture — a React single-page application communicating exclusively over a versioned JSON REST API with a FastAPI backend. The backend is a layered monolith, with every one of its 11 domains structured identically:

```
Router   — HTTP request/response shaping, role-only RBAC dependency
   ↓
Service  — every business rule, validation rule, and ownership check
   ↓
Repository — the only place SQLAlchemy queries are written
   ↓
PostgreSQL
```

This layering is enforced without exception: a router never touches the ORM session directly, and a service never receives a raw HTTP request object. The frontend mirrors this discipline — server state lives exclusively in React Query, one typed hook module per API domain; components never call the HTTP client directly. Role-specific screens (Timetable, Attendance, Results, Fee Centre) share one component tree that branches internally by the current user's role, rather than maintaining four separate page trees per screen.

## 12. Technology Stack

| Layer | Technology |
|---|---|
| Frontend framework | React 18 + TypeScript, built with Vite |
| Styling | TailwindCSS |
| Frontend server-state | TanStack React Query |
| HTTP client | Axios |
| Backend framework | FastAPI (Python 3.12) |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Validation | Pydantic 2 |
| Database | PostgreSQL 16 |
| Authentication | JWT (python-jose), bcrypt password hashing |
| Document generation | ReportLab (PDF), openpyxl (Excel), Python's standard `csv` module |
| Backend testing | pytest |
| Frontend testing | Vitest + React Testing Library |
| Static analysis | ESLint (frontend), TypeScript compiler (`tsc --noEmit`) |
| CI/CD | GitHub Actions |
| Containerization | Docker, `docker-compose` (local development) |

## 13. Module Descriptions

| Module | Description |
|---|---|
| **Authentication** | JWT issuance/refresh/logout, rate-limited login, password change |
| **Users & Profiles** | Student/Teacher account lifecycle (Admin-managed), self-service profile, Parent-child linking |
| **Reference Data** | Department/Course/Room/Semester CRUD, the shared foundation for scheduling and fee scoping |
| **Scheduling** | Class sessions, enrollment, schedule entries with conflict detection, the change-request/approval workflow |
| **Attendance** | Marking, correction, live percentage computation, low-attendance alerting, department/semester/student reporting |
| **Exams & Grading** | Exam authoring (4 question types), timed student exam-taking, per-question teacher grading |
| **Results & Transcripts** | Submit → approve/reject → publish workflow, credit-weighted GPA, PDF transcripts |
| **Fees** | Fee structure/invoice/payment lifecycle, overdue tracking, invoice/receipt PDF |
| **Notifications** | Event-driven dispatch to students and linked parents, a feed with read-state tracking |
| **Reporting** | Admin-facing aggregate attendance/results/fees reports |
| **Dashboards** | One role-specific summary screen per role |

## 14. Authentication & RBAC

**Authentication:** login exchanges valid credentials for a short-lived JWT access token and a longer-lived, rotating refresh token. Every subsequent request carries the access token as a Bearer credential; an expired, malformed, or otherwise invalid token is rejected with `401`. A deactivated account (`is_active = false`) fails authorization immediately, even against a still cryptographically-valid token — re-checked on every request, not assumed from the time of login.

**Role-based access control:** every protected endpoint declares its allowed role(s) via a `require_roles()` dependency at the router layer; a request from a disallowed role is rejected with `403` before any business logic executes.

**Ownership enforcement:** role alone is insufficient for a large class of endpoints — a Parent's role permits viewing *some* student's data, but only the service layer, re-checking a live `parent_student_link` row on every single request, determines *which* student. The same pattern governs a Teacher's own classes (`class_session.teacher_id`/`schedule_entry.teacher_id` compared against the caller's own teacher profile) and a Student's own records. This check is never trusted to the frontend, never cached from a previous request, and is re-verified even for file-download endpoints (transcript, invoice, attendance report PDFs) before the document is generated.

**Workflow-state gating:** some actions are additionally gated by an object's own state, independent of role — a Student can view an exam's correct answers/marks only once that exam's results are published; a result can be approved only while it is in `submitted` status; a published exam cannot be deleted.

## 15. API Overview

The API exposes **82 endpoints** across 11 domains, all versioned under `/api/v1` and returning one consistent JSON error shape for every failure class (`401`/`403`/`404`/`409`/`422`/`500`). See [`API_DOCUMENTATION.md`](API_DOCUMENTATION.md) for the full endpoint-by-endpoint table and `docs/API_Contract.md` for exact request/response schemas; a live, interactive Swagger UI is also generated automatically by FastAPI at `/docs` in every non-production environment.

| Domain | Endpoints |
|---|---|
| Authentication | 4 |
| Users & Profiles | 11 |
| Reference Data | 20 |
| Scheduling | 11 |
| Attendance | 8 |
| Exams & Grading | 10 |
| Results & Transcripts | 5 |
| Fees | 8 |
| Notifications | 2 |
| Reports | 2 |
| Health | 1 |

## 16. Testing

The system is verified by a combined **538 automated tests** (477 backend, 61 frontend), all passing — see [`TEST_REPORT.md`](TEST_REPORT.md) for the full breakdown by file and how to reproduce the run.

- **Backend unit tests** (24 files) exercise service-layer business logic with repositories stubbed — no database required, run in every environment including CI.
- **Backend integration tests** (8 files) exercise the full request → database → response cycle against a real, disposable PostgreSQL database, never a developer's actual data.
- **Frontend component tests** (14 files, Vitest + React Testing Library) cover the shared interactive components (the searchable dropdown's full keyboard support, the Print/PDF/Excel/CSV export toolbar) and the highest-interaction-risk pages (the exam timer, the grading form, the result-approval workflow, the Admin schedule-approval queue, the Parent-facing Results/Fees/Attendance views).
- Every documented business rule and validation rule has a dedicated test; every RBAC/ownership boundary has an explicit **negative** test (verifying a wrong-role or wrong-owner request is actually rejected, not merely that the correct case succeeds); every workflow state machine is tested for both valid and invalid transitions.
- Continuous integration (GitHub Actions) runs the equivalent backend and frontend checks — including an automated schema-drift check (`alembic revision --autogenerate` must produce an empty diff) — on every push and pull request.

## 17. Results

- **82 REST endpoints** delivered across 11 domains, all RBAC- and ownership-enforced.
- **26 database tables**, fully relationally constrained, managed by **10 Alembic migrations** with a single head and zero schema/model drift.
- **538 automated tests, all passing** (477 backend, 61 frontend), plus a clean TypeScript compile, a clean ESLint pass, and a successful production build.
- All four roles have a complete, working set of screens covering their entire documented feature set, including Parent-facing Results, Fee Centre, and export capabilities added during the post-milestone hardening passes.
- A full production-readiness audit (UI/UX, accessibility, RBAC, data integrity, cache correctness, security) found the system largely production-correct on first pass, with only two narrow input-validation gaps identified and fixed (missing lower bounds on course credit-hours and room capacity).
- The system runs locally via a documented setup process and via Docker Compose, with CI verifying both halves of the stack on every change.

## 18. Limitations

The following are deliberate, documented scope boundaries — not oversights:

- **No Communication/Messaging module** — Parents and Teachers cannot exchange in-app messages; this was never part of the original proposal.
- **No dedicated Progress Report generator** — no such document type exists for any role.
- **No Teacher Remarks on the aggregated Results view** — the `result` table has no remarks/comments column; the only existing per-question feedback (`question_grade.feedback`) is a different granularity, already surfaced in the exam-taking view, and folding it into the aggregated Results page would require new aggregation logic rather than exposing an existing field.
- **No overall (cross-semester) CGPA figure** — the backend returns only per-semester GPA and does not retain per-course credit-hours in that response, so an accurate cumulative figure cannot be computed without a new backend aggregate; the UI shows an explicit "Not available" placeholder rather than an approximation.
- **Schedule-change "request modification" is expressed as Reject + comment**, not a distinct third request status — the database enum is exactly `pending`/`approved`/`rejected`.
- **The login rate limiter is in-process memory**, not shared across replicas — sufficient for a single-instance deployment, a known limitation for horizontal scaling.
- **No scheduled/cron-based reminders** (e.g. a fee due-date reminder sent some days in advance) — only event-driven notifications exist; no scheduler mechanism is present anywhere in the system.

## 19. Future Improvements

- A shared (e.g. Redis-backed) rate limiter to support horizontally-scaled deployment.
- Email/SMS delivery channels for notifications, in addition to the existing in-app feed.
- A scheduled-task mechanism to support due-date reminders and other time-based triggers.
- An overall CGPA aggregate endpoint, if credit-hour data is retained across the full academic history.
- A Teacher-remarks field on the Result record, if the institution's grading policy requires narrative feedback at the course level (distinct from the existing per-question feedback).
- A production-oriented Docker Compose profile (reverse proxy/TLS termination, managed database, multiple backend replicas).
- An in-app Communication module, if a future requirement calls for direct Parent-Teacher messaging.

## 20. Conclusion

The University Management System delivers a complete, verifiably working replacement for the fragmented spreadsheet/email/finance-tool approach to university record-keeping described in the problem statement. Every functional requirement in the original proposal was implemented and tested; every access-control boundary is enforced server-side and explicitly, negatively tested; every derived figure a user sees is computed live from its underlying records rather than cached or duplicated. The layered backend architecture and feature-sliced frontend kept the system's growing scope (11 backend domains, 82 endpoints, 26 tables) maintainable throughout an incremental, milestone-based build, and a combined 538-test automated suite — run continuously via CI — gives confidence in the system's correctness beyond what manual inspection alone could provide. Where capabilities were deliberately left unbuilt, they are documented as such, rather than silently omitted, so the system's actual scope is always precisely knowable.

## 21. References

- FastAPI documentation — https://fastapi.tiangolo.com
- SQLAlchemy documentation — https://docs.sqlalchemy.org
- Alembic documentation — https://alembic.sqlalchemy.org
- Pydantic documentation — https://docs.pydantic.dev
- PostgreSQL documentation — https://www.postgresql.org/docs/
- React documentation — https://react.dev
- TanStack Query (React Query) documentation — https://tanstack.com/query
- TailwindCSS documentation — https://tailwindcss.com/docs
- Vite documentation — https://vitejs.dev
- JSON Web Token (RFC 7519) — https://datatracker.ietf.org/doc/html/rfc7519
- ReportLab (PDF generation library) documentation — https://www.reportlab.com/docs/reportlab-userguide.pdf
- openpyxl documentation — https://openpyxl.readthedocs.io
- pytest documentation — https://docs.pytest.org
- Vitest documentation — https://vitest.dev
- This project's own governing engineering documents: `docs/Requirement_Analysis.md`, `docs/System_Architecture.md`, `docs/Database_Design.md`, `docs/API_Contract.md`, `docs/Proposal_vs_Engineering_Additions.md`
