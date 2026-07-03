# Changelog

All notable changes to this project are documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/) — grouped under `### Added` / `### Changed` / `### Fixed` per release. This project is pre-release throughout implementation, so all entries accumulate under `[Unreleased]` until a milestone is judged ready to tag (see `PROJECT_PROGRESS.md` for milestone-level status).

---

## [Unreleased]

### Added (Milestone 2 — Authentication & Authorization)
- `user` table (Alembic revision `0003_user`): id, email (unique), password_hash, role (`student`/`teacher`/`parent`/`admin`), is_active, `current_refresh_token_jti`/`refresh_token_expires_at` (single-active-session refresh tracking — see `Database_Design.md` §6.1 M2 design note), created_at/updated_at
- Password hashing (`bcrypt` directly) and JWT access/refresh token issuance/decoding (`app/core/security.py`)
- `AuthService` (`app/services/auth_service.py`): login (BR-006 deactivation check), refresh (type check, jti-match rotation/reuse detection, expiry check), logout, change-password (VR-002)
- 4 new REST endpoints under `/api/v1/auth`: `POST /login`, `POST /refresh`, `POST /logout`, `PUT /password`
- `get_current_user` (JWT bearer decode + per-request `is_active` re-check) and `require_roles(*roles)` RBAC dependency factory (`app/middleware/auth.py`, `app/middleware/rbac.py`)
- RBAC retrofit on all 12 Milestone 1 reference-data endpoints: GET routes require any authenticated role, POST routes require Admin — closing the Milestone 1 "endpoints are unauthenticated" known issue
- Frontend auth module: `tokenStorage.ts` (localStorage-backed session persistence), `apiClient.ts` interceptors (Bearer token attachment, silent refresh-and-retry on 401), `AuthContext`/`useAuth`, `RouteGuard` (redirect-to-`/login` for unauthenticated access), a real Login page, and a logout action + user email display in `AppLayout`
- Backend test suite: `tests/unit/test_security.py`, `tests/unit/test_auth_service.py` (repository-stubbed, no DB), `tests/integration/test_auth_router.py`, `tests/integration/test_reference_data_rbac.py` (full request→DB→response against a disposable Postgres test database, gated on `TEST_DATABASE_URL`) — 41 tests total, covering BR-006, VR-002, refresh-token rotation/reuse, and RBAC 401/403 negative cases

### Fixed (Milestone 2)
- `passlib==1.7.4` (its final, unmaintained release) crashes on the first `hash_password` call against `bcrypt>=4.1`, because it probes a `bcrypt.__about__.__version__` attribute modern `bcrypt` removed — replaced with direct `bcrypt.hashpw`/`bcrypt.checkpw` calls; `passlib[bcrypt]` dropped from `requirements.txt`
- Alembic migration `0003_user`: an explicit `user_role.create(...)` call in `upgrade()` duplicated the enum type `op.create_table()` already creates implicitly, causing `DuplicateObject` on a real database; removed the redundant call. Also confirmed (via a real upgrade/downgrade/upgrade cycle) that `op.drop_table()` does not drop the enum type on its own — the explicit `user_role.drop(..., checkfirst=True)` in `downgrade()` is required and was kept
- Frontend: the Axios response interceptor's silent-refresh-and-redirect logic was firing on `/auth/login`'s own 401 (wrong password) — with no refresh token yet available, this force-navigated to `/login`, wiping the login form's error state before the "Incorrect email or password" message was ever shown. Fixed by excluding `/auth/login` and `/auth/refresh` from the refresh-and-retry flow
- `backend/tests/` had no fixtures or test files at all despite `CLAUDE.md` §10's per-BR/VR-rule testing requirement (`pytest` reported "no tests ran") — added the missing test suite (see Added, above) as part of Milestone 2's own self-review

