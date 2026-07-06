---
marp: true
theme: default
paginate: true
size: 16:9
---

<!-- Slide 1 -->

# University Management System
## (ICT Education)

A role-based web platform consolidating attendance, exams, results, fees, and scheduling into one system

**Project Defense Presentation**

---

<!-- Slide 2: Team -->

## Team

**Author / Developer:** Mahabbat Hossain

**Role:** Full-stack design and implementation — backend (FastAPI/PostgreSQL), frontend (React/TypeScript), database design, testing, and documentation

---

<!-- Slide 3: Problem Statement -->

## Problem Statement

Universities commonly manage core operations through **disconnected tools**:

- Attendance tracked in spreadsheets
- Results distributed by email
- Fees managed in a separate finance tool
- Schedules maintained ad hoc

**Consequences:**
- Data that's hard to audit and easy to lose
- No enforced, consistent access control
- Figures (attendance %, GPA, balance) that can silently drift out of sync

---

<!-- Slide 4: Objectives -->

## Objectives

1. Replace fragmented tools with **one authoritative system of record**
2. Enforce **role-based access + ownership** server-side, not just in the UI
3. Model exams and results as explicit, validated **workflows** (draft→published, submitted→approved→published)
4. Compute derived figures (attendance %, GPA, balance) **live**, never cached
5. Give each role a **dedicated, relevant** dashboard and screen set
6. Prove correctness through **automated testing**, not manual inspection alone

---

<!-- Slide 5: Existing System -->

## Existing System (Status Quo)

| Approach | Limitation |
|---|---|
| Spreadsheets + email | No access control, no audit trail, easy to duplicate/lose data |
| Generic LMS (e.g. Moodle) | Strong for course content, not built as an institution-wide record system for fees/attendance/scheduling |
| Commercial ERP/SIS (e.g. Banner, PeopleSoft) | Comprehensive but heavyweight, licensed, built for multi-institution scale |

**Gap:** no lightweight, purpose-built, single-institution system with RBAC as a first-class design constraint

---

<!-- Slide 6: Proposed Solution -->

## Proposed Solution

A **decoupled REST API + SPA** system covering exactly the required processes:

- Authentication & RBAC with per-request ownership checks
- Academic reference data, scheduling with conflict detection
- Attendance with automatic low-attendance alerts
- Exams (4 question types) → grading → results → transcripts
- Fees: invoicing, payments, overdue tracking
- Event-driven notifications to students **and** linked parents
- Role-specific dashboards for Admin, Student, Teacher, Parent

---

<!-- Slide 7: Architecture -->

## System Architecture

```
React 18 + TypeScript SPA
        │  HTTPS / JSON, JWT Bearer token
        ▼
FastAPI REST API  (/api/v1/*)
   Router → Service → Repository
        │  SQLAlchemy / Alembic
        ▼
PostgreSQL
```

- **Layered backend**, enforced without exception across 11 domains
- **Feature-sliced frontend** — server state lives only in React Query
- Independently deployable tiers (static frontend, containerized backend)

---

<!-- Slide 8: Database -->

## Database Design

- **PostgreSQL**, accessed exclusively through SQLAlchemy (no raw SQL)
- **26 tables**, normalized to 3NF
- **10 Alembic migrations**, single linear head, **zero schema drift**
- Every FK enforced at the database level (`RESTRICT` by default)
- Identity records (User/Student/Teacher) **deactivated, never deleted**
- Duplicate-prevention via real unique constraints (one attendance record per student/class/date; one result per student/course/semester)
- Percentages/GPA/balances **always computed live**, never stored

---

<!-- Slide 9: Modules -->

## Modules Delivered

| Module | Capability |
|---|---|
| Auth & Users | JWT login/refresh, RBAC, profile, Parent–Student linking |
| Reference Data | Department / Course / Room / Semester CRUD |
| Scheduling | Timetables, conflict detection, change-request workflow |
| Attendance | Marking, correction, live %, low-attendance alerts |
| Exams & Grading | 4 question types, timed exams, per-question grading |
| Results | Submit → approve/reject → publish, GPA, transcripts |
| Fees | Structures, invoices, payments, overdue tracking |
| Notifications | 4 event-driven triggers, Student + Parent fan-out |
| Reporting & Dashboards | Role-specific views, PDF/Excel/CSV export |

---

<!-- Slide 10: Admin Portal -->

## Admin Portal

- **User Management** — create/deactivate Student & Teacher accounts
- **Academic Setup** — full CRUD for Departments, Courses, Rooms, Semesters
- **Timetable management** — class sessions, enrollment, schedule entries, conflict check
- **Pending Schedule Change Requests** — approve/reject with Teacher notification
- **Result Approval queue** — approve (publish) or reject with comment
- **Fee Dashboard** — create fee structures, record payments, overdue accounts
- **Reports** — attendance/results/fees, filterable, exportable

