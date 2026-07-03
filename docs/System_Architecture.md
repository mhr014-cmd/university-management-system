# System Architecture Document
## University Management System (ICT Education)

**Source inputs:** `docs/product_proposal.pdf` (v1.0), `docs/Requirement_Analysis.md`
**Scope:** Architecture design only — no application code included.

---

## 1. Overall Architecture

The system follows a **decoupled, client-server architecture**: a single-page React frontend communicates exclusively with a versioned REST API backend over HTTPS/JSON. There is no server-side rendering coupling and no direct database access from the client — all data flows through the API.

```
                    ┌─────────────────────────────┐
                    │   React 18 + TypeScript SPA  │
                    │   (served from CDN)           │
                    └───────────────┬───────────────┘
                                    │ HTTPS / JSON
                                    │ JWT Bearer Token
                                    ▼
                    ┌─────────────────────────────┐
                    │   FastAPI REST API            │
                    │   /api/v1/*                    │
                    │   - Auth & RBAC middleware     │
                    │   - Business logic (services)  │
                    │   - PDF generation (transcripts,│
                    │     invoices)                   │
                    │   - Notification dispatch       │
                    └───────────────┬───────────────┘
                                    │ SQLAlchemy ORM
                                    │ Alembic migrations
                                    ▼
                    ┌─────────────────────────────┐
                    │   PostgreSQL Database          │
                    └─────────────────────────────┘
```

**Architectural style:** Layered (N-tier) monolith for the API — a single deployable FastAPI service internally organized into presentation (routers), business logic (services), and data access (repositories/ORM models) layers. A monolith is appropriate given the project's scope, timeline (single deadline, single team), and the grading criteria, which reward a working, coherent system over distributed-systems complexity.

**Cross-cutting concerns** (authentication, RBAC, error handling, logging) are implemented as middleware/dependency layers shared across all endpoints rather than duplicated per-router.

**Mobile note:** Since the proposal's cover page states "Web/Mobile App" but Section 7 only specifies a web SPA (see Requirement_Analysis.md §14, item 10), this architecture treats the frontend as a **responsive web SPA** that satisfies both web and mobile browser access. No native mobile app architecture is defined, consistent with the ambiguity already flagged.

---

## 2. Backend Architecture

### 2.1 Style
Layered architecture within a single FastAPI service:

1. **Router/Controller layer** — one router module per domain (auth, users, exams, attendance, results, fees, schedule), responsible only for request/response shaping, input validation (Pydantic schemas), and delegating to services.
2. **Service layer** — contains business logic and business rules (BR-001 to BR-010 from Requirement_Analysis.md), orchestrates multiple repositories, enforces workflow rules (e.g., result submit → approve → publish).
3. **Repository / Data Access layer** — SQLAlchemy models and query logic, isolated from business rules so the ORM can be swapped or mocked in tests.
4. **Cross-cutting layer** — authentication dependency, RBAC dependency, exception handlers, logging middleware, applied globally via FastAPI dependency injection and middleware.

### 2.2 Domain Modules (mapped to Requirement_Analysis.md §6)
- `auth` — login, refresh, logout, password change, JWT issuance
- `users` — student/teacher/parent account management, profile
- `exams` — exam builder, submission, grading
- `attendance` — marking, correction, reporting
- `results` — submission, approval workflow, transcript generation
- `fees` — fee structure, payments, invoices, overdue tracking
- `schedule` — timetable CRUD, conflict detection
- `notifications` — real-time alert generation and delivery (endpoint gap noted in Requirement_Analysis.md §14, item 3 — must be resolved during design)
- `reports` — Admin result/fee/attendance reporting aggregation queries (FR-030, FR-054, FR-055, FR-056; endpoint gap for result/fee reporting noted in Requirement_Analysis.md §14, item 15 — added during the Project Readiness Audit)

### 2.3 Request Lifecycle
1. Request hits FastAPI router.
2. Auth dependency validates JWT bearer token → resolves current user + role.
3. RBAC dependency checks whether the resolved role is permitted for this endpoint (per the Access column in Requirement_Analysis.md §8).
4. Pydantic schema validates request body/query params (Validation Rules VR-001–VR-009).
5. Router calls the relevant service method.
6. Service applies business rules, calls one or more repositories.
7. Repository executes SQLAlchemy queries against PostgreSQL.
8. Service returns a domain result; router serializes it to the response schema.
9. Global exception handlers catch and translate any errors raised at any layer into a standard error response (see Section 9).