### Changed
- `.gitignore` env-file patterns broadened from exact `.env` matches to also cover `.env.local` and other common variants (`.env.*.local`, `.env.development`, `.env.production`, `.env.test`) after `backend/.env.local` was found sitting untracked (one `git add` away from being committed) under the old, narrower patterns
- Codified a mandatory "never touch local `.env` files" policy in `CLAUDE.md` §8/§14 — no deleting, overwriting, recreating, renaming, or cleaning `backend/.env`/`frontend/.env` under any circumstance, including temporary use during verification; env var changes go through `.env.example` only, with instructions for the user to copy manually
- Codified a mandatory pre-commit `git status` check in `CLAUDE.md` §8/§14 and `docs/MILESTONE_VERIFICATION_CHECKLIST.md` §11 — run immediately before staging and before committing; if any local developer configuration file (`.env`/variants, IDE settings, personal secrets) appears unexpectedly in the diff, stop and ask for confirmation rather than committing or modifying it

### Added
- Project foundation: FastAPI backend and React 18 + TypeScript frontend scaffolding (Milestone 0)
- FastAPI application factory with settings-driven configuration (fail-fast validation on missing `DATABASE_URL`/`JWT_SECRET_KEY`), structured JSON logging, CORS, global exception handlers (standard `{"error":{...}}` envelope), and request logging middleware
- PostgreSQL configuration: SQLAlchemy engine/session wiring, Alembic configured against `Base.metadata` with an empty baseline revision
- Health endpoint (`GET /health`) with live database connectivity check
- Frontend routing (React Router), server state (React Query), and API client (Axios, split into versioned business client + unversioned infra client)
- Light/dark theme provider and shared app layout shell
- Docker Compose local development stack (Postgres + backend with reload + Vite dev server)
- `PROJECT_PROGRESS.md` milestone progress tracker
- Complete planning documentation set (`docs/`): Requirement Analysis, System Architecture, Database Design, API Contract, UI Wireframes, Requirement Traceability Matrix, Implementation Roadmap, Proposal vs. Engineering Additions
- Core reference data domain (Milestone 1): SQLAlchemy models, Pydantic schemas, repository, service, and router for Department, Course, Room, and Semester, matching `Database_Design.md` exactly
- 12 new REST endpoints (list/create/get-by-id for each of Department, Course, Room, Semester) under `/api/v1`, newly documented in `API_Contract.md` §10 as a Derived (unavoidable-plumbing) domain, not a proposal feature
- Alembic revision `0002_core_reference_data`: creates `department`, `course`, `room`, `semester` tables with all documented unique constraints, the `course.department_id` FK (`ON DELETE RESTRICT`) and index, and the `semester.start_date < end_date` check constraint

