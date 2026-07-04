# ICT Education — University Management System

A web platform consolidating university operations — attendance, exams, results, fees, and scheduling — into a single system, replacing spreadsheets, email-based results, and siloed finance tools.

**Status:** All 12 milestones (0–11) complete and approved — authentication, user management, scheduling, attendance, exams/grading, results/transcripts, fees, notifications, role-specific dashboards/reporting, and final hardening/testing/deployment prep are all implemented. This is the project's final release — see [`docs/Implementation_Roadmap.md`](docs/Implementation_Roadmap.md) and [`PROJECT_PROGRESS.md`](PROJECT_PROGRESS.md) for the full milestone history.

## Documentation

All design and planning documentation lives in [`docs/`](docs/):

| Document | Contents |
|---|---|
| [`product_proposal.pdf`](docs/product_proposal.pdf) | Original project specification |
| [`Requirement_Analysis.md`](docs/Requirement_Analysis.md) | Numbered functional/non-functional requirements |
| [`System_Architecture.md`](docs/System_Architecture.md) | Architecture, auth/authz flows, folder structure |
| [`Database_Design.md`](docs/Database_Design.md) | Full schema, relationships, constraints |
| [`Implementation_Roadmap.md`](docs/Implementation_Roadmap.md) | Milestone-by-milestone build order |
| [`Requirement_Traceability_Matrix.md`](docs/Requirement_Traceability_Matrix.md) | Every requirement traced to tables/APIs/pages/status |
| [`API_Contract.md`](docs/API_Contract.md) | Full REST API documentation |
| [`UI_Wireframes.md`](docs/UI_Wireframes.md) | Text wireframes for every required page |
| [`Proposal_vs_Engineering_Additions.md`](docs/Proposal_vs_Engineering_Additions.md) | Every endpoint added beyond the original proposal, and why |

See [`CLAUDE.md`](CLAUDE.md) for coding standards and conventions governing this repository.

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript |
| Styling | TailwindCSS |
| API data layer (frontend) | React Query |
| Backend | FastAPI (Python 3.12) |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Auth | JWT (access + refresh tokens), role-based access control |

## Repository Structure

```
university-management-system/
├── docs/           # design & planning documentation
├── backend/        # FastAPI application, Alembic migrations, backend tests
├── frontend/       # React + TypeScript SPA
├── database/       # seed data and supplementary DB assets
├── scripts/        # repository-level operational scripts
├── tests/          # cross-cutting / end-to-end tests
├── docker/         # Dockerfiles and docker-compose for local dev
└── .github/workflows/  # CI pipelines
```

## Getting Started

### Option A — Docker Compose (recommended, starts Postgres too)
```
cd docker
docker compose up
```
This starts Postgres on `5432`, the backend on `8000` (with reload), and the frontend dev server on `5173`. Copy `backend/.env.example` to `backend/.env` and `frontend/.env.example` to `frontend/.env` first (docker-compose reads them via `env_file`); the default `DATABASE_URL` in `backend/.env.example` must match the `db` service credentials (`postgresql://ict_education:ict_education@db:5432/ict_education` when running via Docker — the example file's `localhost` default is for Option B below).

### Option B — Run natively

**Backend** (requires a running PostgreSQL instance):
```
cd backend
pip install -r requirements.txt
cp .env.example .env    # edit DATABASE_URL, JWT_SECRET_KEY to match your local Postgres
uvicorn app.main:app --reload
```
Verify: `curl http://localhost:8000/health` should return `{"status":"ok","environment":"development","database":"ok"}`.

**Frontend**:
```
cd frontend
npm install
cp .env.example .env
npm run dev
```
Open `http://localhost:5173` — it redirects to `/login`, and the Dashboard page (`/dashboard`) shows role-specific widgets after signing in.

## Deadline

Submission deadline: **July 13, 2026**. See `Implementation_Roadmap.md` for the schedule-risk assessment and milestone prioritization.
