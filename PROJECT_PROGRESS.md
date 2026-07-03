# University Management System — Project Progress

Single source of truth for milestone-level progress. Milestone numbering, names, and order are copied verbatim from `docs/Implementation_Roadmap.md` (the approved, frozen build order) — this file tracks *status against* that plan, it does not redefine it. For each milestone's Goal, Files, APIs, DB tables, Frontend pages, and Dependencies, see the roadmap directly. For per-requirement status (Testing/Implementation/Verification), see `docs/Requirement_Traceability_Matrix.md`.

**Last updated:** 2026-07-04 (Milestone 2 — Authentication & Authorization — completed)

---

## Summary

| Field | Value |
|---|---|
| **Overall Progress** | 25% (3 of 12 milestones completed) |
| **Current Milestone** | M2 — Authentication & Authorization *(complete, awaiting explicit approval — see Review Status below)* |
| **Last Completed Milestone** | M2 — Authentication & Authorization |
| **Next Milestone** | M3 — User Management & Profiles *(blocked on M2 approval, same wait-for-sign-off convention established after M0/M1)* |
| **Current Git Commit** | `494b60f` |

**Schedule risk (from `Implementation_Roadmap.md`):** full 12-milestone scope is ~20 working days solo against the July 13, 2026 deadline (10-day runway from project start). Planned Dates below are computed from the roadmap's own cumulative day estimates and show M6 onward landing **after** July 13 — this is the same risk the roadmap already flags, not a new finding. Committed core is M0–M7 + M11; M8 (Fees) and parts of M10 (advanced reporting) are the first items to cut if the timeline slips further.

---

## Milestone Tracker

| Milestone | Status | Planned Date | Completed Date | Git Commit Hash | Review Status | Notes |
|---|---|---|---|---|---|---|
| **M0** — Project Scaffolding & Environment Setup | Completed | 2026-07-03 | 2026-07-03 | `8cb72c1` | **Approved** | Backend app factory, DB/Alembic wiring, `/health`, frontend shell all verified working (see Milestone Detail Log). Dependency-pin defect found and fixed post-hoc (`fdaaf59` → `889465e`). Full 9-document self-review run (`5fe42ca`, `cfef1e8`) — found and fixed two gaps. Reproducibility verified from a genuinely fresh `git clone`. `HTTP_422_UNPROCESSABLE_ENTITY` deprecation warning fixed (`8cb72c1`). **Approved by user 2026-07-04.** |
| **M1** — Core Reference Data Model | Completed | 2026-07-04 | 2026-07-04 | `37f3ce4` | **Approved** | Department/Course/Room/Semester models, schemas, repository, service, router (12 endpoints, list/create/get-by-id per entity) implemented exactly per `Database_Design.md` §6.7/6.8/6.11/6.20 and the new `API_Contract.md` §10. Alembic revision `0002_core_reference_data`. **Post-completion fix:** user-reported real-machine failure — `cd backend && alembic upgrade head` raised `ModuleNotFoundError: No module named 'app'` because verification had only ever used `python -m alembic`, not the bare console script. Fixed via `prepend_sys_path` + a `__file__`-based fallback in `env.py`; reproduced-then-fixed-then-reverified from a fresh clone. `MILESTONE_VERIFICATION_CHECKLIST.md` updated so this can't recur. Known issues from M1 (endpoints unauthenticated; migration not autogenerate-diff-checked) both addressed/closed in M2 — see M2 row and Milestone Detail Log. **Approved by user 2026-07-04.** |
| **M2** — Authentication & Authorization | Completed | 2026-07-05 | 2026-07-04 | `494b60f` | Pending | JWT access/refresh auth (login/refresh/logout/change-password), bcrypt password hashing, `require_roles` RBAC dependency retrofitted onto all 12 M1 reference-data endpoints, and the full frontend auth module (token storage, interceptors, AuthContext, RouteGuard, Login page). Alembic revision `0003_user`. 41 backend tests added (previously zero existed project-wide) covering BR-006, VR-002, refresh-token rotation/reuse, and RBAC negative cases — see Milestone Detail Log. Full `MILESTONE_VERIFICATION_CHECKLIST.md` self-review run; no unresolved findings. |
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

