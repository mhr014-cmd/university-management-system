# Deployment Guide

## Local development via Docker Compose

`docker/docker-compose.yml` orchestrates three services for a full local stack without installing PostgreSQL or Node.js directly:

```bash
cd docker
docker-compose up
```

| Service | Image/build | Port | Notes |
|---|---|---|---|
| `db` | `postgres:16-alpine` | 5432 | Credentials `ict_education`/`ict_education`/`ict_education` (dev only); healthcheck via `pg_isready` |
| `backend` | Built from `docker/Dockerfile.backend` | 8000 | Runs `uvicorn app.main:app --reload`, bind-mounted to `../backend` for live reload; waits for `db`'s healthcheck |
| `frontend` | `node:20-slim` | 5173 | Runs `npm install && npm run dev`, bind-mounted to `../frontend` |

Both `backend` and `frontend` read their configuration from `../backend/.env` and `../frontend/.env` respectively (`env_file:` in the compose file) — create these from their `.env.example` templates before running `docker-compose up` (see [INSTALLATION.md](INSTALLATION.md)).

This compose setup is a **local development convenience**, not a production deployment topology — it uses the Vite dev server (not a built static bundle) for the frontend and `--reload` (not a production ASGI server invocation) for the backend.

## Production-style container images

Separate, standalone Dockerfiles exist for building deployable images independent of the dev compose setup:

**`docker/Dockerfile.backend`** — `python:3.12-slim` base, installs `libpq-dev` (for `psycopg2-binary`), installs pinned `requirements.txt`, copies source, runs `uvicorn app.main:app --host 0.0.0.0 --port 8000` (no `--reload`). Exposes port 8000.

```bash
docker build -f docker/Dockerfile.backend -t umsm-backend:latest backend/
docker run -p 8000:8000 --env-file backend/.env umsm-backend:latest
```

**`docker/Dockerfile.frontend`** — multi-stage build: `node:20-slim` installs dependencies and runs `npm run build`, then the compiled `dist/` output is copied into an `nginx:alpine` image serving on port 80. This matches the architecture's stated intent that the frontend is a static bundle deployable from any CDN/static host in production — the nginx image is one way to serve that bundle, not the only one.

```bash
docker build -f docker/Dockerfile.frontend -t umsm-frontend:latest frontend/
docker run -p 8080:80 umsm-frontend:latest
```

## Continuous Integration

Two independent GitHub Actions workflows, each triggered only by changes under its own directory (so a frontend-only change doesn't re-run the backend suite and vice versa):

### `backend-ci.yml`

Runs against a real `postgres:16-alpine` service container (never a developer's real database):

1. Set up Python 3.12, install `backend/requirements.txt`.
2. `pip check` — verify no broken/conflicting dependency versions.
3. `alembic upgrade head` — apply all migrations against the fresh CI database.
4. **Schema-drift check**: run `alembic revision --autogenerate`, inspect the output for any "Detected ..." line (meaning the ORM models and the migration history have diverged), delete the generated diff file either way, and fail the build if drift was detected.
5. `pytest` — the full backend suite (`TEST_DATABASE_URL` is set, so integration tests run too).

### `frontend-ci.yml`

1. Set up Node 20, `npm ci` (exact, reproducible install from `package-lock.json`).
2. `npx tsc --noEmit` — type check.
3. `npm run lint` — ESLint.
4. `npx vitest run` — component test suite.
5. `npm run build` — production build must succeed.

Both workflows must pass before a pull request is considered mergeable, matching the same checks required locally before any change is considered complete (see [TEST_REPORT.md](TEST_REPORT.md)).

## Production deployment notes

The target production topology (from [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)) is:

```
Users → CDN/static host (React SPA build) → HTTPS → FastAPI (Uvicorn/Gunicorn, containerized, horizontally scalable) → managed PostgreSQL
```

- **Environment variables** — set `ENVIRONMENT=production` in the backend's environment; this automatically disables `/docs`, `/redoc`, and `/openapi.json`, closing off the API schema from public discovery. Set a real, secret `JWT_SECRET_KEY` (never the `.env.example` placeholder), and point `DATABASE_URL` and `FRONTEND_ORIGIN` (CORS) at the real production values.
- **Migrations as a deployment step** — run `alembic upgrade head` against the production database before the new backend version starts serving traffic, exactly as CI does against its disposable database.
- **API versioning** — the `/api/v1` prefix means a future breaking change can ship as `/api/v2` without breaking an already-deployed frontend build.
- **Known scaling limitation** — the login rate limiter (`POST /auth/login`) is currently in-process memory, so it does not share state across multiple backend replicas behind a load balancer. This is a documented, explicitly out-of-scope-for-now limitation (see the Future Work section of the project's top-level `README.md`), not an oversight — a shared store (e.g. Redis) would be the natural next step for a horizontally-scaled production deployment.
- **No secrets in source control** — `backend/.env` and `frontend/.env` are `.gitignore`d; only the `.env.example` placeholder files are ever committed.

## Health checks

`GET /health` (unauthenticated) reports `{"status": "ok", "environment": "...", "database": "ok"}` and is the correct endpoint for a load balancer, container orchestrator, or uptime monitor to poll.
