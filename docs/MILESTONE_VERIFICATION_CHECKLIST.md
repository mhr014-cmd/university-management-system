# Milestone Verification Checklist
## University Management System (ICT Education)

**Purpose:** Run this checklist after every milestone in `docs/Implementation_Roadmap.md`, before updating `PROJECT_PROGRESS.md`'s Status to "Completed" or moving on to the next milestone. It exists to catch exactly the class of problem already found once in this project — a working-looking app that has a silent defect (the 404 exception-handler mismatch in Milestone 0) or a non-reproducible environment (the floating dependency ranges caught in the Milestone 0 review) — before it compounds into the next milestone.

**How to use this document:** Copy the checklist below into the milestone's PR description or into `PROJECT_PROGRESS.md`'s Notes column, check off each item with real evidence (command output, screenshot, log excerpt), and record any unchecked item under "Known Issues" rather than silently skipping it. An item marked "N/A" must say why.

---

## 1. Build Verification

- [ ] Backend: fresh `pip install -r backend/requirements.txt` into a **clean** virtual environment succeeds with no errors
- [ ] Backend: `pip check` reports no broken requirements
- [ ] Frontend: fresh `npm install` in `frontend/` succeeds with no `npm ERR!` output
- [ ] Frontend: `npx tsc --noEmit` passes with zero type errors
- [ ] Frontend: `npm run build` completes and produces `frontend/dist/`
- [ ] No new dependency was added without updating `backend/requirements.txt` / `frontend/package.json` accordingly (per `CLAUDE.md` §14.8 — no undeclared dependencies)
- [ ] `npm audit` / dependency vulnerability output reviewed; any new high/critical findings are either fixed or explicitly logged under Known Issues with justification

---

## 2. Backend Startup

- [ ] `uvicorn app.main:app` boots with no unhandled exceptions in the startup log
- [ ] Structured startup log line appears and names the correct app title/environment (see `app/main.py` lifespan logging)
- [ ] App fails **fast and loudly** if a required environment variable is missing (re-test by temporarily unsetting `DATABASE_URL` or `JWT_SECRET_KEY` and confirming a clear Pydantic validation error, not a silent default or a confusing downstream crash)
- [ ] No deprecation warnings introduced by this milestone's code went unreviewed (existing ones already logged under Known Issues are fine to carry forward, not re-litigate)
- [ ] Server shuts down cleanly (Ctrl+C / SIGTERM) without hanging or throwing on teardown

---

## 3. Frontend Startup

- [ ] `npm run dev` boots the Vite dev server with no console errors on initial load
- [ ] App loads at `http://localhost:5173` without a blank page or unhandled render error
- [ ] Routing works: navigating to each route added/changed this milestone renders the correct page, and an unmatched route renders the 404 page (not a blank screen or router crash)
- [ ] No hydration/console warnings about missing `key` props, invalid nesting, or React strict-mode double-invoke side effects introduced this milestone
- [ ] Environment variables (`VITE_API_BASE_URL`, `VITE_API_ROOT_URL`, and any added this milestone) are read from `.env`, not hardcoded

---

## 4. Database Migration