### Fixed
- `alembic upgrade head` failed with `ModuleNotFoundError: No module named 'app'` when run as `cd backend && alembic upgrade head` (the plain console-script entry point) on a real machine — it had only ever been verified via `python -m alembic`, which (unlike the bare `alembic` command) implicitly adds the current working directory to `sys.path`. Fixed with the standard Alembic mechanism (`prepend_sys_path = .` in `alembic.ini`, relative to the ini file's own location, not the caller's cwd) plus a `__file__`-based `sys.path` fallback directly in `env.py` as defense-in-depth. Verified by reproducing the exact failure first (fresh clone, fresh venv, bare `alembic` console script), then confirming it's resolved, then confirming `python -m alembic` still works (no regression).
- 404 responses on unmatched routes were bypassing the custom exception handler and returning Starlette's default `{"detail": "Not Found"}` instead of the project's standard error envelope — caused by FastAPI registering default handlers under `fastapi.HTTPException` and `starlette.exceptions.HTTPException` as two separate dict keys; fixed by registering the handler against the Starlette base class
- Backend dependencies were floating version ranges (`>=`, `<`) rather than exact pins, making installs non-reproducible
- `pytest`/`pytest-asyncio` pins were stale (captured from an earlier resolver snapshot); re-resolved from a fully clean install to `9.1.1`/`1.4.0`, the actual current releases
- `HTTP_422_UNPROCESSABLE_ENTITY` deprecation warning fixed — renamed to `HTTP_422_UNPROCESSABLE_CONTENT` (same integer value, Starlette's own RFC-alignment rename, no behavior change)
- Pydantic v2 error details for custom `@model_validator` failures embed a raw, non-JSON-serializable exception instance in `error["ctx"]["error"]`; the shared validation exception handler was passing this straight to `json.dumps()`, causing an unhandled `TypeError` (surfaced as a 500) instead of the documented 422 whenever `SemesterCreate`'s `start_date < end_date` check failed. Fixed by routing `exc.errors()` through `fastapi.encoders.jsonable_encoder`.

### Changed
- Backend dependencies re-pinned to exact, clean-dependency-resolution-verified versions across two independent clean virtual environments (`fastapi`, `starlette`, `pydantic`/`pydantic-core`, `uvicorn`, `sqlalchemy`, `alembic`, and the full transitive graph)
- Investigated and confirmed `starlette==1.3.1` as a legitimate, currently-correct pin (not a bad resolution) via PyPI's JSON API and FastAPI's own GitHub release notes — FastAPI's `pyproject.toml` declares `starlette>=0.46.0` and its CI has merged dependabot bumps up to `1.3.1`
- API display metadata (OpenAPI title, description, Swagger UI title, startup log banner) renamed from "ICT Education API" to "University Management System API" — no routes, business logic, package names, or schema changed
- `docs/Proposal_vs_Engineering_Additions.md` extended to cover frontend additions, not just API endpoints, after a proposal-traceability review found two undocumented UI elements (theme toggle, Dashboard health widget); both logged as Design Enhancements with an explicit disposition (keep vs. remove-at-M10)
- `docs/Proposal_vs_Engineering_Additions.md` further extended to cover backend middleware/utilities after a full 9-document self-review (`CLAUDE.md` §14 item 12) found seven unlogged items (exception handlers, request logging, structured logging config, settings validation, DB session/engine, CORS, Alembic baseline); all logged as Derived, permanent, no removal needed
- `docs/MILESTONE_VERIFICATION_CHECKLIST.md` gains Section 13 (Full Documentation Self-Review), required before any milestone is marked Completed
- `PROJECT_PROGRESS.md`'s stale `Current Git Commit` field (pointing several commits behind actual HEAD) corrected; live browser verification (real backend + frontend, cross-origin `/health` call, console/network inspection) performed and recorded for Milestone 0, closing a gap where the original completion pass had only used `TestClient`, not a real browser
- Milestone 0 re-verified end-to-end from a genuinely fresh `git clone` (isolated temp directory, not the working tree): `pip install --no-cache-dir` with zero cache, exact-pinned versions confirmed programmatically, `npm ci` from the committed lockfile, real `uvicorn`/`vite` process boots hit over real HTTP — all pass identically to the working-tree verification

### Known Issues
- **Resolved in Milestone 2:** `alembic upgrade head`/`downgrade`/`upgrade` execution against a live database is now demonstrated — real local PostgreSQL credentials became available during M2 and were used, on disposable databases created and dropped solely for verification, to run full upgrade/downgrade/upgrade cycles for revisions `0001`→`0002`→`0003` with the bare `alembic` console-script entry point (the specific form that previously failed on a real machine — see M1's post-completion fix, below). Never run against the developer's real `university_management_db`.
- **Resolved in Milestone 2:** Milestone 1's reference-data endpoints (`/api/v1/departments`, `/courses`, `/rooms`, `/semesters`) are now RBAC-protected (GET: any authenticated role, POST: Admin) — see Added, above.
- Migrations `0002_core_reference_data` and `0003_user` were hand-authored rather than produced by `alembic revision --autogenerate`. Both were written to mirror the SQLAlchemy models exactly and reviewed carefully, and both now have confirmed-working upgrade/downgrade cycles against a real database (see above), but a live autogenerate diff-check (expected to show no changes if the migrations are correct) has still not been performed — recommended before either is trusted in a production deployment.