### 2.4 Background/Async Concerns
- **PDF generation** (transcripts, invoices) is CPU-bound and should run as an async task or background worker triggered by the relevant endpoint, to avoid blocking the request thread.
- **Notification dispatch** (result published, schedule changed, attendance warning, fee due) is event-driven: triggered by service-layer events (e.g., "result approved" → enqueue notification) rather than polled.

---

## 3. Frontend Architecture

### 3.1 Style
A **feature-sliced SPA** built with React 18 + TypeScript, using React Query for all server-state management (caching, refetch, optimistic updates, loading/error states — per proposal §7) and a lightweight client-state solution (e.g., context) reserved only for UI-local state (e.g., modal open/closed), since server state should not be duplicated in client state stores.

### 3.2 Layers
1. **Routing layer** — role-aware route guards; unauthenticated users redirected to Login; authenticated users redirected to their role's Dashboard (FR-005).
2. **Page layer** — one component tree per screen listed in Requirement_Analysis.md §7 (Dashboard, Profile, Exam list, Exam room, Results view, Attendance page, Fee centre, Timetable, Admin screens, Teacher screens, Notifications panel).
3. **Feature/API layer** — React Query hooks wrapping each REST endpoint group (e.g., `useExams`, `useAttendance`, `useResults`), isolating API contracts from UI components.
4. **Shared UI layer** — reusable presentational components (tables, badges, forms, PDF download buttons) styled with TailwindCSS utility classes.
5. **Auth layer** — stores access/refresh tokens, attaches bearer token to all requests, handles silent refresh and logout-on-expiry.

### 3.3 Role-Based UI Composition
The same Dashboard/Profile/Notifications shell is shared across roles, but role-specific widgets and navigation items are composed conditionally based on the authenticated user's role — avoiding four fully separate frontend applications while still respecting NFR-001/NFR-002 (enforced server-side, mirrored client-side for UX only).

### 3.4 State Ownership
- **Server state** (exams, results, attendance, fees, schedule, users) → React Query only, never duplicated into global client state.
- **Client-only state** (form drafts, modal visibility, active tab) → local component state or lightweight context.
- **Auth state** (current user, role, token presence) → a small auth context, since it must be accessible for route guards across the whole app.

---

## 4. PostgreSQL Architecture

### 4.1 Core Entities (derived from proposal §3–§6 and Requirement_Analysis.md)

- **User** (base identity: email, password hash, role, active/deactivated status)
  - **Student** (profile fields, department, enrollment info) — 1:1 with User
  - **Teacher** (profile fields, department) — 1:1 with User
  - **Parent** (profile fields) — 1:1 with User
  - **Admin** — 1:1 with User (or a role flag on Admin-capable Users)
- **ParentStudentLink** — many-to-many join between Parent and Student (per Assumption A-003, a parent may link to multiple children)
- **Department**
- **Course** — belongs to a Department
- **ClassSession** ("class") — a scheduled instance of a Course (links to Schedule)
- **Enrollment** — join between Student and Course/ClassSession
- **Exam** — belongs to a Course/ClassSession, created by a Teacher; has a published/unpublished state
- **Question** — belongs to an Exam; has type (MCQ/short/descriptive/coding), marks, optional hint
- **ExamSubmission** — belongs to a Student + Exam; holds answers and submission timestamp
- **QuestionGrade** — belongs to a Submission + Question; holds awarded marks and feedback
- **AttendanceRecord** — belongs to a Student + ClassSession + date; present/absent + who marked it
- **Result** — belongs to a Student + Course/semester; holds grade/GPA components; has a workflow status (submitted, approved, published)
- **Transcript** (generated artifact, not necessarily its own table — may be derived on demand from Result)
- **FeeStructure** — belongs to a Department/semester; defines amounts (Optional module)
- **Payment** — belongs to a Student + FeeStructure; records amount, date, method (Optional module)
- **Invoice** (generated artifact from FeeStructure + Payment state)
- **ScheduleEntry** — belongs to a Course/ClassSession, Room, Teacher, and time slot
- **Notification** — belongs to a User; type, payload, read/unread state, created timestamp

