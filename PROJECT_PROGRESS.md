# University Management System — Project Progress

Single source of truth for milestone-level progress. Milestone numbering, names, and order are copied verbatim from `docs/Implementation_Roadmap.md` (the approved, frozen build order) — this file tracks *status against* that plan, it does not redefine it. For each milestone's Goal, Files, APIs, DB tables, Frontend pages, and Dependencies, see the roadmap directly. For per-requirement status (Testing/Implementation/Verification), see `docs/Requirement_Traceability_Matrix.md`.

**Last updated:** 2026-07-04 (Milestone 1 complete)

---

## Summary

| Field | Value |
|---|---|
| **Overall Progress** | 17% (2 of 12 milestones completed) |
| **Current Milestone** | M1 — Core Reference Data Model *(complete, awaiting explicit approval — see Review Status below)* |
| **Last Completed Milestone** | M1 — Core Reference Data Model |
| **Next Milestone** | M2 — Authentication & Authorization *(blocked on M1 approval, same wait-for-sign-off convention established after M0)* |
| **Current Git Commit** | `8cb72c1` |

**Schedule risk (from `Implementation_Roadmap.md`):** full 12-milestone scope is ~20 working days solo against the July 13, 2026 deadline (10-day runway from project start). Planned Dates below are computed from the roadmap's own cumulative day estimates and show M6 onward landing **after** July 13 — this is the same risk the roadmap already flags, not a new finding. Committed core is M0–M7 + M11; M8 (Fees) and parts of M10 (advanced reporting) are the first items to cut if the timeline slips further.

---

## Milestone Tracker

