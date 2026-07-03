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

### Fixed
- 404 responses on unmatched routes were bypassing the custom exception handler and returning Starlette's default `{"detail": "Not Found"}` instead of the project's standard error envelope — caused by FastAPI registering default handlers under `fastapi.HTTPException` and `starlette.exceptions.HTTPException` as two separate dict keys; fixed by registering the handler against the Starlette base class
- Backend dependencies were floating version ranges (`>=`, `<`) rather than exact pins, making installs non-reproducible
- `pytest`/`pytest-asyncio` pins were stale (captured from an earlier resolver snapshot); re-resolved from a fully clean install to `9.1.1`/`1.4.0`, the actual current releases

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
- `alembic upgrade head` execution against a live database has not been demonstrated in the sandboxed verification environment — the one reachable local PostgreSQL instance's real credentials are unknown (two reasonable default-credential attempts were made and deliberately not pushed further), and no Docker is available to spin up a throwaway instance. The Alembic mechanism itself (config loading, settings resolution, connection attempt) is confirmed working; only the final connect-and-apply step against a real database is unverified. Low urgency for Milestone 0 (its only revision is an empty baseline, nothing to migrate), but should be confirmed with real credentials or `docker compose up` before Milestone 1 adds real schema.