- [ ] A new Alembic revision was generated for every schema change this milestone (per `CLAUDE.md` §6 — never hand-edited after generation, never applied as manual DDL)
- [ ] `alembic upgrade head` runs cleanly against a fresh database
- [ ] `alembic downgrade -1` (or to the previous milestone's head) runs cleanly and doesn't leave orphaned objects — test this explicitly, not just the upgrade path
- [ ] New tables/columns match `docs/Database_Design.md` exactly (names, types, nullability, constraints) — no ad hoc columns, no relaxed constraints for convenience
- [ ] Every index listed for the new tables in `Database_Design.md` §9 is present
- [ ] Foreign key `ON DELETE` behavior (RESTRICT vs CASCADE) matches `Database_Design.md` §10
- [ ] Seed data (if this milestone adds any, per `Database_Design.md` §11) loads without error and matches the "clean demo" vs. "test/deliberate-conflict" separation called for in that section

---

## 5. API Testing

- [ ] Every endpoint this milestone adds/changes matches `docs/API_Contract.md` exactly: HTTP method, URL, request body shape, response body shape, status codes
- [ ] Every endpoint's **Access** roles from `API_Contract.md` are enforced — tested with at least one correct-role request (succeeds) and one wrong-role request (403) per endpoint
- [ ] Every `/me`-scoped or parent-linked endpoint has an explicit **ownership** test (not just role) — e.g., Student A cannot fetch Student B's data even with a valid Student-role token (per `CLAUDE.md` §6, `System_Architecture.md` §6)
- [ ] Every Business Rule (BR-xxx) and Validation Rule (VR-xxx) touched by this milestone has at least one passing test and one rejected-case test (per `CLAUDE.md` §10)
- [ ] Every workflow state transition added this milestone (e.g., draft→published, submitted→approved) has both a valid-transition test and an invalid-transition-rejected test
- [ ] Error responses match the standard envelope from `System_Architecture.md` §9 (`{"error": {"code", "message", "details"}}`) for 401/403/404/409/422 cases — not a framework default shape
- [ ] Pagination/filtering works on any list endpoint added this milestone (per `CLAUDE.md` §11 — no unbounded result sets)

---

## 6. Swagger Verification

- [ ] `/docs` (Swagger UI) loads without error and lists every endpoint added/changed this milestone
- [ ] Every new endpoint has a non-empty summary/description — not FastAPI's auto-generated default
- [ ] Request/response schemas shown in Swagger match the Pydantic schemas actually used (no stale cached schema, no `Any`/untyped fields per `CLAUDE.md` §3)
- [ ] "Try it out" successfully executes at least the happy-path case for each new endpoint against a running backend
- [ ] `/openapi.json` is valid JSON and `info.title`/`info.version` are correct
- [ ] No endpoint is accidentally exposed that should be internal-only, and no endpoint documented in `API_Contract.md` is missing from Swagger

---

## 7. Error Logs

- [ ] Backend log output for this milestone's manual/automated test run reviewed line by line — no unexpected `ERROR`/stack traces during otherwise-successful requests
- [ ] Every intentionally-triggered error case (403, 404, 409, 422) logs at the correct severity per `System_Architecture.md` §10 (`4xx` lower severity, `5xx` always with full stack trace server-side)
- [ ] No sensitive data appears in logs — passwords, raw JWTs, full payment details (per `CLAUDE.md` §12/§13) — grep the log output for these explicitly, don't just eyeball it
- [ ] Audit-worthy actions added this milestone (result approval, payment recording, account creation/deactivation, schedule changes — per `System_Architecture.md` §10) produce a discrete, reviewable log entry
- [ ] No new unhandled `Exception` reaches the generic 500 handler during normal operation of this milestone's features (if one does, it's a bug to fix before sign-off, not to log around)

---

## 8. Browser Console

- [ ] Zero uncaught errors in the browser console while exercising every page/feature added this milestone
- [ ] Zero React warnings (missing keys, prop-type mismatches, "Cannot update state on unmounted component," etc.)
- [ ] No failed network requests in the browser Network tab that the UI silently swallows (every failed request should surface a visible error state, per `UI_Wireframes.md` "Cross-Page Conventions")
- [ ] No leftover `console.log`/debug output committed in frontend source for this milestone
- [ ] CORS works correctly end-to-end (frontend origin can call the backend without a CORS error) when both are run via the documented `README.md` setup steps

---

## 9. Unit Tests

- [ ] `pytest` (backend) passes with zero failures and zero unexpected skips
- [ ] Every service-layer function added/changed this milestone that implements a BR-xxx/VR-xxx rule has a corresponding unit test, with repositories mocked/stubbed (per `CLAUDE.md` §10)
- [ ] Router-level integration tests exist for every endpoint added this milestone (full request → DB → response cycle against a test database, not the dev database)
- [ ] Frontend component tests (where this milestone adds interaction logic — forms, timers, approval workflows) pass
- [ ] Test coverage for this milestone's new code reviewed — gaps are either filled or explicitly logged under Known Issues, not silently left untested
- [ ] No test was skipped/commented-out to make the suite pass (per `CLAUDE.md` §3 — no dead code paths)