#### Post-completion fix: `alembic upgrade head` failed on a real machine (2026-07-04)

User-reported, reproduced, and fixed. `cd backend && alembic upgrade head` (the bare console-script entry point — how a real developer actually runs it) failed with `ModuleNotFoundError: No module named 'app'` from `backend/alembic/env.py`. Root cause: my own verification throughout Milestone 0 and Milestone 1 only ever invoked Alembic via `python -m alembic` (which implicitly adds the current working directory to `sys.path`) or through direct Python imports (`from app.main import app`) — never the plain `alembic` command, which does **not** add cwd to `sys.path`. This is a genuine gap in the verification methodology itself, not just the code.

**Fix:** `prepend_sys_path = .` added to `alembic.ini` (the standard Alembic mechanism for exactly this problem — interpreted relative to the ini file's own location, correct regardless of invocation cwd), plus a `__file__`-based `sys.path` insertion directly in `env.py` as a self-contained fallback.

**Verified properly, not just patched:** reproduced the exact failure first (fresh `git clone`, fresh venv, bare `alembic` console script — confirmed identical error/traceback to the report), applied the fix, confirmed `alembic upgrade head` now proceeds past the import and reaches a real database connection attempt (fails only on placeholder credentials, the same pre-existing documented limitation, not a new bug), confirmed `alembic history`/`alembic current` work, and confirmed `python -m alembic` still works with no regression.

**Process fix, not just a code fix:** `docs/MILESTONE_VERIFICATION_CHECKLIST.md` §4 updated to require testing the bare console-script form specifically — testing only `python -m alembic` is no longer sufficient evidence for future milestones.

**No application architecture changed** — fix is scoped entirely to `alembic.ini` and `alembic/env.py` import/path resolution.

**Verified:** fresh `pip install`, all new modules syntax-checked, app imports and boots, all 12 endpoints present in `/openapi.json` under `/api/v1`, field-validation (422) and semester date-order validation (422, post-fix) both produce the standard error envelope, duplicate-name/code paths correctly designed to return 409 (exercised at the service-logic level; full round-trip against a live DB blocked by the same credentials limitation as the migration), graceful 500 (not a crash) when the database is unreachable, and all Milestone 0 behaviors (`/health`, 404 shape, app title) remain unchanged.

**Outstanding before M2 can start:** explicit approval of M1. **Approved by user 2026-07-04.**

### M2 — Authentication & Authorization (Completed — 2026-07-04)

Implemented exactly the scope `Implementation_Roadmap.md` defines for Milestone 2: JWT-based login/refresh/logout/change-password, RBAC middleware, and its retrofit onto Milestone 1's endpoints. Nothing from Milestone 3 (account creation, user profiles) was implemented — `UserRepository` deliberately has no `create()` method.

**Design gap resolved first (docs-only, `414bc30`):** `Database_Design.md`'s `user` table had no mechanism to support refresh-token rotation/revocation. Presented the tradeoff to the user via `AskUserQuestion` (a dedicated session table vs. two columns on `user`); user chose the two-column approach. `current_refresh_token_jti`/`refresh_token_expires_at` added to `Database_Design.md` §6.1 with an explicit design note: this is a single-active-session-per-user model — logging in on a second device invalidates the first session's refresh token. `API_Contract.md` updated to reference the resolved design.

**Database:** `user` table (`id`, `email` unique, `password_hash`, `role` enum, `is_active`, the two refresh-tracking columns, `created_at`/`updated_at`) matching `Database_Design.md` §6.1 exactly. Alembic revision `0003_user` (down_revision `0002`).

**Backend:** `app/core/security.py` (bcrypt hashing, JWT encode/decode), `app/repositories/user_repository.py`, `app/services/auth_service.py` (BR-006 deactivation check on both login and refresh; refresh-token rotation with jti-mismatch reuse detection; VR-002 change-password check), `app/middleware/auth.py` (`get_current_user`, re-checks `is_active` on every request per `CLAUDE.md` §12) and `app/middleware/rbac.py` (`require_roles`), `app/routers/auth.py` (4 endpoints under `/api/v1/auth`). RBAC retrofitted onto all 12 M1 reference-data endpoints (GET: any authenticated role; POST: Admin), closing M1's tracked known issue.

**Frontend:** `frontend/src/auth/` (tokenStorage, AuthContext, RouteGuard), Axios request/response interceptors in `lib/apiClient.ts` (Bearer attachment, silent refresh-and-retry on 401), a real Login page, logout action + user email display in `AppLayout`. localStorage chosen for token persistence over httpOnly cookies — documented tradeoff (the API returns tokens in the JSON body, not `Set-Cookie`; an httpOnly-cookie approach would need a backend-for-frontend layer this project doesn't have).

**Real defects found and fixed during verification (not deferred):**
1. `passlib==1.7.4` (unmaintained, final release) crashes against `bcrypt>=4.1` — probes a removed `bcrypt.__about__.__version__` attribute. Replaced with direct `bcrypt.hashpw`/`checkpw` calls (`ce6a5af`).
2. Alembic migration `0003_user`: redundant explicit `user_role.create()` in `upgrade()` conflicted with `op.create_table()`'s automatic enum creation (`DuplicateObject`); and `op.drop_table()` was confirmed to *not* drop the enum type on its own, so the explicit `.drop()` in `downgrade()` is required and was kept. Found via the first genuine `alembic upgrade`/`downgrade`/`upgrade` cycle run against a real, disposable PostgreSQL database in this project's history (`8bbc009`).
3. Frontend: the response interceptor's silent-refresh logic was hijacking `/auth/login`'s own 401 (wrong password) — no refresh token exists yet, so the doomed refresh attempt force-navigated to `/login`, wiping the login form's error state before the user ever saw it. Fixed by excluding `/auth/login`/`/auth/refresh` from the refresh-and-retry flow (`42aaac6`).
4. `backend/tests/` had zero test files project-wide (`pytest` reported "no tests ran") despite `CLAUDE.md` §10's requirement that every BR-xxx/VR-xxx rule have a test — caught during this milestone's own self-review, not by the user. Added 41 tests: unit tests for `core/security.py` and `AuthService` (repository stubbed, no DB dependency, always run), plus integration tests for the auth router and the RBAC retrofit (full request→DB→response against a disposable Postgres database, gated on `TEST_DATABASE_URL`, skipped rather than failing when unavailable) (`494b60f`).

**Verified (not just claimed):** `pytest` — 41 passed (23 unit + 18 integration) against a disposable `ict_education_m2_test` database, created and dropped solely for this run. `npx tsc --noEmit` and `npm run build` both clean. `pip check` — no broken requirements. `alembic upgrade head` / `downgrade -1` / `upgrade head` all clean via the bare `alembic` console-script entry point (the specific historical failure mode from M1) against a fresh disposable database. Full live-browser verification of the frontend auth flow (wrong-password error banner, successful login + redirect + user display, logout, direct-navigation route guarding while unauthenticated) via the preview browser tools against a real backend + real Postgres, using `.claude/launch.json`'s `env` field so no `.env` file was ever touched. All disposable test/verification databases (`ict_education_m2_verify`, `ict_education_m2_test`, `ict_education_m2_migration_check`) dropped after use; the developer's real `university_management_db` was never touched.

**Known issues (tracked, not oversights):**
1. ~~Migration `0003_user` not autogenerate-diff-checked.~~ **Resolved in the M2 review follow-up below** — `alembic revision --autogenerate` now confirmed to produce an empty migration.
2. FR-005 (redirect to role-specific dashboard) currently redirects every role to the same generic `/dashboard` — role-specific dashboard *content* is out of scope until the role-owning domains (M3+) exist. Login/redirect mechanism itself is complete and tested.
3. Single-active-session-per-user is a deliberate scope decision (see design-gap resolution above), not a defect — logging in on a second device invalidates the first device's refresh token (the first device's access token remains valid until it naturally expires, then its silent-refresh attempt will fail and redirect to `/login`).

**Commits (`37f3ce4`..`494b60f`):** `414bc30` (design gap resolution, docs-only), `1ed5a68` (User model + migration), `ce6a5af` (security utilities), `affe337` (auth schemas), `8bbc009` (migration bug fix), `99b13df` (user repository + auth service), `c600ff3` (auth + RBAC middleware), `c95c6e9` (auth router), `23f7bff` (RBAC retrofit on M1 endpoints), `42aaac6` (frontend auth module), `494b60f` (backend test suite).

#### M2 review follow-up (2026-07-05)

Before final approval, the user ran an independent verification pass (see prior conversation turn) and asked for four fixes, none of which touch business logic, auth flow, JWT handling, API endpoints, tests, or milestone scope:

1. **`user.is_active` ORM/migration default asymmetry.** The migration declared `server_default=sa.true()`; the model declared only the Python-side `default=True`, with no `server_default`. Alembic doesn't compare `server_default` by default, so this never surfaced as an autogenerate diff — but it was a real, undocumented inconsistency between the two representations of the same column. **Resolved by making the model match the migration**: added `server_default=true()` to `User.is_active` alongside the existing `default=True` (both are useful — `default` gives an ORM-constructed object a value before it's ever flushed; `server_default` is what a raw `INSERT` outside the ORM relies on). No migration change needed — the DDL was already correct; only the model was updated to represent it accurately.
2. **Index representation gap.** `alembic revision --autogenerate` logged `Detected removed index` for `ix_course_department_id` and `ix_user_role` — both exist in the database (created via explicit `op.create_index()` in the hand-written migrations) but weren't declared on the corresponding model columns via `index=True`, so the ORM metadata didn't actually represent the live schema. **Resolved by adding `index=True`** to `Course.department_id` and `User.role` (both already required by `Database_Design.md` §9, which lists both indexes — the model was simply incomplete, not the design). No migration change — the indexes already existed correctly; the migrations gained a one-line comment cross-referencing the model for future readers. Re-verified with a fresh `alembic revision --autogenerate` run: generated migration body is now empty (`pass`/`pass`), with no "detected" log lines at all. Temporary diff-check migration file deleted; disposable database dropped.
3. **Ownership-check wording ambiguity.** `Implementation_Roadmap.md`'s Milestone 2 Goal/file-list describes `rbac.py` as a "role + ownership check dependency," but M2 has no `/me`-scoped or parent-linked endpoints to check ownership against — those first appear in Milestone 3. `rbac.py` has always correctly implemented role-only checks (ownership belongs in the service layer per `CLAUDE.md` §6), but this wasn't explicitly reconciled against the roadmap's own wording anywhere. **Resolved by adding a Milestone 2 scope note directly to `Implementation_Roadmap.md`** clarifying that the "ownership-check" phrase describes the milestone's eventual purpose in the dependency chain, not something M2 itself delivers, and that ownership checks land at the service layer of whichever future milestone first introduces an ownership-scoped resource. No code changed — `rbac.py`'s existing behavior was already correct.
4. **`CHANGELOG.md` missing documentation-only M2 changes.** See `CHANGELOG.md`'s `[Unreleased]` section, "Changed (Milestone 2 — Documentation)" — now lists every `Database_Design.md`, `API_Contract.md`, `Proposal_vs_Engineering_Additions.md`, `Requirement_Traceability_Matrix.md`, and `Implementation_Roadmap.md` change made during M2, not just the code changes.

**Re-verification after these fixes:** `alembic upgrade head` clean from a fresh disposable database; `alembic revision --autogenerate` produces an empty migration (confirmed no diff, including for the two previously-unrepresented indexes); temporary diff-check migration file and disposable database both removed. No business logic, auth flow, JWT implementation, API endpoint, or test file was touched.

**Full documentation self-review run** (`CLAUDE.md` §14 item 12, `MILESTONE_VERIFICATION_CHECKLIST.md`): `Database_Design.md` and `API_Contract.md` updated in the same change as the design-gap resolution (not backfilled). `Requirement_Traceability_Matrix.md` FR-001–FR-005 and NFR-001/NFR-004 updated to Verified. `Proposal_vs_Engineering_Additions.md`'s M2 schema addition and reference-data auth-note entries confirmed present and accurate. No undocumented additions found. One real gap found and fixed by this review itself: the missing test suite (see Real Defects #4, above) — fixed in the same pass, before this milestone was marked Completed, per the checklist's own instruction not to mark Completed with a known, unfixed finding.

**Outstanding before M3 can start:** explicit approval of M2.
