# Changelog

All notable changes to this project are documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/) — grouped under `### Added` / `### Changed` / `### Fixed` per release. This project is pre-release throughout implementation, so all entries accumulate under `[Unreleased]` until a milestone is judged ready to tag (see `PROJECT_PROGRESS.md` for milestone-level status).

---

## [Unreleased]

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
- `alembic upgrade head` execution against a live database has not been demonstrated in the sandboxed verification environment — the one reachable local PostgreSQL instance's real credentials are unknown (two reasonable default-credential attempts were made and deliberately not pushed further), and no Docker is available to spin up a throwaway instance. The Alembic mechanism itself (config loading, settings resolution, connection attempt) is confirmed working; only the final connect-and-apply step against a real database is unverified. Applies to both revision `0001` (Milestone 0, empty baseline, low urgency) and revision `0002` (Milestone 1, real schema — higher urgency, should be confirmed with real credentials or `docker compose up` before this migration is trusted in a real deployment).
- Milestone 1's reference-data endpoints (`/api/v1/departments`, `/courses`, `/rooms`, `/semesters`) are unauthenticated — Milestone 2 (Authentication & Authorization) hasn't landed yet, so there is no RBAC mechanism to apply. Tracked, not accidental; closes when Milestone 2 lands.
- Migration `0002_core_reference_data` was hand-authored rather than produced by `alembic revision --autogenerate`, for the same credentials reason as above. Written to mirror the SQLAlchemy models exactly and reviewed carefully, but a live autogenerate diff-check (expected to show no changes if correct) has not been performed.