---

## 10. Manual Testing

- [ ] Every user-facing flow this milestone adds was walked through by hand in a real browser against a real running backend + database — not just verified via automated tests
- [ ] Tested as each role the feature applies to (Student/Teacher/Admin/Parent), not only the "primary" role, including a deliberate wrong-role attempt to confirm it's rejected in the UI, not just the API
- [ ] Tested at least one deliberate invalid input per new form (empty required field, out-of-range value, malformed data) and confirmed the validation message shown matches `UI_Wireframes.md`'s Validation section for that page
- [ ] Responsive behavior spot-checked at mobile and desktop breakpoints per the relevant page's `UI_Wireframes.md` Responsive Behaviour section
- [ ] Loading and empty states (not just the happy-path populated state) were actually seen, not assumed — e.g., a fresh account with no data, a slow network throttled in devtools

---

## 11. Git Status

- [ ] `git status` is clean — no untracked files that should have been committed, no accidentally-staged build artifacts (`node_modules/`, `dist/`, `.venv/`, `__pycache__/`)
- [ ] Commits for this milestone are logically separated (per `CLAUDE.md` §8 — not one giant commit), with imperative present-tense messages referencing the milestone/requirement ID where useful
- [ ] No secrets, `.env` files, or credentials were committed — diff the milestone's commits explicitly for this, don't just trust `.gitignore`
- [ ] No schema migration was mixed into the same commit as unrelated feature code (per `CLAUDE.md` §8)
- [ ] Branch is up to date with the target integration branch (no unresolved merge conflicts, no stale rebase state)
- [ ] `PROJECT_PROGRESS.md`'s Git Commit Hash column for this milestone is updated to the actual final commit, not left stale

---

## 12. Documentation Updated

- [ ] `PROJECT_PROGRESS.md`: this milestone's row updated (Status, Completed Date, Git Commit Hash, Review Status, Notes) — Review Status stays "Pending" until the person approving actually signs off, per the convention established after Milestone 0
- [ ] `CHANGELOG.md`: this milestone's real Added/Fixed/Changed entries recorded — genuine changes only, not placeholder text
- [ ] `docs/Requirement_Traceability_Matrix.md`: every FR/NFR touched by this milestone has its Testing Status / Implementation Status / Verification Status columns updated in place (rows are never deleted or renumbered, per that document's own instructions)
- [ ] If implementation revealed a design doc was wrong or incomplete, the relevant `docs/` file was corrected **in the same change** — not patched around in code only (per `CLAUDE.md` §9)
- [ ] Any newly-resolved ambiguity from `Requirement_Analysis.md` §14 is reflected back into that section (marked resolved, decision noted) rather than left stale
- [ ] `docs/API_Contract.md` still matches the implemented API exactly — if a genuine defect forced a contract change, the contract was updated and the deviation is explained, not left silently out of sync (per the top-level instruction: don't change API contracts unless implementation reveals a genuine defect)
- [ ] `README.md` "Getting Started" instructions still work as written, re-tested from a clean checkout if this milestone changed setup steps

---

## Sign-off

A milestone is not "Completed" in `PROJECT_PROGRESS.md` until every section above is either checked or has an explicit, justified "N/A"/Known Issue entry. Completion (all boxes checked) and Approval (explicit reviewer sign-off) are tracked as two separate fields in `PROJECT_PROGRESS.md` — finishing this checklist moves Status to "Completed," it does not by itself move Review Status to "Approved."

| Field | Value |
|---|---|
| Milestone | |
| Checklist run by | |
| Date | |
| Git commit verified against | |
| Known Issues (if any) | |
| Result | Pass / Pass with Known Issues / Fail |
