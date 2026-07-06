# Installation Guide

Full local development setup for the University Management System. All commands assume you're starting from the repository root unless noted otherwise.

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.12+ | Backend runtime |
| Node.js | 20+ (with npm) | Frontend runtime |
| PostgreSQL | 16 | Local install or via Docker |
| Git | any recent | Source control |

## 1. Clone the repository

```bash
git clone <repository-url>
cd university-management-system
```

## 2. Backend setup

### 2.1 Create a virtual environment

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 2.2 Install dependencies

```bash
pip install -r requirements.txt
```

This installs FastAPI, SQLAlchemy, Alembic, Pydantic, python-jose (JWT), bcrypt, ReportLab (PDF), openpyxl (Excel), pytest, and their transitive dependencies — see [`requirements.txt`](../../backend/requirements.txt) for the full pinned list.

### 2.3 Configure environment variables

```bash
cp .env.example .env
```

Edit `backend/.env` and set at minimum:

| Variable | Example | Purpose |
|---|---|---|
| `ENVIRONMENT` | `development` | Gates `/docs`, `/redoc`, `/openapi.json` — disabled automatically when set to `production` |
| `LOG_LEVEL` | `INFO` | Backend log verbosity |
| `DATABASE_URL` | `postgresql://user:password@localhost:5432/ict_education` | Must point at a real, running PostgreSQL database |
| `JWT_SECRET_KEY` | *(generate your own)* | Signs access/refresh tokens — never reuse the placeholder in a real deployment |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `API_V1_PREFIX` | `/api/v1` | API route prefix |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | Allowed CORS origin for local frontend dev |

`backend/.env` is developer-local and must never be committed — only `.env.example` is tracked in source control.

### 2.4 Create the database

Create an empty PostgreSQL database matching the name in your `DATABASE_URL` (e.g. `ict_education`), using whatever tool you prefer (`psql`, pgAdmin, or the `docker-compose` setup described in [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)).

### 2.5 Run database migrations

```bash
alembic upgrade head
```

This applies all 10 migrations in order, creating all 26 tables. Alembic must be run from inside `backend/` — if you see `ModuleNotFoundError: No module named 'app'`, you're running it from the wrong directory; use `python -m alembic upgrade head` as a workaround if needed.

### 2.6 Seed demo data (optional but recommended)

```bash
python -m scripts.seed_demo_data
```

Populates a complete demo dataset — 1 Admin, 3 Teachers, 8 Students, 2 Parents, 2 departments, 5 courses, exams in every lifecycle state, attendance history (including one student below the low-attendance threshold), and fee data (including one overdue invoice). It is idempotent — safe to run again. See [USER_MANUAL.md](USER_MANUAL.md#demo-accounts) for the exact login credentials this creates.

### 2.7 Run the backend

```bash
uvicorn app.main:app --reload
```

Verify it's up:

```bash
curl http://localhost:8000/health
# {"status":"ok","environment":"development","database":"ok"}
```

Interactive API docs (Swagger UI) are available at `http://localhost:8000/docs` whenever `ENVIRONMENT` is not `production`.

## 3. Frontend setup

### 3.1 Install dependencies

```bash
cd frontend
npm install
```

### 3.2 Configure environment variables

```bash
cp .env.example .env
```

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` | Versioned business API base URL |
| `VITE_API_ROOT_URL` | `http://localhost:8000` | Unversioned infrastructure endpoint (`/health`) |

### 3.3 Run the frontend

```bash
npm run dev
```

Open `http://localhost:5173` — it redirects to `/login`.

## 4. Verify the installation

```bash
# Backend
cd backend
pytest -q                    # runs unit tests; integration tests are skipped unless TEST_DATABASE_URL is set

# Frontend
cd frontend
npx tsc --noEmit              # TypeScript check
npm run lint                  # ESLint
npx vitest run                # component tests
npm run build                 # production build
```

See [TEST_REPORT.md](TEST_REPORT.md) for what a full, database-backed test run covers and its latest verified results.

## 5. Troubleshooting

| Symptom | Fix |
|---|---|
| `POST /auth/login` returns 401 for every credential | The `user` table is empty — run `python -m scripts.seed_demo_data` after confirming `alembic upgrade head` completed. |
| Backend fails to start / `database: unreachable` | Confirm `DATABASE_URL` in `backend/.env` matches a running PostgreSQL instance and that the named database exists. |
| `alembic upgrade head` fails with `ModuleNotFoundError: No module named 'app'` | Run it from inside `backend/`, or use `python -m alembic upgrade head`. |
| Frontend shows a blank page / network errors | Confirm `VITE_API_BASE_URL` in `frontend/.env` points at the running backend and that the backend is reachable at that address. |
| `npm run lint` or `npx vitest run` fails right after a fresh clone | Run `npm install` first — both rely on devDependencies not installed by default. |
| Integration tests all show as "skipped" | Expected — they require `TEST_DATABASE_URL` pointing at a disposable Postgres database. See [TEST_REPORT.md](TEST_REPORT.md) for how to run them. |