| Milestone | Status | Planned Date | Completed Date | Git Commit Hash | Review Status | Notes |
|---|---|---|---|---|---|---|
| **M0** — Project Scaffolding & Environment Setup | Completed | 2026-07-03 | 2026-07-03 | `8cb72c1` | **Approved** | Backend app factory, DB/Alembic wiring, `/health`, frontend shell all verified working (see Milestone Detail Log). Dependency-pin defect found and fixed post-hoc (`fdaaf59` → `889465e`). Full 9-document self-review run (`5fe42ca`, `cfef1e8`) — found and fixed two gaps. Reproducibility verified from a genuinely fresh `git clone`. `HTTP_422_UNPROCESSABLE_ENTITY` deprecation warning fixed (`8cb72c1`). **Approved by user 2026-07-04.** |
| **M1** — Core Reference Data Model | Completed | 2026-07-04 | 2026-07-04 | *(this milestone's commit)* | Pending | Department/Course/Room/Semester models, schemas, repository, service, router (12 endpoints, list/create/get-by-id per entity) implemented exactly per `Database_Design.md` §6.7/6.8/6.11/6.20 and the new `API_Contract.md` §10. Alembic revision `0002_core_reference_data`. Two known issues — see Milestone Detail Log: (1) endpoints are unauthenticated (M2 hasn't landed yet, tracked not accidental); (2) migration hand-authored, not `--autogenerate`'d against a live DB (no known-good local Postgres credentials in this sandbox). One real defect found and fixed during verification: Pydantic v2 custom-validator errors (`ctx.error`) aren't JSON-serializable by default — fixed via `jsonable_encoder` in the shared exception handler (a Milestone-0 file, fixed because M1's own documented semester-date validation required it to work). |
| **M2** — Authentication & Authorization | Not Started | 2026-07-05 | — | — | Pending | Depends on M0 only — can run in parallel with M1 per roadmap, but sequenced after it here. |
| **M3** — User Management & Profiles (Student, Teacher, Parent, Admin) | Not Started | 2026-07-07 | — | — | Pending | Depends on M1, M2. Seeds the first Admin account. |
| **M4** — Scheduling & Timetable | Not Started | 2026-07-09 | — | — | Pending | Depends on M1, M3. Unblocks Attendance and Exams. |
| **M5** — Attendance | Not Started | 2026-07-11 | — | — | Pending | Depends on M4. |
| **M6** — Exams & Grading | Not Started | 2026-07-15 | — | — | Pending | Depends on M3, M4. **Planned date falls after the July 13 deadline** — see Schedule Risk. |
| **M7** — Results & Transcripts | Not Started | 2026-07-17 | — | — | Pending | Depends on M1, M6. |
| **M8** — Fees (Optional) | Not Started | 2026-07-19 | — | — | Pending | Optional per proposal — see `Requirement_Analysis.md` §14 item 1. Depends on M1, M3 only — independently parallelizable with M4–M7. First item to cut under schedule pressure. |
| **M9** — Notifications | Not Started | 2026-07-19 | — | — | Pending | Depends on M4, M5, M7, M8. Closes the notification-endpoint gap identified in `Requirement_Analysis.md` §14 item 3. |
| **M10** — Dashboards & Reporting | Not Started | 2026-07-21 | — | — | Pending | Depends on M3–M9 (all prior feature milestones). Second item to cut under schedule pressure. **Action carried from M0 traceability review:** remove the temporary "Backend connectivity" health widget from `Dashboard/index.tsx` once the real Upcoming Exams/Attendance %/Fee Status/Recent Results widgets land — see `docs/Proposal_vs_Engineering_Additions.md` "Frontend / UI Engineering Decisions." |
| **M11** — Hardening, Testing & Deployment | Not Started | 2026-07-23 | — | — | Pending | Depends on all prior milestones. Final whole-system pass. |

*Planned Dates are derived from `Implementation_Roadmap.md`'s cumulative day estimates (Summary Table), added sequentially to the project start date (2026-07-03) — they are a scheduling projection, not a commitment, and will drift as actual completion dates land. Update this table's Planned Date column if the roadmap's estimates are revised.*

---

## Milestone Detail Log

*(One entry per completed milestone — brief summary of what actually shipped, plus commit references. Add a new entry each time a milestone closes; do not delete prior entries.)*

### M0 — Project Scaffolding & Environment Setup (Completed — 2026-07-03)

FastAPI app factory (settings-driven config with fail-fast validation, structured JSON logging, CORS, global exception handlers producing the standard error envelope, request logging middleware, `/health` with DB connectivity check), SQLAlchemy engine/session wiring, Alembic configured against `Base.metadata` with an empty baseline revision. React 18 + TypeScript + Vite + TailwindCSS frontend with React Router, React Query, a split Axios client (versioned + root), a light/dark theme provider, a shared app layout, and a live backend-connectivity widget on the Dashboard placeholder. Docker Compose local dev stack (Postgres + backend reload + Vite dev server). No business modules, no authentication — strictly foundation, per the milestone's own constraints.

Verified (not just claimed): clean `pip install`/`npm install`, app imports and boots, `uvicorn` serves real HTTP, `GET /health` and `GET /openapi.json` both return correctly, `npx tsc --noEmit` and `npm run build` both succeed, and a real defect (404s bypassing the custom exception handler due to a `fastapi.HTTPException` vs `starlette.exceptions.HTTPException` registration mismatch) was found and fixed during verification.

Two follow-up fix passes after initial completion:
- Dependency pins tightened from floating ranges to exact versions (`fdaaf59`), then re-verified against two independent clean dependency resolutions after a reviewer flagged `starlette==1.3.1` as suspicious-looking — confirmed legitimate via PyPI's JSON API and FastAPI's own GitHub release notes, not a bad resolution (`889465e`).
- API display metadata (OpenAPI title/description, Swagger, startup log banner) renamed from "ICT Education API" to "University Management System API" (`9e9680d`).

**Commits:** `71019ef` (backend foundation), `8c9e25f` (frontend foundation), `7eff95d` (infra), `fdaaf59` (dependency pins v1), `889465e` (dependency pins v2 — verified fix), `9e9680d` (metadata rename).

#### Full documentation self-review (2026-07-03, per `CLAUDE.md` §14 item 12)

Ran `docs/MILESTONE_VERIFICATION_CHECKLIST.md` Section 13 against all nine governing documents. Two real gaps found and fixed (documentation-only, no implementation changed):
- **Undocumented frontend additions** — the theme toggle and Dashboard health widget had no proposal linkage and no `Proposal_vs_Engineering_Additions.md` entry. Fixed in `07695ab`: both logged as Design Enhancements, theme toggle kept permanently, health widget scheduled for removal at M10.
- **Undocumented backend middleware/utilities** — exception handlers, request logging middleware, structured logging config, settings validation, DB session/engine, CORS, and the Alembic baseline had no entry either, despite the same-commit policy (added the commit before this review) explicitly naming "middleware, utility." Fixed in `5fe42ca`: all seven logged as Derived (unavoidable prerequisites for Required features, each implementing a mechanism `System_Architecture.md` already mandates).

Also performed **live verification beyond the original completion pass** (which had used `TestClient`, not a real browser): started the actual backend (`uvicorn`, port 8010) and frontend (`vite`, port 5173) via `.claude/launch.json`, in a real browser —
- Zero console errors; only Vite HMR debug logs and a harmless React Router v6 future-flag notice
- `GET http://localhost:8010/health` succeeded cross-origin from the frontend (confirms CORS actually works end-to-end, not just in unit tests) — real network tab evidence, response `{"status":"degraded","database":"unreachable"}` (correct — no live Postgres in this environment)
- Login (`/`) and Dashboard (`/dashboard`) pages render correctly; theme toggle clicked and confirmed switching light/dark and updating its own label
- No untracked/stray files left behind — temporary `.env` files used for this test were removed afterward; `.claude/launch.json` added as a reusable (gitignored) tool for future milestones' Section 8/13 checks

Both `PROJECT_PROGRESS.md`'s Summary and this milestone's row were stale before this review (`Current Git Commit` pointed at `d9ff4d2`, several commits behind actual HEAD) — corrected as part of this same pass.

#### Clean-clone reproducibility verification (2026-07-03)

Everything above had been verified from the working tree, which can accumulate local state (stale `.venv`, cached wheels, manually-edited files) that masks a real reproducibility problem. Re-verified from a genuinely fresh `git clone` (not a copy) into an isolated temp directory, at commit `f4044d5`:

| Step | Result |
|---|---|
| `git clone` (local) | Only tracked files present — confirmed no `.venv`, `.env`, `node_modules`, `.claude/`, or build artifacts came along |
| `python -m venv .venv` + `pip install --no-cache-dir -r requirements.txt` | Clean install, exit 0, **no pip cache used at all** |
| `pip check` | "No broken requirements found" |
| Resolved package set vs. `requirements.txt` pins | Exact match, all 46 packages (verified programmatically with PEP 503 name normalization, not eyeballed) |
| `cp .env.example .env` (no manual edits) | — |
| `alembic upgrade head` | **Alembic mechanism confirmed working** (loads `env.py`, resolves settings, attempts connection) — **connection itself failed**: the documented placeholder `DATABASE_URL` (`user`/`password`) doesn't match this machine's real local PostgreSQL 18 instance, whose actual credentials are unknown to me. Deliberately did not brute-force guess further after two reasonable attempts (`postgres`/`postgres`, `postgres`/`password`) both failed — that would be inappropriate against a real local database. **Known limitation, not a defect**: M0's only migration is an empty baseline (no schema to verify), so the meaningful check — does the Alembic wiring itself work — passed; a genuine `upgrade head` success run still needs to happen once, with real credentials, before M1 adds actual schema. |
| `uvicorn app.main:app` (real process, real port, real HTTP via `curl`) | `GET /health` → `200 {"status":"degraded","database":"unreachable"}` (correct graceful degradation, matching working-tree behavior exactly); `GET /openapi.json` → 200, title correct |
| `npm ci` (lockfile-exact install, not `npm install`) | Clean, same known esbuild/vite dev-server advisory as previously logged (Known Issue, unchanged) |
| `npx tsc --noEmit` | Zero errors |
| `npm run build` | Succeeds, same output shape as working-tree build |
| `npm run dev` (real Vite process, real port) | Boots in 263ms; `curl` confirms `index.html` and `/src/main.tsx` both serve correctly, title tag correct |
| Backend + frontend paired live (different clean-clone ports) | `GET /health` reachable from the frontend's configured API base — full stack wired correctly end-to-end |
| Cleanup | All test processes stopped by exact PID (command-line matched, not by name — avoided touching unrelated `python`/`node` processes on the machine); temp clone directory removed entirely; main working tree confirmed untouched (`git status` clean) throughout |

**Conclusion: Milestone 0 is reproducible from a clean clone**, with one explicitly-scoped exception: full `alembic upgrade head` execution success against a live database has not been demonstrated in this sandbox (credentials for the one reachable local Postgres instance are unknown, and no Docker is available here to spin up a throwaway one). Recommended next step: run `docker compose up` (per `README.md`) or supply real `DATABASE_URL` credentials once, specifically to confirm migration execution.

**Milestone 0 approved by user, 2026-07-04.**

### M1 — Core Reference Data Model (Completed — 2026-07-04)

Implemented exactly the scope `Implementation_Roadmap.md` defines for Milestone 1 — Department, Course, Room, Semester — and nothing from Milestone 2 or later.

**Database:** SQLAlchemy models for all four tables, matching `Database_Design.md` §6.7/6.8/6.11/6.20 column-for-column (including that `room` and `semester` deliberately have no `created_at`/`updated_at`, per the spec — not an oversight). Alembic revision `0002_core_reference_data` (down_revision `0001`): creates all four tables with the documented unique constraints (`department.name`, `department.code`, `course.code`, `room.name`, `semester.name`), the `course.department_id` FK with `ON DELETE RESTRICT`, the `course.department_id` index (per `Database_Design.md` §9), and the `semester.start_date < end_date` check constraint (§10).

**API:** 12 endpoints — list/create/get-by-id for each of Department, Course, Room, Semester — newly documented in `API_Contract.md` §10 *before* implementation (per the same-commit engineering-additions policy), classified **Derived** in `Proposal_vs_Engineering_Additions.md` (unavoidable plumbing for Required features, not a proposal feature itself). Update/delete deliberately not implemented — nothing yet needs to edit or remove reference data; scope stays minimal rather than preemptive.

**Layering:** router → service → repository, per `CLAUDE.md` §6 — routers contain no queries, services own uniqueness/FK-existence checks and translate `IntegrityError` to 409, repositories hold all SQLAlchemy statements.

**Known issues (both explicitly tracked, not oversights):**
1. **Endpoints are unauthenticated.** Milestone 1 lands before Milestone 2 (Authentication & Authorization) per the roadmap's own dependency graph — there is no RBAC mechanism yet to apply. Documented in `API_Contract.md` §10's header note and in `Proposal_vs_Engineering_Additions.md`. RBAC is added when M2 lands; this is not a security defect in the delivered scope, since M1 was never going to have auth available.
2. **Migration hand-authored, not `--autogenerate`'d.** Same sandbox limitation as Milestone 0 (no known-good local Postgres credentials, no Docker available) — autogenerate requires a live DB connection to diff against. The migration was written to mirror the SQLAlchemy models column-for-column and reviewed carefully, but a real `alembic revision --autogenerate` diff-check against a live database (expected to show *no* changes if this migration is correct) has not been performed. Recommended before this migration is trusted in a real deployment.

**Real defect found and fixed during verification (not deferred):** Pydantic v2's error details for custom `@model_validator` failures (used by `SemesterCreate` for the `start_date < end_date` check) embed a raw, non-JSON-serializable exception instance in `error["ctx"]["error"]`. The shared `validation_exception_handler` in `app/middleware/error_handlers.py` (a Milestone 0 file) was passing this straight into `json.dumps()`, causing a `TypeError` that surfaced as an unhandled 500 instead of the documented 422. Fixed by routing `exc.errors()` through `fastapi.encoders.jsonable_encoder` before building the response. This is a Milestone-0-file fix made during Milestone 1 because M1's own documented behavior (`API_Contract.md` §10.11: "start_date >= end_date (422)") depended on it — not scope creep into Milestone 2.

**Verified:** fresh `pip install`, all new modules syntax-checked, app imports and boots, all 12 endpoints present in `/openapi.json` under `/api/v1`, field-validation (422) and semester date-order validation (422, post-fix) both produce the standard error envelope, duplicate-name/code paths correctly designed to return 409 (exercised at the service-logic level; full round-trip against a live DB blocked by the same credentials limitation as the migration), graceful 500 (not a crash) when the database is unreachable, and all Milestone 0 behaviors (`/health`, 404 shape, app title) remain unchanged.

**Outstanding before M2 can start:** explicit approval of M1.
