# Project Structure

## University Management System (ICT Education)

**Version:** 2.0.0
**Status:** Complete — 12 of 12 milestones delivered and approved

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Complete Directory Tree](#2-complete-directory-tree)
3. [Backend Explanation](#3-backend-explanation)
4. [Frontend Explanation](#4-frontend-explanation)
5. [Database](#5-database)
6. [Alembic](#6-alembic)
7. [Docker](#7-docker)
8. [GitHub Workflow (CI)](#8-github-workflow-ci)
9. [Documentation](#9-documentation)
10. [Tests](#10-tests)
11. [Scripts](#11-scripts)
12. [Configuration](#12-configuration)
13. [Architecture](#13-architecture)
14. [Authentication Flow](#14-authentication-flow)
15. [Authorization Flow](#15-authorization-flow)
16. [Request Flow](#16-request-flow)
17. [Response Flow](#17-response-flow)

---

## 1. Project Overview

The University Management System is a web platform that consolidates university operations — student/teacher/parent/admin accounts, scheduling, attendance, exams and grading, results and transcripts, fees, notifications, and reporting dashboards — into a single system. It is built as a decoupled Single Page Application (React 18 + TypeScript) backed by a REST API (FastAPI + PostgreSQL), following a strict layered backend architecture (Router → Service → Repository → SQLAlchemy).

| Fact | Value |
|---|---|
| Backend framework | FastAPI (Python 3.12) |
| Frontend framework | React 18 + TypeScript (Vite) |
| Database | PostgreSQL, via SQLAlchemy ORM |
| Migrations | Alembic (10 revisions, single head) |
| REST endpoints | 68 |
| Database tables | 26 |
| Backend tests | 349 (unit + integration) |
| Frontend tests | 7 (component) |
| Milestones delivered | 12 (M0–M11) |

---

## 2. Complete Directory Tree

```
university-management-system/
├── .github/
│   └── workflows/
│       ├── backend-ci.yml          # Backend CI: pip check, Alembic, pytest (disposable Postgres service)
│       └── frontend-ci.yml         # Frontend CI: tsc, lint, vitest, build
├── backend/
│   ├── alembic/
│   │   ├── env.py                  # Alembic runtime config (reads Settings.database_url)
│   │   ├── script.py.mako          # Migration file template
│   │   └── versions/
│   │       ├── 0001_initial_baseline.py
│   │       ├── 0002_core_reference_data.py
│   │       ├── 0003_user.py
│   │       ├── 0004_role_profiles.py
│   │       ├── 0005_scheduling.py
│   │       ├── 0006_attendance.py
│   │       ├── 0007_exams.py
│   │       ├── 0008_results.py
│   │       ├── 0009_fees.py
│   │       └── 0010_notifications.py
│   ├── app/
│   │   ├── main.py                 # FastAPI app factory, router registration, CORS, lifespan
│   │   ├── core/
│   │   │   ├── config.py           # Settings (env-driven), incl. is_production
│   │   │   ├── logging_config.py   # Structured JSON logging setup
│   │   │   └── security.py         # Password hashing (bcrypt), JWT encode/decode
│   │   ├── db/
│   │   │   ├── base.py             # SQLAlchemy declarative Base
│   │   │   └── session.py          # Engine, SessionLocal, get_db dependency
│   │   ├── middleware/
│   │   │   ├── auth.py             # get_current_user (JWT verification, is_active re-check)
│   │   │   ├── rbac.py             # require_roles(*roles) dependency factory
│   │   │   ├── rate_limit.py       # POST /auth/login rate limiter
│   │   │   ├── error_handlers.py   # Global exception handlers → standard error envelope
│   │   │   └── logging.py          # Request logging middleware
│   │   ├── models/                 # 26 SQLAlchemy ORM models (one file per table)
│   │   ├── schemas/                # Pydantic request/response schemas, one file per domain
│   │   ├── repositories/           # All SQLAlchemy queries, one file per domain
│   │   ├── services/               # Business rules, workflow, RBAC/ownership, one file per domain
│   │   ├── routers/                # FastAPI routers, one file per domain
│   │   ├── notifications/
│   │   │   └── dispatcher.py       # Notification trigger/dispatch functions
│   │   └── pdf/
│   │       ├── invoice_generator.py
│   │       └── transcript_generator.py
│   ├── scripts/
│   │   ├── seed_admin.py           # Bootstraps the first Admin account
│   │   └── seed_demo_data.py       # Populates full demo/dev dataset
│   ├── tests/
│   │   ├── conftest.py             # Shared fixtures (db_session, client, make_*_user, etc.)
│   │   ├── unit/                   # Service-layer tests, repositories stubbed
│   │   └── integration/            # Full request → DB → response tests (disposable DB)
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── App.tsx             # Root component: ErrorBoundary + AppProviders + RouterProvider
│   │   │   ├── providers.tsx       # React Query, Theme, Auth providers
│   │   │   ├── router.tsx          # React Router route table
│   │   │   └── ThemeProvider.tsx   # Light/dark theme context
│   │   ├── auth/
│   │   │   ├── AuthContext.tsx     # useAuth(): user, login(), logout()
│   │   │   ├── RouteGuard.tsx      # Redirects unauthenticated users to /login
│   │   │   └── tokenStorage.ts     # localStorage token/user persistence
│   │   ├── components/
│   │   │   ├── AppLayout.tsx       # Shared header/nav shell (role-composed links)
│   │   │   └── ErrorBoundary.tsx   # Root error boundary
│   │   ├── features/               # React Query hooks per API domain (10 modules)
│   │   ├── lib/
│   │   │   ├── apiClient.ts        # Axios instance, token attach, silent refresh
│   │   │   ├── reportClientError.ts
│   │   │   └── useHealthCheck.ts
│   │   ├── pages/                  # One folder per screen (22 pages/widgets total)
│   │   └── styles/globals.css
│   ├── tests/
│   │   ├── setup.ts                # Vitest + jest-dom setup
│   │   └── pages/                  # Component tests (ExamRoom, GradingInterface, ResultApproval)
│   ├── eslint.config.js
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── package.json
├── database/
│   ├── README.md                   # Points to backend/scripts/seed_demo_data.py
│   └── seeds/                      # Reserved for static seed fixtures (currently empty)
├── docker/
│   ├── Dockerfile.backend          # Production-style FastAPI image (Uvicorn)
│   ├── Dockerfile.frontend          # Static build served by nginx
│   └── docker-compose.yml          # Local dev stack: Postgres + backend (reload) + Vite dev server
├── docs/
│   ├── product_proposal.pdf        # Original specification
│   ├── Requirement_Analysis.md     # FR-001–FR-056, NFR-001–NFR-016
│   ├── System_Architecture.md
│   ├── Database_Design.md
│   ├── Implementation_Roadmap.md
│   ├── API_Contract.md
│   ├── UI_Wireframes.md
│   ├── Requirement_Traceability_Matrix.md
│   ├── Proposal_vs_Engineering_Additions.md
│   └── MILESTONE_VERIFICATION_CHECKLIST.md
├── scripts/
│   └── README.md                   # Reserved for repo-level operational scripts
├── tests/
│   ├── README.md
│   └── e2e/                        # Reserved for cross-cutting end-to-end tests
├── logs/                           # Local runtime log output (empty, gitignored content)
├── CLAUDE.md                       # Coding standards and conventions
├── README.md
├── CHANGELOG.md
├── PROJECT_PROGRESS.md
├── Project_Structure.md            # This document
├── Project_Structure.txt
├── Project_SRS.md
├── Project_SRS.pdf
├── PROJECT_SUMMARY.md
├── CONTRIBUTING.md
├── LICENSE
└── .gitignore
```

---

## 3. Backend Explanation

The backend is a FastAPI application under `backend/app/`, structured as a strict layered architecture:

```
Router  →  Service  →  Repository  →  SQLAlchemy  →  PostgreSQL
```

- **`routers/`** — one file per domain (`auth`, `users`, `reference_data`, `schedule`, `attendance`, `exams`, `results`, `fees`, `notifications`, `reports`, `health`). Routers shape the HTTP request/response and delegate immediately to a service. They contain no business logic and no direct ORM access.
- **`services/`** — own every business rule, validation rule, and RBAC/ownership check. Services call repositories only, never the ORM session directly.
- **`repositories/`** — the only place SQLAlchemy queries are written. No business logic.
- **`schemas/`** — every request body and response model is a Pydantic schema; ORM models are never returned directly from a router.
- **`models/`** — one SQLAlchemy model per database table (26 total).
- **`middleware/`** — cross-cutting concerns: JWT verification (`auth.py`), role-based access control (`rbac.py`), a fixed-window login rate limiter (`rate_limit.py`), global exception handling (`error_handlers.py`), and structured request logging (`logging.py`).
- **`notifications/dispatcher.py`** — the four automatic notification triggers (result published, schedule change, attendance warning, fee due), each dispatched after its originating transaction commits.
- **`pdf/`** — server-side PDF generation (transcripts, invoices) via `reportlab`.
- **`core/`** — environment-driven settings (`config.py`), structured logging setup, and password/JWT security utilities.
- **`db/`** — the SQLAlchemy engine, session factory, and the `get_db` FastAPI dependency.

---

## 4. Frontend Explanation

The frontend is a React 18 + TypeScript single-page application built with Vite.

- **`pages/`** — one folder per screen, matching the roles/screens defined in `Requirement_Analysis.md` §7 (Login, Dashboard with four role-specific widget sets, Profile, Timetable, Attendance, Exam List/Room, Teacher Exam Builder/Grading Interface/Attendance Marker, Results View, Fee Centre, Notifications, and the Admin screens: User Management, Result Approval, Fee Dashboard, Reports).
- **`features/`** — one module per API domain, each wrapping its endpoints in typed React Query hooks. Components call these hooks; they never call `axios`/`fetch` directly.
- **`auth/`** — token storage, the `AuthContext` (`useAuth()`), and `RouteGuard` (redirects unauthenticated users to `/login`).
- **`components/`** — the shared `AppLayout` (role-composed navigation shell) and the root `ErrorBoundary`.
- **`lib/`** — the shared Axios client (`apiClient.ts`, with automatic token attachment and silent refresh-and-retry on 401), the client-error reporting sink, and the health-check hook.
- **`app/`** — provider composition (`AppProviders`: React Query, Theme, Auth) and the React Router route table.
- Server state lives exclusively in React Query; client-only UI state (form drafts, active tab, modal open/closed) uses local component state.

---

## 5. Database

PostgreSQL, accessed exclusively through the SQLAlchemy ORM (no raw string-interpolated SQL anywhere in the codebase). 26 tables, grouped by domain:

| Domain | Tables |
|---|---|
| Reference data | `department`, `course`, `room`, `semester` |
| Identity & roles | `user`, `student`, `teacher`, `parent`, `admin`, `parent_student_link` |
| Scheduling | `class_session`, `enrollment`, `schedule_entry`, `schedule_change_request` |
| Attendance | `attendance_record` |
| Exams & grading | `exam`, `question`, `question_option`, `exam_submission`, `answer`, `question_grade` |
| Results | `result` |
| Fees | `fee_structure`, `invoice`, `payment` |
| Notifications | `notification` |

All foreign keys, unique constraints, and check constraints are declared on the SQLAlchemy models themselves (not just in migrations), so `alembic revision --autogenerate` produces an empty diff against the current schema. Full column-level design is in [`docs/Database_Design.md`](docs/Database_Design.md).

---

## 6. Alembic

Ten sequential migrations (`0001`–`0010`), one per milestone that introduced schema:

```
0001 initial_baseline        →  empty baseline (Milestone 0)
0002 core_reference_data     →  department, course, room, semester
0003 user                    →  user (auth)
0004 role_profiles           →  student, teacher, parent, admin, parent_student_link
0005 scheduling              →  class_session, enrollment, schedule_entry, schedule_change_request
0006 attendance              →  attendance_record
0007 exams                   →  exam, question, question_option, exam_submission, answer, question_grade
0008 results                 →  result
0009 fees                    →  fee_structure, invoice, payment
0010 notifications           →  notification
```

Current head: `0010`. `alembic upgrade head`, `alembic current`, `alembic heads`, and `alembic revision --autogenerate` (empty diff) are all part of the project's standard verification routine and are wired into `backend-ci.yml`.

---

## 7. Docker

- **`docker/Dockerfile.backend`** — installs pinned dependencies from `requirements.txt`, copies the application, runs `uvicorn` without `--reload` (production-style image).
- **`docker/Dockerfile.frontend`** — multi-stage build: `npm run build` in a Node stage, then the static `dist/` output is served by `nginx`.
- **`docker/docker-compose.yml`** — local development orchestration: a Postgres 16 service, the backend (bind-mounted, running with `--reload`), and the Vite dev server. This is the local dev loop; the two Dockerfiles above are for staging/deployment-style builds.

---

## 8. GitHub Workflow (CI)

- **`.github/workflows/backend-ci.yml`** — on push/PR touching `backend/**`: spins up a disposable Postgres 16 service container, installs dependencies, runs `pip check`, `alembic upgrade head`, an autogenerate empty-diff check, and the full `pytest` suite.
- **`.github/workflows/frontend-ci.yml`** — on push/PR touching `frontend/**`: installs dependencies, runs `npx tsc --noEmit`, `npm run lint`, `npx vitest run`, and `npm run build`.

---

## 9. Documentation

All design and planning documentation lives in `docs/` (see the [README](README.md#documentation) for the full index) and is treated as the source of truth — implementation does not silently diverge from it. `CLAUDE.md` at the repository root defines the coding standards and conventions that governed every milestone's implementation.

---

## 10. Tests

| Layer | Location | Count | What it covers |
|---|---|---|---|
| Backend unit | `backend/tests/unit/` | — | Service-layer business rules, repositories stubbed — no database required |
| Backend integration | `backend/tests/integration/` | — | Full request → DB → response cycle against a disposable Postgres database |
| Backend total | | **349** | |
| Frontend component | `frontend/tests/pages/` | **7** | Exam timer/auto-submit, grading form entry + validation error, result approval/reject-with-comment workflow |

Backend tests require `TEST_DATABASE_URL` (a disposable database) and are otherwise skipped, never run against a developer's real database. Frontend tests run via Vitest + React Testing Library + jsdom.

---

## 11. Scripts

- **`backend/scripts/seed_admin.py`** — bootstraps the first Admin account from process-level environment variables (never `.env`). Required because account-creation endpoints are Admin-only.
- **`backend/scripts/seed_demo_data.py`** — populates a full demo/development dataset: departments, semesters, rooms, an admin, teachers, students (including one crossing the low-attendance threshold and one with an overdue fee), parents (one linked to multiple children), courses, class sessions, enrollments, schedule entries, exams in every lifecycle state, attendance history, results in every workflow state, fee structures/invoices/payments, and notifications. Idempotent.
- **`scripts/README.md`** (repository root) — reserved for cross-cutting operational scripts spanning both `backend/` and `frontend/`; none exist yet beyond what's described in that file.

---

## 12. Configuration

| File | Purpose |
|---|---|
| `backend/.env.example` | Documented placeholder values for `DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_ALGORITHM`, token expiry, `API_V1_PREFIX`, `FRONTEND_ORIGIN`, `ENVIRONMENT`, `LOG_LEVEL` |
| `frontend/.env.example` | `VITE_API_BASE_URL`, `VITE_API_ROOT_URL` |
| `backend/app/core/config.py` | `Settings` (pydantic-settings) — the single source of truth for environment-driven backend config, including the `is_production` property used to disable `/docs`/`/redoc`/`/openapi.json` in production |
| `backend/alembic.ini` | Alembic configuration (reads the real `DATABASE_URL` via `env.py`, never hardcoded) |
| `frontend/vite.config.ts` | Vite build config + Vitest test config (jsdom environment, setup file) |
| `frontend/tailwind.config.js` | TailwindCSS configuration (dark-mode via class strategy) |
| `frontend/eslint.config.js` | ESLint flat config (recommended + TypeScript + the two core React Hooks rules) |

Real `.env` files are never committed (see `.gitignore`); only the `.env.example` placeholders are tracked.

---

## 13. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser (SPA)                        │
│   React 18 + TypeScript, React Router, React Query, Tailwind │
└───────────────────────────┬───────────────────────────────────┘
                            │  HTTPS, JSON, /api/v1/*
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                    │
│  ┌───────────┐   ┌───────────┐   ┌──────────────┐   ┌──────┐ │
│  │  Routers   │──▶│ Services  │──▶│ Repositories │──▶│ ORM  │ │
│  └───────────┘   └───────────┘   └──────────────┘   └───┬──┘ │
│  Middleware: JWT auth · RBAC · rate limit · error handlers   │
│              · request logging                              │
└───────────────────────────────────────────────────────────┼──┘
                                                             ▼
                                              ┌───────────────────────┐
                                              │  PostgreSQL Database   │
                                              │  26 tables, FK/unique/ │
                                              │  check constraints     │
                                              └───────────────────────┘
```

---

## 14. Authentication Flow

```
1. Client submits POST /api/v1/auth/login { email, password }
2. Rate limiter (app/middleware/rate_limit.py) checks the caller's
   IP has not exceeded 5 attempts in the last 60 seconds → 429 if so
3. AuthService looks up the user by email, verifies the bcrypt hash,
   and rejects a deactivated account (user.is_active = false) → 401/403
4. On success: a short-lived JWT access token and a longer-lived
   refresh token are issued; the refresh token's jti and expiry are
   persisted on the user row (single-active-session-per-user model)
5. Client stores both tokens (frontend/src/auth/tokenStorage.ts) and
   attaches the access token as a Bearer header on every subsequent
   request (frontend/src/lib/apiClient.ts request interceptor)
6. On a 401 response (access token expired), the API client's response
   interceptor calls POST /auth/refresh once, silently, and retries
   the original request with the new access token
7. POST /auth/logout invalidates the current refresh token server-side
```

---

## 15. Authorization Flow

```
1. Every protected route depends on get_current_user (JWT decode +
   signature/expiry check + a live re-check of user.is_active — a
   deactivated account fails authorization immediately even with a
   still-valid token)
2. Role-only checks are enforced via require_roles(*roles), a FastAPI
   dependency applied per-route (e.g. Depends(require_roles("admin")))
3. Ownership/linkage checks (a Student viewing only their own data, a
   Parent viewing only a linked child's data via parent_student_link)
   are enforced in the SERVICE layer on every request — never trusted
   to the frontend, and never satisfied by a role check alone
4. Resources outside a caller's scope return 404 (not 403), so their
   existence is never leaked to an unauthorized caller
5. The frontend's own role-based UI composition (which nav links/
   widgets render per role) is a UX convenience only — every check
   above is re-verified server-side regardless of what the UI shows
```

---

## 16. Request Flow

```
Browser
  → React Query hook (frontend/src/features/<domain>/index.ts)
    → Axios (frontend/src/lib/apiClient.ts) — attaches Bearer token
      → HTTPS request to /api/v1/<domain>/...
        → FastAPI router (backend/app/routers/<domain>.py)
          → Middleware chain: request logging → CORS → auth → RBAC
            → Router function — parses/validates the Pydantic request
              schema, calls exactly one Service method
              → Service — business rules, validation, ownership checks
                → Repository — the SQLAlchemy query
                  → PostgreSQL
```

---

## 17. Response Flow

```
PostgreSQL row(s)
  → Repository returns ORM model instance(s)
    → Service applies any computed/derived fields (e.g. GPA, attendance
      percentage, invoice overdue status — always computed on demand,
      never cached) and constructs a Pydantic response schema
      → Router returns the schema (FastAPI serializes it to JSON)
        → On any error at any layer: a global exception handler
          (backend/app/middleware/error_handlers.py) converts it into
          the single consistent JSON error envelope:
          { "error": { "code", "message", "details" } }
          → Axios response interceptor: a 401 triggers the silent
            refresh-and-retry flow above; other errors propagate to
            the calling React Query hook
            → The page/component renders the result, a loading state,
              or an inline error — every async operation has explicit
              loading and error states (no unhandled promise states)
```
