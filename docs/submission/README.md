# University Management System (ICT Education)

A role-based REST API and React single-page application that consolidates university attendance, exams, results, fees, scheduling, and notifications into one system, serving four roles — **Student**, **Teacher**, **Parent**, and **Admin** — with permissions enforced at the API layer, not just hidden in the UI.

> This is the submission documentation package. It summarizes the system for evaluation purposes; the authoritative, most-detailed engineering documents live in [`docs/`](../) (see the "Where to look next" table below).

---

## What this system does

- **Authentication & RBAC** — JWT access/refresh tokens with rotation, rate-limited login, role-based access control with per-request ownership verification (a Parent can only ever see their own linked children's data; a Teacher only their own classes).
- **User management** — Admin-managed Student/Teacher accounts, self-service profiles, Parent–Student linking.
- **Academic Setup** — Departments, Courses, Rooms, Semesters — full CRUD via a dedicated Admin screen with searchable-dropdown pickers everywhere a reference-data ID is needed.
- **Scheduling** — Timetables with room/teacher conflict detection, a Teacher-initiated schedule change-request workflow with an Admin approval queue and automatic Teacher notification.
- **Attendance** — Teacher marking/correction, live-computed percentages (never cached), automatic low-attendance warnings to Student and linked Parents, PDF/Excel/CSV export.
- **Exams & Grading** — MCQ/short-answer/descriptive/coding question types, timed exam-taking, per-question teacher grading, draft → open → published lifecycle.
- **Results & Transcripts** — Submit → approve/reject → publish workflow, credit-weighted per-semester GPA, downloadable PDF transcripts (Student and linked Parent).
- **Fees** — Fee structures, auto-generated invoices, payment recording, overdue tracking, downloadable invoice PDF that relabels itself "Receipt" once paid.
- **Notifications** — four automatic triggers (result published, schedule change, attendance warning, fee due), fanned out to both the Student and every linked Parent.
- **Reporting** — Admin attendance/results/fees reports, filterable by department/semester/student, exportable to PDF/Excel/CSV.
- **Role-specific dashboards** for all four roles.

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript, Vite, TailwindCSS, React Router, TanStack React Query, Axios |
| Backend | FastAPI (Python 3.12), SQLAlchemy 2.0, Alembic, Pydantic |
| Database | PostgreSQL |
| Auth | JWT (python-jose), bcrypt |
| Documents | ReportLab (PDF), openpyxl (Excel), stdlib `csv` |
| Testing | pytest (backend), Vitest + React Testing Library (frontend), ESLint |
| CI/CD | GitHub Actions (`backend-ci.yml`, `frontend-ci.yml`) |
| Containers | Docker (`docker-compose` for local development) |

## Project scale (verified, current)

- **82 REST endpoints** across 11 domains (auth, users, reference data, scheduling, attendance, exams, results, fees, notifications, reports, health), all versioned under `/api/v1`.
- **26 database tables**, managed by **10 Alembic migrations** with a single linear head and zero drift against the live ORM models.
- **478 backend tests** (unit + integration, all passing) and **61 frontend component tests** (all passing).
- Layered backend architecture (Router → Service → Repository) enforced without exception across every domain.

## Quick start

See [`INSTALLATION.md`](INSTALLATION.md) for full setup instructions. In short:

```bash
# Backend
cd backend && python -m venv .venv && source .venv/Scripts/activate   # or .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL / JWT_SECRET_KEY
alembic upgrade head
python -m scripts.seed_demo_data
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend && npm install
cp .env.example .env
npm run dev
```

Then open `http://localhost:5173` and log in with one of the [demo accounts](USER_MANUAL.md#demo-accounts).

## Documentation index

| Document | Covers |
|---|---|
| [INSTALLATION.md](INSTALLATION.md) | Full local setup, environment variables, seed data, troubleshooting |
| [USER_MANUAL.md](USER_MANUAL.md) | How to use every screen, per role |
| [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) | Layered architecture, request lifecycle, auth/authz flow |
| [DATABASE_DESIGN.md](DATABASE_DESIGN.md) | Schema summary, ER diagram, constraints |
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | Endpoint reference by domain |
| [TEST_REPORT.md](TEST_REPORT.md) | Test suite composition and latest verified run results |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Docker Compose, CI pipelines, production notes |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Repository folder-by-folder guide |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

### Where to look next (authoritative engineering docs)

This submission package summarizes the system for a reader. The detailed, governing engineering documents — kept in sync with the implementation throughout the build — live in [`docs/`](../):

| For | See |
|---|---|
| Full functional/non-functional requirements (FR-xxx, NFR-xxx, BR-xxx, VR-xxx) | `docs/Requirement_Analysis.md` |
| Full architecture rationale | `docs/System_Architecture.md` |
| Full schema (every column, index, constraint) | `docs/Database_Design.md` |
| Full API contract (every endpoint, request/response shape) | `docs/API_Contract.md` |
| Every capability added beyond the original proposal, and why | `docs/Proposal_vs_Engineering_Additions.md` |
| Requirement-to-implementation traceability | `docs/Requirement_Traceability_Matrix.md` |
| Milestone-by-milestone build history | `PROJECT_PROGRESS.md` |

## Author

**Mahabbat Hossain** — [mhr014@gmail.com](mailto:mhr014@gmail.com)