### 4.2 Relationship Highlights
- User → Student/Teacher/Parent/Admin: single-table-inheritance-style or role-flag design decision to be finalized during implementation; either way, `role` must be a first-class, indexed column for RBAC checks.
- Result workflow state (submitted → approved → published) is modeled as an enum/status column on Result, satisfying BR-002.
- Exam published/unpublished state is a boolean or enum on Exam, satisfying BR-003.
- ScheduleEntry must have a uniqueness/overlap constraint (enforced at the service layer plus a supporting index) on (Room, TimeSlot) and (Teacher, TimeSlot) to satisfy BR-005/NFR-015.
- ParentStudentLink resolves Assumption A-003 and directly supports NFR-003 (parent data isolation) by giving the API a concrete join to authorize against.

### 4.3 Schema Management
- **SQLAlchemy** models define the schema in code; **Alembic** manages versioned, incremental migrations (per proposal §7 tech stack and Constraint C-001).
- Every schema change ships as a new Alembic revision — no manual DDL against the running database.

### 4.4 Data Integrity Rules (NFR-006)
- Foreign keys enforced at the database level for all relationships listed above (not application-only checks).
- Soft-deactivation (not hard delete) for User/Student/Teacher accounts (BR-006) — an `is_active` flag rather than row deletion, preserving historical Attendance/Result/Payment references.
- Cascading rules must distinguish between "restrict" (e.g., cannot delete a Course with existing Enrollments) and "cascade" (e.g., deleting a draft/unpublished Exam removes its Questions).

---

## 5. Authentication Flow

1. **Login**: Client submits email/password to `POST /auth/login`. Backend verifies credentials against the stored password hash, then issues a short-lived **access token** (JWT, contains user ID + role) and a longer-lived **refresh token**.
2. **Token storage**: Access token is held in memory/short-lived client storage; refresh token is stored more durably (e.g., httpOnly cookie or secure storage) to reduce XSS exposure risk (Security Strategy, Section 11).
3. **Authenticated requests**: Every subsequent API call attaches the access token as an `Authorization: Bearer <token>` header.
4. **Token expiry**: When the access token expires, the client calls `POST /auth/refresh` with the refresh token to obtain a new access token, without forcing the user to log in again.
5. **Refresh token expiry/invalidation**: If the refresh token is also expired or has been invalidated (e.g., after logout), the client is redirected to the Login screen.
6. **Logout**: `POST /auth/logout` invalidates the current session's refresh token server-side (denylist or rotation record), and the client discards both tokens locally.
7. **Password change**: `PUT /auth/password` requires the current session to be authenticated; per VR-002, the new password must differ from the old one and meet a minimum complexity standard (exact policy to be defined — flagged in Requirement_Analysis.md §14, item 13).

---

## 6. Authorization Flow

1. Every protected endpoint declares which role(s) may access it, matching the Access column in Requirement_Analysis.md §8 (e.g., `POST /users/students` → Admin only).
2. On each request, after the Authentication step resolves the current user and role, an **RBAC dependency** checks the resolved role against the endpoint's allowed-roles list. If not permitted, the API returns `403 Forbidden`.
3. **Ownership checks** (beyond role) are required for several endpoints where role alone is insufficient:
   - `GET/PUT /users/me` — user must only affect their own record.
   - `GET /attendance/me`, `GET /results/me`, `GET /fees/me`, `GET /schedule/me` — scoped to the authenticated user's own ID.
   - `GET /fees/payments/{studentId}` (Parent access) — the API must verify a `ParentStudentLink` exists between the authenticated parent and `{studentId}` before returning data (satisfies NFR-003).
   - `GET /results/{studentId}/transcript` (Student access) — student may only request their own `{studentId}`.
4. **Workflow-state checks** — some actions are gated not just by role but by object state:
   - A Student can view question marks only if the Exam's results are published (BR-001).
   - A Result can only be approved by Admin if it is in "submitted" state (BR-002).
   - An Exam can only be deleted if it is unpublished (BR-003).
