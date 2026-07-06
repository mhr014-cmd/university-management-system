# Project Structure

> This is a concise, current guide to the repository layout for submission/evaluation. A deeper, file-by-file walkthrough (including the authentication/authorization/request/response flow narratives) exists at [`Project_Structure.md`](../../Project_Structure.md) in the repository root — note that document predates this submission's most recent work and its headline numbers (endpoint/test counts) are superseded by this document and by [TEST_REPORT.md](TEST_REPORT.md)/[API_DOCUMENTATION.md](API_DOCUMENTATION.md).

## Top level

```
university-management-system/
├── backend/            # FastAPI application, tests, migrations, seed script
├── frontend/            # React + TypeScript SPA, tests
├── docs/                 # Engineering design documents + this submission package
├── docker/               # Dockerfiles + docker-compose for local dev
├── .github/workflows/    # CI pipelines (backend-ci.yml, frontend-ci.yml)
├── database/             # (supplementary database assets, if any)
├── scripts/              # repository-level helper scripts
├── images/               # placeholder location for README screenshots
├── README.md, CHANGELOG.md, PROJECT_SUMMARY.md, LICENSE, CONTRIBUTING.md, CLAUDE.md, PROJECT_PROGRESS.md
```

## `backend/app/` — one folder per architectural layer

```
backend/app/
├── main.py            # FastAPI app factory, router registration, CORS, lifespan
├── core/               # settings, JWT/password security, logging config
├── db/                  # SQLAlchemy session + declarative base
├── models/              # ORM models — one file per table, 26 tables total
├── schemas/             # Pydantic request/response DTOs — one file per domain
├── routers/             # HTTP layer — one file per domain, 11 files, 82 endpoints total
├── services/             # business logic — one file per domain; owns every RBAC/ownership/workflow rule
├── repositories/         # the only place SQLAlchemy queries are written — one file per domain
├── middleware/           # JWT auth dependency, RBAC dependency, rate limiting, global error handlers
├── notifications/        # event-driven notification dispatch (4 trigger types)
├── pdf/                  # ReportLab-based PDF generation (transcript, invoice, attendance report)
├── excel/                # openpyxl-based Excel generation (attendance report)
└── csv/                  # stdlib-csv-based CSV generation (attendance report)
```

```
backend/
├── alembic/versions/     # 10 sequential migrations, single linear head
├── tests/
│   ├── unit/              # 24 files — service logic, repositories stubbed, no database
│   └── integration/       # 8 files — full request→DB→response cycle, disposable Postgres
├── scripts/
│   └── seed_demo_data.py  # idempotent demo dataset (see INSTALLATION.md)
├── requirements.txt       # pinned dependency versions
└── .env.example           # placeholder environment config
```

## `frontend/src/` — feature-sliced SPA

```
frontend/src/
├── app/            # routing (router.tsx), root layout/providers
├── pages/           # one folder per screen — Dashboard, Profile, Timetable, Attendance,
│                     # ExamList/ExamRoom, ResultsView, FeeCentre, Notifications,
│                     # Admin/ (UserManagement, AcademicSetup, ResultApproval, FeeDashboard, Reports),
│                     # Teacher/ (AttendanceMarker, ExamBuilder, GradingInterface)
├── features/         # one React Query hook module per API domain (attendance, results, fees,
│                     # schedule, exams, notifications, users, departments, courses, rooms, semesters)
├── components/       # shared UI — Button, Card, Badge, EmptyState, PageLoader, ConfirmDialog,
│                     # Toast, SearchableSelect, ReportToolbar, ReportLayout, Pagination
├── auth/             # AuthContext, token storage, silent refresh, RouteGuard
├── lib/              # apiClient (Axios instance), exportClient (PDF/Excel/CSV download), usePrint
└── styles/           # Tailwind config, print stylesheet
```

```
frontend/
├── tests/            # 14 files, 61 component tests (Vitest + React Testing Library)
├── package.json       # dependencies, scripts (dev/build/lint/test)
└── .env.example        # placeholder environment config
```

## `docs/` — engineering design documents

| File | Purpose |
|---|---|
| `product_proposal.pdf` | Original project proposal (source of truth for scope) |
| `Requirement_Analysis.md` | Numbered functional/non-functional/business/validation requirements |
| `System_Architecture.md` | Full architecture rationale (this submission's `SYSTEM_ARCHITECTURE.md` summarizes it) |
| `Database_Design.md` | Full schema (this submission's `DATABASE_DESIGN.md` summarizes it) |
| `API_Contract.md` | Full API contract (this submission's `API_DOCUMENTATION.md` summarizes it) |
| `Implementation_Roadmap.md` | Milestone build order and dependencies |
| `Requirement_Traceability_Matrix.md` | Requirement-to-implementation traceability |
| `Proposal_vs_Engineering_Additions.md` | Every capability added beyond the original proposal, classified and justified |
| `UI_Wireframes.md` | Screen-by-screen wireframes |
| `MILESTONE_VERIFICATION_CHECKLIST.md` | Self-review checklist run before any milestone is marked complete |
| `submission/` | **This documentation package** (10 files, generated for evaluation) |

## Why this layout

The backend's one-folder-per-layer structure (`models/`, `schemas/`, `routers/`, `services/`, `repositories/`) is the direct, physical expression of the layered architecture described in [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md): a router file never imports SQLAlchemy directly, and a service file never imports FastAPI's request/response types — the folder boundary is also the dependency boundary. The frontend's `features/` folder mirrors this on the client side: a page component never calls `axios` directly, only a typed hook from `features/`.
