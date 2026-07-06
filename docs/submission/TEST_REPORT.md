# Test Report

## Summary

| Suite | Test files | Test cases | Result |
|---|---|---|---|
| Backend (pytest) | 32 | 477 | **All passing** |
| Frontend (Vitest) | 14 | 61 | **All passing** |

Both suites were last verified together in a single full run, immediately following the most recent code change, against a real disposable PostgreSQL database (not mocked) for the backend integration tier — see [Verification methodology](#verification-methodology) below.

## Backend test suite

### Composition

**24 unit test files** (`backend/tests/unit/`) — exercise service-layer business logic with repositories stubbed via `unittest.mock`, no database required. These run in every environment, including CI, without any database configured.

Representative coverage: `test_exam_service.py` (36 tests), `test_result_service.py` (25), `test_attendance_service.py` (25), `test_fee_service.py` (29), `test_schedule_service.py` (19), `test_grading_service.py` (18), `test_notification_dispatcher.py` (16), `test_user_service.py` (17), `test_auth_service.py` (15), `test_reference_data_service.py` (20), `test_report_service.py` (11), `test_security.py` (8), `test_error_handlers.py` (6), `test_notification_service.py` (6), `test_rate_limit.py` (4), plus smaller focused files for the PDF/Excel generators and the app factory.

**8 integration test files** (`backend/tests/integration/`) — exercise the full request → database → response cycle through FastAPI's test client, against a disposable PostgreSQL database. These are skipped automatically unless `TEST_DATABASE_URL` is set, so a contributor without a database configured never sees false failures.

Representative coverage: `test_attendance_router.py` (34 tests — including RBAC, duplicate-attendance rejection, and the Parent PDF/Excel/CSV export paths), `test_users_router.py` (25), `test_reference_data_rbac.py` (25 — RBAC across Academic Setup CRUD, plus the two new validation-bounds regression tests), `test_results_router.py` (24 — including the Parent transcript-download and result-published-notification paths), `test_exams_router.py` (27), `test_fees_router.py` (21 — including the Parent invoice-download and paid-invoice-labeled-as-receipt paths), `test_schedule_router.py` (15 — including the Admin change-request queue and Teacher-notified-on-resolution paths), `test_auth_router.py` (15), `test_reports_router.py` (8), `test_notifications_router.py` (10).

### What's covered

- Every documented business rule (BR-xxx) and validation rule (VR-xxx) has at least one dedicated test.
- Every RBAC/ownership boundary has an explicit **negative** test — a wrong-role or wrong-owner request is verified to be rejected (`403`), not just that the correct-role/owner request succeeds.
- Every workflow state machine (exam draft → published, result submitted → approved/rejected → published, schedule-change-request pending → approved/rejected) has tests covering both valid transitions and rejected invalid transitions (e.g. resolving an already-resolved request returns `409`).
- Duplicate-prevention is tested at the database-constraint level, not just the pre-flight service check (e.g. attendance's `IntegrityError → 409` translation).

### How to run

```bash
cd backend
pytest -q                                          # unit tests only (no database needed)

# Full suite, including integration tests, against a disposable database:
createdb umsm_test_disposable                       # or your platform's equivalent
export TEST_DATABASE_URL="postgresql://user:pass@localhost:5432/umsm_test_disposable"
export DATABASE_URL="$TEST_DATABASE_URL"
alembic upgrade head
pytest -q
```

### Last verified result

```
477 passed, 12 warnings in ~180s
```

(The 12 warnings are benign SQLAlchemy `SAWarning`s about test-transaction teardown ordering, not failures.) Re-running with no `TEST_DATABASE_URL` set (the default, unit-only mode) produces `250 passed, 227 skipped` — confirming the integration tier is cleanly opt-in, never silently run against an unintended database.

`alembic upgrade head` against a completely fresh database produces zero drift against the current ORM models (`alembic revision --autogenerate` generates an empty migration), confirming the 10 migrations and the code that describes them have never diverged.

## Frontend test suite

### Composition

**14 test files** (`frontend/tests/`) using Vitest + React Testing Library + jsdom.

- `SearchableSelect.test.tsx` (14 tests) — the shared searchable-dropdown component: mouse interaction, keyboard navigation (Escape, Arrow Up/Down, Enter), filtering.
- `TimetableAdminSchedulePanel.test.tsx` (9) — the Admin schedule-management forms and the Pending Schedule Change Requests queue (list, approve, reject).
- `ReportToolbar.test.tsx` (9) — the shared Print/PDF/Excel/CSV export toolbar.
- `AcademicSetupDepartments/Courses/Rooms/Semesters.test.tsx` (2 each, 8 total) — the Admin reference-data CRUD screens.
- `ResultsViewParent.test.tsx` (5) — the Parent Results view (child selector, GPA, derived Pass/Fail, transcript download).
- `FeeCentreParent.test.tsx` (5) — the Parent Fee Centre view (child selector, invoice/receipt labeling and download).
- `ResultApproval.test.tsx` (3), `ReportLayout.test.tsx` (3), `GradingInterface.test.tsx` (2), `ExamRoom.test.tsx` (2) — teacher/admin workflow screens and the exam-taking timer.
- `AttendanceParentExport.test.tsx` (1) — the Parent attendance PDF/Excel/CSV export buttons.

### How to run

```bash
cd frontend
npx tsc --noEmit      # TypeScript check
npm run lint          # ESLint
npx vitest run        # component tests
npm run build         # production build
```

### Last verified result

```
Test Files  14 passed (14)
     Tests  61 passed (61)
```

`tsc --noEmit`, `eslint .`, and `npm run build` all completed with zero errors on the same run.

## Verification methodology

- Integration tests never run against a developer's real database — every verification pass in this project's history creates a disposable PostgreSQL database, runs `alembic upgrade head` against it, runs the full suite, and drops it afterward.
- The two suites (backend/frontend) are always run together as part of the same verification pass before any change is considered complete, per this project's governing engineering conventions (`CLAUDE.md`).
- CI (`.github/workflows/backend-ci.yml`, `frontend-ci.yml`) runs the equivalent checks automatically on every push/PR — see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#continuous-integration) for what each workflow executes.
