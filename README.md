<div align="center">

# University Management System (ICT Education)

![Status](https://img.shields.io/badge/status-complete-brightgreen)
![Version](https://img.shields.io/badge/version-2.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-yellow)
![Python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688)
![React](https://img.shields.io/badge/frontend-React%2018-61DAFB)
![PostgreSQL](https://img.shields.io/badge/database-PostgreSQL-4169E1)
![Backend Tests](https://img.shields.io/badge/backend%20tests-380%20passing-success)
![Frontend Tests](https://img.shields.io/badge/frontend%20tests-7%20passing-success)

</div>

# Brief One Line Summary

A role-based REST API and React SPA that consolidates university attendance, exams, results, fees, and scheduling into one system.

# Overview

The University Management System (ICT Education) is a decoupled, full-stack web platform serving four roles — **Student**, **Teacher**, **Admin**, and **Parent** — through a FastAPI (Python 3.12) REST API backend, a PostgreSQL database, and a React 18 + TypeScript single-page frontend. It was built across 12 sequential milestones (M0–M11), each reviewed and approved before the next began, and is released as `v2.0.0`.

The system provides authentication and role-based access control, student/teacher/parent account management, department/course/room/semester reference data, class scheduling with conflict detection, attendance tracking with automatic low-attendance warnings, exam creation and timed exam-taking with per-question grading, a result submission → approval → publication workflow with PDF transcripts, fee structure/payment/invoice management with overdue tracking, automatic and manual notifications, role-specific dashboards, and administrative reporting.

# Problem Statement

Universities frequently run core academic and administrative operations across disconnected tools — attendance in spreadsheets, results distributed by email, fee records in a separate finance tool, and schedules maintained ad hoc. This creates data that is hard to audit, easy to lose, and impossible to view holistically per student, per class, or per department. This project replaces that fragmentation with a single system where every role sees exactly the data they are authorized to see, every workflow (grading, result approval, fee tracking) is enforced server-side, and every number shown (attendance percentage, GPA, outstanding balance) is computed live from the same source of truth rather than manually recalculated and copied between tools.

# Dataset

The project ships a **demo seed dataset** (`backend/scripts/seed_demo_data.py`) that populates a complete, realistic development/demo environment in one command. It is idempotent and safe to re-run.

**Demo users** — one account per role, plus supporting accounts to exercise multi-record scenarios:
- 1 Admin, 3 Teachers, 8 Students (across two departments), 2 Parents (one linked to two children, exercising the many-to-many parent–student relationship)
- All demo accounts share a per-role password pattern (see [Demo Credentials](#demo-credentials) below)

**Sample academic data:**
- 2 departments (Computer Science, Business Administration), 2 semesters (one past, one current), 5 courses, 6 class sessions with enrollments and schedule entries
- 4 exams, one in each lifecycle state (draft, scheduled, open, published), covering MCQ, short-answer, descriptive, and coding question types
- One fully graded exam submission and one pending/ungraded submission
- 3 results, one in each workflow state (submitted, published, rejected) — including a credit-weighted GPA on the published result

**Sample fee data:**
- 3 fee structures across departments/semesters
- One fully paid invoice, one partially paid invoice, and one overdue (unpaid, past due date) invoice

**Sample attendance:**
- A multi-week attendance history per enrolled student, with one student deliberately crossing below the 80% low-attendance warning threshold and the rest maintaining full attendance

# Tools and Technologies

**Backend**
- FastAPI (Python 3.12), SQLAlchemy 2.0 (ORM), Alembic (migrations), Pydantic / pydantic-settings, python-jose (JWT), bcrypt, ReportLab (PDF generation), pytest

**Frontend**
- React 18, TypeScript, Vite, TailwindCSS, React Router, React Query (TanStack Query), Axios

**Database**
- PostgreSQL

**Testing**
- pytest (backend unit + integration), Vitest + React Testing Library + jsdom (frontend component tests), ESLint (flat config)

**CI/CD**
- GitHub Actions (`backend-ci.yml`, `frontend-ci.yml`)

**Docker**
- `docker-compose` for local development (PostgreSQL + backend + Vite dev server); separate production-style `Dockerfile.backend` / `Dockerfile.frontend`

**Git**
- Git, with a milestone-per-feature-slice branching/commit discipline (see `CHANGELOG.md` and `PROJECT_PROGRESS.md` for the full history)

**Development Environment**
- Windows / macOS / Linux, Python 3.12 virtual environment, Node.js 20, a local or containerized PostgreSQL 16 instance

# Methods

**Request path:**

```
React (SPA)
    ↓
REST API (HTTPS, JSON, /api/v1/*)
    ↓
FastAPI
    ↓
Router          — shapes the HTTP request/response only
    ↓
Service         — owns every business rule, validation rule, and RBAC/ownership check
    ↓
Repository      — the only place SQLAlchemy queries are written
    ↓
SQLAlchemy
    ↓
PostgreSQL
```

This layering is enforced without exception across all 11 backend domains: a router never touches the ORM session directly, and a service never receives a raw HTTP request object.

**JWT Authentication** — login issues a short-lived access token and a longer-lived, rotating refresh token; a deactivated account fails authentication immediately even with a still-valid token; `POST /auth/login` is rate-limited (5 attempts / 60 seconds / IP).

**RBAC (Role-Based Access Control)** — every endpoint requires an authenticated role via a `require_roles()` dependency; ownership/linkage checks (a Student's own data, a Parent's linked child) are re-verified in the service layer on every request, never trusted to the frontend.

**Repository Pattern** — all SQLAlchemy queries live in `app/repositories/`, one file per domain, so the same query is never duplicated across services.

**Dependency Injection** — FastAPI's `Depends()` wires the database session, the current authenticated user, and role/rate-limit checks into every route function without any router owning that construction logic itself.

**Service Layer** — one service per domain owns the actual business rules (e.g. the result approval workflow, invoice auto-generation, exam grading validation) independent of both the HTTP layer above it and the SQL layer below it.

**Alembic Migration** — every schema change is a reviewed, versioned migration; 10 sequential revisions currently exist, with a single head and an empty `autogenerate` diff against the live models.

**Validation** — every request body is a Pydantic schema validated before it reaches business logic; business rules that Pydantic cannot express (e.g. "a reject decision requires a comment") are enforced in the service layer.

**Testing Strategy** — unit tests exercise service-layer business logic with repositories stubbed (no database); integration tests exercise the full request → database → response cycle against a disposable PostgreSQL database, never a developer's real database; frontend component tests cover the three most interaction-critical flows (exam timer, grading form, approval workflow).

# Key Insights

**Problems solved:** a single, auditable source of truth for attendance/results/fees; no more email-distributed results or spreadsheet-tracked attendance; every workflow (grading → result approval, fee overdue tracking) has an explicit, tested state machine rather than an informal process.

**Benefits:** role-appropriate dashboards mean each user sees only what's relevant to them; computed-on-demand figures (GPA, attendance %, outstanding balance) can never drift out of sync with the underlying records, because they are never stored separately from them.

**Architecture decisions:** the strict Router → Service → Repository layering was chosen specifically so that business rules never leak into either the HTTP layer or the SQL layer — this made it possible to unit-test every business rule without a database, while still integration-testing the full stack separately.

**Scalability:** the frontend is a static build deployable independently via any CDN; the backend is a stateless container that can run multiple replicas behind a load balancer (the one current exception is the in-memory login rate limiter, documented as a known limitation for horizontally-scaled deployments — see Future Work).

**Security:** JWT with short-lived access tokens and rotating refresh tokens; bcrypt password hashing; RBAC and ownership enforced server-side on every request, never only in the UI; login rate limiting; API documentation (`/docs`, `/redoc`, `/openapi.json`) automatically disabled when `ENVIRONMENT=production`.

**Maintainability:** one file per domain across models/schemas/repositories/services/routers/features keeps each concern's blast radius small; 380 backend tests and 7 frontend tests mean the layered architecture's contracts are continuously verified, not just documented.

# Dashboard / Model / Output

> Screenshots are not embedded in this repository. The placeholders below indicate where to add them.

- `images/login.png` — Login screen
- `images/admin-dashboard.png` — Admin Dashboard (pending approvals, overdue fees, recent signups)
- `images/student-dashboard.png` — Student Dashboard (upcoming exams, attendance %, fee status, recent results)
- `images/teacher-dashboard.png` — Teacher Dashboard (classes today, pending grading)
- `images/parent-dashboard.png` — Parent Dashboard (fee status, recent results)
- `images/swagger.png` — Swagger / OpenAPI documentation (`/docs`)
- `images/database-erd.png` — Database entity-relationship diagram

---

# How to Run this Project

## Prerequisites

- **Python** 3.12+
- **Node.js** 20+ (with npm)
- **PostgreSQL** 16 (local install or via Docker)
- Git

## Clone Repository

```
git clone https://github.com/mhr014-cmd/university-management-system.git
cd university-management-system
```

## Virtual Environment

```
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

## Install Backend

```
pip install -r requirements.txt
```

## Install Frontend

```
cd ../frontend
npm install
```

## Configure .env

```
cd ../backend
cp .env.example .env      # edit DATABASE_URL and JWT_SECRET_KEY to match your local Postgres

cd ../frontend
cp .env.example .env      # defaults point at http://localhost:8000
```

`backend/.env` and `frontend/.env` are developer-local and are never committed — only the `.env.example` placeholders are tracked.

## Run Alembic

```
cd backend
alembic upgrade head
```

## Run Demo Seed

```
python -m scripts.seed_demo_data
```

This populates the full demo dataset described above. It is idempotent — running it again is a safe no-op once seeded.

## Run Backend

```
uvicorn app.main:app --reload
```

Verify: `curl http://localhost:8000/health` should return `{"status":"ok","environment":"development","database":"ok"}`.

## Run Frontend

```
cd ../frontend
npm run dev
```

Open `http://localhost:5173` — it redirects to `/login`.

## Swagger

Interactive API documentation is available at `http://localhost:8000/docs` (and the raw schema at `/openapi.json`) whenever `ENVIRONMENT` is not `production`.

## Demo Credentials

| Role | Email | Password |
|---|---|---|
| Admin | `admin@ictedu.example` | `DemoAdmin123!` |
| Teacher | `teacher1@ictedu.example` | `DemoTeacher123!` |
| Student | `student1@ictedu.example` | `DemoStudent123!` |
| Parent | `parent1@ictedu.example` | `DemoParent123!` |

(`student1` is deliberately seeded with low attendance and a published result, to exercise both the warning badge and the GPA/transcript flow. `parent1` is linked to `student1`.)

## Troubleshooting

- **`POST /auth/login` returns 401 for every credential:** the `user` table is empty — the demo seed was never run against this database. Run `python -m scripts.seed_demo_data` (see above) after confirming `alembic upgrade head` has completed.
- **Backend fails to start / `database: unreachable`:** confirm `DATABASE_URL` in `backend/.env` matches a running PostgreSQL instance and that the database named in the URL exists.
- **`alembic upgrade head` fails with `ModuleNotFoundError: No module named 'app'`:** run it from inside `backend/` (not the repo root), or use `python -m alembic upgrade head`.
- **Frontend shows a blank page / network errors:** confirm `VITE_API_BASE_URL` in `frontend/.env` points at the running backend, and that the backend is reachable at that address.
- **`npm run lint` or `npx vitest run` fails after a fresh clone:** run `npm install` first — both rely on devDependencies that are not installed by default.

---

# Results & Conclusion

- **68 REST APIs** across 11 domains (auth, users, reference data, scheduling, attendance, exams, results, fees, notifications, reports, health), all versioned under `/api/v1` and returning a consistent JSON error envelope
- **26 database tables**, fully constrained (foreign keys, unique constraints, check constraints), managed by 10 sequential Alembic migrations with a single head and an empty `autogenerate` diff
- **380 backend tests** (unit + integration, all passing) and **7 frontend component tests** (all passing), covering every business rule and the three most interaction-critical UI flows
- **Role-based dashboards** for all four roles, each showing only the data and actions relevant to that role
- **Reporting** — attendance, results, and fees, each filterable by department/semester/student
- **Notifications** — four automatic triggers (result published, schedule change, attendance warning, fee due), dispatched synchronously, plus a manual admin-triggered overdue notice
- **Authentication** — JWT access/refresh tokens with rotation, rate-limited login
- **Authorization** — RBAC and ownership enforced server-side on every one of the 68 endpoints
- **Testing** — a disposable-database discipline throughout; no test ever runs against a real/production database
- **Deployment ready** — Docker images for both backend and frontend, `docker-compose` for local development, and CI pipelines verifying both halves of the stack on every push/PR

All 12 milestones (M0–M11) were delivered, reviewed, and approved sequentially, culminating in the `v2.0.0` release.

# Future Work

The following are realistic, scoped improvements, explicitly not implemented in `v2.0.0`:

- **Redis Rate Limiter** — replace the current in-memory/single-process login rate limiter with a shared store for horizontally-scaled deployments
- **Email Notification** — deliver notifications by email in addition to the in-app feed
- **SMS Notification** — deliver time-sensitive alerts (attendance warnings, fee due dates) by SMS
- **Docker Compose Production** — a production-oriented compose profile (Gunicorn workers, reverse proxy/TLS termination, managed Postgres)
- **Cloud Deployment** — provider-specific deployment automation (no provider was specified by the original project proposal)
- **CI/CD Enhancement** — automated deployment on tag, dependency vulnerability scanning
- **Analytics Dashboard** — trend-over-time views on the Admin dashboard, not just point-in-time snapshots
- **Audit Logs** — a dedicated screen to browse the audit events already logged server-side
- **Mobile App** — a native or hybrid mobile client

---

# Author & Contact

**Author:** Mahabbat Hossain

**GitHub:** [University Management System Repository](https://github.com/mhr014-cmd/university-management-system)

**Email:** [mhr014@gmail.com](mailto:mhr014@gmail.com)

**LinkedIn:** [LinkedIn Profile](https://www.linkedin.com/in/https://www.linkedin.com/in/mahabbatrh/)
