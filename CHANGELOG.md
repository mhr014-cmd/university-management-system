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