5. Authorization failures return a consistent error shape (see Section 9) distinguishing `401 Unauthorized` (no/invalid token) from `403 Forbidden` (valid token, insufficient permission) from `404 Not Found` (used instead of 403 where resource existence itself should not be revealed, e.g., another student's record).

---

## 7. Folder Structure

> Structure only — no source files are created as part of this document.

```
university-management-system/
├── docs/
│   ├── product_proposal.pdf
│   ├── Requirement_Analysis.md
│   └── System_Architecture.md
│
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI app entrypoint
│   │   ├── core/                        # config, security, JWT, settings
│   │   ├── db/                          # SQLAlchemy session, base model
│   │   ├── models/                      # ORM models (User, Student, Exam, ...)
│   │   ├── schemas/                     # Pydantic request/response schemas
│   │   ├── routers/                     # one module per domain (auth, users, exams, ...)
│   │   ├── services/                    # business logic per domain
│   │   ├── repositories/                # data-access queries per domain
│   │   ├── middleware/                  # auth, RBAC, logging, error handling
│   │   ├── notifications/               # notification generation/dispatch
│   │   └── pdf/                         # transcript/invoice PDF generation
│   ├── alembic/                         # migration scripts
│   ├── tests/                           # backend test suite
│   └── requirements/ (or pyproject.toml)
│
├── frontend/
│   ├── src/
│   │   ├── app/                         # routing, root layout, providers
│   │   ├── pages/                       # one folder per screen (Dashboard, Profile, ExamRoom, ...)
│   │   ├── features/                    # per-domain API hooks (React Query) + logic
│   │   ├── components/                  # shared UI components
│   │   ├── auth/                        # auth context, token handling, route guards
│   │   └── styles/                      # Tailwind config/theme
│   ├── public/
│   └── tests/
│
└── infra/ (optional)
    ├── docker/                          # Dockerfiles for backend/frontend
    └── ci/                              # pipeline configuration
```

This mirrors the domain modules from Section 2.2 and the screen list from Requirement_Analysis.md §7, keeping backend and frontend independently deployable per Constraint C-007.

---

## 8. Deployment Architecture

```
        ┌────────────┐        ┌──────────────────────┐
        │   Users     │──────▶│  CDN (static hosting)  │──▶ React SPA assets
        └────────────┘        └──────────────────────┘
                │
                │ HTTPS API calls (/api/v1/*)
                ▼
        ┌──────────────────────┐
        │  API Server(s)         │
        │  FastAPI (Uvicorn/     │
        │  Gunicorn workers)      │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  PostgreSQL (managed   │
        │  instance)              │
        └──────────────────────┘
```

- **Frontend**: Built as static assets and served from a CDN, per proposal §7 ("served from a CDN"). No server-side rendering; the CDN only serves the compiled SPA bundle and communicates with the API entirely client-side.
- **Backend**: Deployed as a containerized FastAPI service (e.g., behind Uvicorn/Gunicorn workers), independently scalable and independently deployable from the frontend (Constraint C-007).
- **Database**: A managed PostgreSQL instance, separated from the API tier so it can be scaled, backed up, and secured independently.
- **Environments**: At minimum, a development and a production environment, each with its own database and its own set of secrets (JWT signing key, DB credentials). Alembic migrations run as a deployment step before the new API version starts serving traffic.
- **Versioning**: The `/api/v1` prefix (NFR-005) allows the API to introduce a future `/api/v2` without breaking existing frontend deployments.

*(This section describes the target deployment topology implied by the proposal's tech stack; it does not select or mandate a specific cloud provider, since the proposal does not specify one — an item worth confirming with the instructor, similar to the ambiguities already logged in Requirement_Analysis.md §14.)*

---

## 9. Error Handling Strategy

- **Global exception handling**: FastAPI global exception handlers translate all raised errors (validation errors, business rule violations, not-found, permission errors, unhandled exceptions) into a single consistent JSON error shape, e.g. `{ "error": { "code": "...", "message": "...", "details": [...] } }`, rather than letting each router format its own errors.
- **Validation errors** (VR-001–VR-009, and general Pydantic schema failures) → `422 Unprocessable Entity` with field-level detail.
- **Authentication errors** (missing/expired/invalid token) → `401 Unauthorized`.
- **Authorization errors** (valid token, wrong role or wrong ownership) → `403 Forbidden`, or `404 Not Found` where hiding resource existence is preferable (Section 6).
- **Business rule violations** (e.g., attempting to delete a published exam per BR-003, or approving a result not in "submitted" state per BR-002) → `409 Conflict` with a message identifying the violated rule.
- **Not-found errors** (invalid ID) → `404 Not Found`.
- **Unexpected server errors** → `500 Internal Server Error`, with the underlying exception logged (Section 10) but never leaked to the client response body.
- **Frontend handling**: React Query's built-in error states surface these responses per-screen; a shared API client interceptor handles the cross-cutting cases (401 → redirect to Login; 403 → show a permission-denied state) so individual screens only need to handle domain-specific error messaging.

---

## 10. Logging Strategy

- **Structured logging**: All backend logs are structured (JSON) rather than free-text, to support later aggregation/searching.
- **Request logging**: A logging middleware records method, path, status code, response time, and the authenticated user's ID/role (not credentials) for every API request.
- **Audit logging for sensitive actions**: Result approval, fee payment recording, user account creation/deactivation, and schedule changes are logged as discrete audit events (who did what, to which resource, when) — this directly supports NFR-014 (auditability of the approval workflow).
- **Error logging**: Every `500`-level error logs the full stack trace server-side; `4xx`-level errors are logged at a lower severity (they represent expected client/business conditions, not system faults).
- **Log levels**: `DEBUG` (local development only), `INFO` (routine request/audit events), `WARNING` (recoverable issues, e.g., a failed notification dispatch that will be retried), `ERROR` (unhandled exceptions, failed critical operations).
- **No sensitive data in logs**: Passwords, raw JWTs, and full payment card/financial details (if ever handled beyond the scope described) must never be written to logs.
- **Frontend logging**: Client-side errors (e.g., unexpected API failures, render errors) are captured via an error boundary and reported to a central location distinct from routine console output, so production issues are visible without depending on user bug reports.

---

## 11. Security Strategy

- **Transport security**: All client-API traffic over HTTPS only; no plaintext HTTP in any environment beyond local development.
- **Password storage**: Passwords are never stored in plaintext; a strong adaptive hashing algorithm (e.g., bcrypt/argon2) is used, satisfying the implicit expectation behind FR-004/NFR-004.
- **Token security**: Short-lived access tokens limit the exposure window of a stolen token; refresh tokens are rotated on use and invalidated on logout (Section 5), directly supporting NFR-004.
- **RBAC enforcement at the API layer**: As established in Section 6, authorization is never trusted to the frontend alone — this satisfies NFR-001 explicitly and closes the gap flagged as Risk R-004 in Requirement_Analysis.md.
- **Ownership verification**: All "me" and parent-linked endpoints re-verify ownership/linkage server-side on every request, not just at login time (supports NFR-002/NFR-003).
- **Input validation**: Every request body is validated against a Pydantic schema before reaching business logic, mitigating injection and malformed-data risks.
- **SQL injection protection**: All database access goes through the SQLAlchemy ORM/parameterized queries — no raw string-interpolated SQL.
- **File/PDF handling**: Generated transcripts/invoices are produced server-side from validated data (not user-supplied templates), avoiding injection into generated documents.
- **Least privilege for deactivated accounts**: A deactivated User must fail authentication (or have all authorization checks fail) immediately, even if a still-valid token exists for that account — token validation should re-check `is_active` status, not rely solely on token claims issued at login time.
- **Secrets management**: JWT signing keys and database credentials are stored in environment configuration/secret managers, never committed to source control.
- **Rate limiting** (gap noted in Requirement_Analysis.md §14, item 13): Not specified in the proposal; recommended as a defensive addition on `/auth/login` and other public endpoints to mitigate brute-force attempts, to be confirmed with stakeholders.

---

## 12. Technology Stack

*(As fixed by the proposal, Constraints C-001/C-002.)*

| Layer | Technology |
|---|---|
| Frontend framework | React 18 + TypeScript |
| Styling | TailwindCSS |
| API communication (frontend) | React Query |
| Backend framework | FastAPI (Python 3.12) |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Authentication | JWT (access + refresh tokens), role-based access control |
| API format | REST, JSON, versioned under `/api/v1` |
| Frontend hosting | CDN (static SPA hosting) |
| Backend hosting | Containerized API service (Uvicorn/Gunicorn workers) |
| Documents | Server-side PDF generation for transcripts and invoices (library choice not specified by proposal — to be selected during implementation) |

---

## Traceability Note

This architecture was derived strictly from `docs/product_proposal.pdf` and `docs/Requirement_Analysis.md`. Where the source documents were silent (e.g., cloud provider, PDF library, exact GPA formula, rate-limiting policy, mobile app architecture), this document either proposes a reasonable default consistent with the stated tech stack or explicitly flags the gap by referencing the corresponding item in Requirement_Analysis.md §14, rather than inventing unstated requirements.