---

<!-- Slide 11: Student Portal -->

## Student Portal

- **Attendance** — overall %, low-attendance warning, table/calendar views
- **Exams** — eligible exam list → timed Exam Room (server-recorded start time)
- **Results** — per-semester GPA, per-course grades, transcript download
- **Fee Centre** — balance, payment history, invoice/receipt download
- **Timetable & Profile** — own weekly schedule, academic history

---

<!-- Slide 12: Teacher Portal -->

## Teacher Portal

- **Attendance Marker** — mark present/absent/late/excused per class/date
- **Exam Builder** — create/edit/publish exams (MCQ, short-answer, descriptive, coding)
- **Grading Interface** — per-question marks + feedback
- **Timetable** — own classes, **Request Change** (day/time/room) to Admin
- **Profile** — assigned courses this semester

---

<!-- Slide 13: Parent Portal -->

## Parent Portal

- **Linked-child selector** on every screen — always clear whose data is shown
- **Dashboard** — selected child's attendance, fees, recent results, notifications
- **Attendance** — same views as Student, plus Print/PDF/Excel/CSV export
- **Results** — GPA, grades, Pass/Fail, transcript download
- **Fee Centre** — balance, invoices, Invoice/Receipt download
- Strictly **read-only** — cannot modify any academic data

---

<!-- Slide 14: RBAC -->

## Authentication & RBAC

- **JWT** access + rotating refresh tokens; rate-limited login
- **Role check** — every endpoint declares its allowed role(s)
- **Ownership check** — re-verified server-side on *every request*:
  - Parent → only their linked children (`parent_student_link`)
  - Teacher → only their own classes
  - Student → only their own records
- Deactivated accounts fail immediately, even with a valid token
- File downloads (PDF/Excel/CSV) re-check ownership before generating the file

---

<!-- Slide 15: API -->

## API Overview

- **82 REST endpoints** across **11 domains**, versioned under `/api/v1`
- Consistent JSON error shape: `401 / 403 / 404 / 409 / 422 / 500`
- Interactive Swagger UI at `/docs` (disabled automatically in production)

| Domain | Endpoints |
|---|---|
| Reference Data | 20 |
| Scheduling | 11 |
| Users | 11 |
| Exams | 10 |
| Attendance | 8 |
| Fees | 8 |
| Results | 5 |
| Auth | 4 |
| Notifications / Reports | 2 / 2 |
| Health | 1 |

---

<!-- Slide 16: Testing -->

## Testing

- **538 automated tests, all passing** (477 backend + 61 frontend)
- Backend: **unit** tests (business logic, stubbed repos) + **integration** tests (real disposable PostgreSQL database)
- Frontend: Vitest + React Testing Library — timer logic, grading form, approval workflow, admin queues
- Every business/validation rule has a dedicated test
- Every RBAC boundary has an explicit **negative** test (wrong role/owner → rejected)
- CI (GitHub Actions) runs the full suite + schema-drift check on every push

---

<!-- Slide 17: Demo Flow -->

## Live Demo Flow

1. **Login** as Admin → create/verify Academic Setup data
2. **Teacher** marks attendance → **Student**/**Parent** see it update live
3. **Teacher** builds & publishes an exam → **Student** takes it in the Exam Room
4. **Teacher** grades it → **Admin** approves → **Student**/**Parent** see the published result + notification
5. **Teacher** requests a schedule change → **Admin** approves → Teacher notified, timetable updates
6. **Admin** creates a fee structure → **Student**/**Parent** view and download the invoice

---

<!-- Slide 18: Challenges -->

## Challenges

- Enforcing **ownership**, not just role, consistently across every "me"/linked-child endpoint
- Keeping **derived figures** (attendance %, GPA, balance) always live-computed without a performance or duplication shortcut
- Designing a **layered architecture** disciplined enough to unit-test business logic without a database, while still integration-testing the full stack
- Closing real gaps found in later audits (e.g. a schedule-change approval that updated data but never notified the Teacher) without scope creep

---

<!-- Slide 19: Future Work -->

## Future Work

- Shared (Redis-backed) rate limiter for horizontally-scaled deployment
- Email/SMS notification delivery channels
- Scheduled/cron-based reminders (e.g. fee due-date alerts)
- Overall (cross-semester) CGPA aggregate
- Production-oriented deployment profile (reverse proxy/TLS, managed DB, multiple replicas)
- Optional in-app Parent–Teacher communication module

---

<!-- Slide 20: Conclusion -->

## Conclusion

- A complete, **verifiably working** replacement for fragmented spreadsheet/email/finance-tool record-keeping
- Every functional requirement implemented and tested; every access boundary server-enforced and negatively tested
- **82 endpoints, 26 tables, 538 passing tests** — correctness demonstrated, not just claimed
- Deliberate, documented scope boundaries — nothing silently omitted

### Thank you — Questions?
