# System Architecture (Summary)

> This is a reader-friendly summary for submission/evaluation. The full, authoritative architecture document — including every rationale, edge case, and design decision — is [`docs/System_Architecture.md`](../System_Architecture.md). If anything here and that document ever appear to disagree, `docs/System_Architecture.md` is correct.

## Overall shape

A **decoupled client-server architecture**: a React 18 + TypeScript single-page application communicates exclusively with a versioned REST API (`/api/v1/*`) over HTTPS/JSON. There is no server-side rendering and no direct database access from the client.

```
React 18 + TypeScript SPA
        │  HTTPS / JSON, JWT Bearer token
        ▼
FastAPI REST API (/api/v1/*)
        │  SQLAlchemy ORM, Alembic migrations
        ▼
PostgreSQL
```

The backend is a **layered monolith** — one deployable FastAPI service, internally organized into presentation, business-logic, and data-access layers. This was a deliberate choice given the project's scope and timeline: it rewards a working, coherent system over distributed-systems complexity, while the internal layering still keeps concerns cleanly separated and independently testable.

## Backend layering

Every one of the 11 backend domains (auth, users, reference data, scheduling, attendance, exams, results, fees, notifications, reports, health) follows the same four-layer structure without exception:

1. **Router** (`app/routers/`) — shapes the HTTP request/response and enforces role-only RBAC via a dependency. Never touches the ORM session or contains business logic.
2. **Service** (`app/services/`) — owns every business rule, validation rule not expressible in a Pydantic schema, and ownership/linkage check (e.g. "this Parent is actually linked to this Student"). Calls one or more repositories; never the ORM session directly.
3. **Repository** (`app/repositories/`) — the only place SQLAlchemy queries are written, one file per domain.
4. **Cross-cutting middleware** — JWT authentication, RBAC dependencies, global exception handlers, and request logging, applied uniformly via FastAPI's dependency injection rather than duplicated per router.

**Request lifecycle:** JWT validated → role checked → Pydantic schema validates the body → router delegates to a service method → service applies business rules and calls repositories → repository executes parameterized SQLAlchemy queries → response serialized back through a Pydantic schema (never a raw ORM model) → any error at any layer is caught by a global exception handler and returned in one consistent JSON shape.

## Frontend layering

A **feature-sliced SPA**:

- **`app/`** — routing and the root layout/providers.
- **`pages/`** — one component tree per screen (Dashboard, Profile, Timetable, Attendance, Exams, Results, Fee Centre, Notifications, and the Admin/Teacher-only screens).
- **`features/`** — one typed React Query hook module per API domain (`useAttendance`, `useResults`, `useFees`, `useSchedule`, `useNotifications`, ...). Components call these hooks; they never call `axios`/`fetch` directly.
- **`components/`** — shared, reusable UI (tables, badges, forms, the `ReportToolbar` Print/PDF/Excel/CSV export bar, `SearchableSelect`).
- **`auth/`** — token storage, silent refresh, route guarding.

**State ownership:** all server state (exams, results, attendance, fees, schedule) lives exclusively in React Query and is never duplicated into component or global state. Client-only UI state (a modal's open/closed flag, a form draft) uses local component state. Role-based screens (Timetable, Attendance, Results, Fee Centre) share one component tree per screen that branches internally on the current user's role, rather than four fully separate page trees.

## Authentication & authorization

- **Login** issues a short-lived JWT access token and a longer-lived, rotating refresh token. `POST /auth/login` is rate-limited.
- Every subsequent request attaches the access token as `Authorization: Bearer <token>`.
- A **role check** (via a `require_roles()` dependency) happens on every protected endpoint.
- An **ownership check** happens in the service layer wherever role alone is insufficient — e.g. `GET /attendance/me`, `GET /results/me`, and `GET /fees/me` all re-verify, on every single request, that the calling Parent is actually linked to the requested Student (never trusted from a prior login or from the frontend alone).
- A deactivated account (`is_active = false`) fails authorization immediately, even with a still-valid, unexpired token.
- File-download endpoints (transcript PDF, invoice PDF, attendance PDF/Excel/CSV) re-validate the same ownership rule inside the service layer before generating the file — a role-only check at the router is never treated as sufficient by itself.

## Error handling & logging

All errors — validation (`422`), authentication (`401`), authorization (`403`/`404`), business-rule conflicts (`409`), and unexpected failures (`500`) — are translated by global exception handlers into one consistent JSON error shape, rather than each router formatting its own. `5xx` responses log a full stack trace server-side and never leak internals to the client; `4xx` responses log at lower severity. Sensitive actions (result approval, payment recording, account creation/deactivation, schedule changes) are logged as discrete audit events.

## Notifications

Event-driven, not polled: a service raises a notification immediately after its own transaction commits (e.g. `result_service.approve_or_reject()` calls the notification dispatcher only after the approval itself has already succeeded). Four notification types exist — `result_published`, `schedule_change`, `attendance_warning`, `fee_due` — and every one of them fans out to both the directly-affected Student and every Parent linked to that Student.

## PDF/Excel/CSV generation

Transcripts, invoices, and attendance reports are generated on demand inside the request/response cycle (via `fastapi.concurrency.run_in_threadpool` to avoid blocking the async event loop), using ReportLab (PDF) and openpyxl (Excel); CSV uses only Python's standard library `csv` module. Nothing is pre-generated or stored — every document reflects live data at download time.

## Deployment topology

- **Frontend** — built as static assets, deployable independently from any CDN/static host.
- **Backend** — a stateless, containerized FastAPI service (Uvicorn/Gunicorn), horizontally scalable except for the current in-memory login rate limiter (a documented, scoped limitation — see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)).
- **Database** — a separately managed PostgreSQL instance.
- **API versioning** — the `/api/v1` prefix allows a future `/api/v2` without breaking existing frontend deployments.

See [`docs/System_Architecture.md`](../System_Architecture.md) for the full authentication/authorization flow diagrams, the complete error-response shape, the full technology-stack rationale table, and every documented design tradeoff.
