# Proposal vs. Engineering Additions
## University Management System (ICT Education) — REST API

**Source inputs:** `docs/product_proposal.pdf` §3–§7, `docs/API_Contract.md`, `docs/UI_Wireframes.md`, `docs/Requirement_Analysis.md` §14
**Purpose:** A single, explicit ledger of every endpoint, frontend addition, and backend middleware/utility that does **not** appear in the proposal itself, so implementation starts with — and stays on — a clear line between what the client (ICT Bangladesh) asked for and what this project added to make that request buildable or verifiable. Extended beyond API endpoints on 2026-07-03 after a traceability review found two undocumented frontend additions (see "Frontend / UI Engineering Decisions") and, on immediate self-review against the newly-added same-commit policy, a full category of unlogged backend middleware/utilities (see "Backend Middleware & Utilities").
**Scope:** No endpoints or UI elements are removed by this document — it is a review and classification layer only.

---

## Classification Definitions

| Classification | Meaning |
|---|---|
| **Required** | The underlying capability is **explicitly described in the proposal's narrative** (§3 Student features, §4 Teacher features, §5 Admin & Parent features, or §7 Web application screens) — the proposal simply omitted the corresponding row from its own §6 endpoint table. The capability is not optional; only its enumeration as a REST endpoint was missing. |
| **Derived** | The endpoint is not itself named anywhere in the proposal, but is a **logically unavoidable mechanical consequence** of building a Required feature — the system cannot function without it, even though no proposal sentence asked for it directly. |
| **Design Enhancement** | A specific implementation choice (response shape, parameter design, splitting one capability into two endpoints, bulk-operation support, etc.) layered **on top of** a Required or Derived capability. The *existence* of the underlying capability is not a Design Enhancement — only the *shape* of the solution is. |

Every endpoint below is **Required** at the capability level (all seven trace to a sentence the proposal actually contains). Where a specific design choice within that endpoint goes beyond what the proposal states, it is called out separately as a Design Enhancement so the two are never conflated.

---

## 1. `POST /schedule/change-requests`

**Why it was added:** The proposal's Teacher feature list describes a request-and-confirm workflow for schedule changes, but §6 (API Specification) lists no endpoint through which a Teacher submits such a request.

**Proposal requirement supported (quoted):**
> §4, Teacher features: "Schedule management — Teacher — View and request changes to their timetable. Changes go to admin for confirmation."

**Classification: Required.** The capability — a Teacher submitting a change request — is explicitly named in the proposal's own prose (§4). Only the REST endpoint enumeration was missing from §6.

**Design Enhancement within this endpoint:** The request payload's `requested_change` object (day/time/room fields) and its `pending` status value are an engineering interpretation of "request changes" — the proposal does not specify the request's data shape.

---

## 2. `POST /schedule/change-requests/{id}/resolve`

**Why it was added:** The same proposal sentence that requires endpoint #1 also requires an Admin-side confirmation step, which likewise has no corresponding row in §6.

**Proposal requirement supported (quoted):**
> §4, Teacher features: "...Changes go to admin for confirmation." (same sentence as above — the second half describes this endpoint's function)

**Classification: Required.** "Changes go to admin for confirmation" directly names the Admin confirmation action this endpoint performs; the proposal describes the behavior, not the endpoint.

**Design Enhancement within this endpoint:** Splitting the workflow into two endpoints (submit, then resolve) rather than one combined endpoint is an engineering design choice — a single endpoint with a state parameter could have served the same proposal-stated behavior. The two-endpoint split was chosen for clean separation of the Teacher-facing and Admin-facing actions, matching the pattern already used for Result approval (`POST /results/{examId}/submit` + `POST /results/{id}/approve`) for internal consistency.

---

## 3. `GET /notifications`

**Why it was added:** The proposal requires a Notifications panel showing a feed with read/unread state, but §6 lists no endpoint to fetch that feed.

**Proposal requirement supported (quoted):**
> §3, Student features: "Notifications — Student — Receive real-time alerts for result publishing, schedule changes, attendance warnings, and fee due dates."
> §7, Web application screens: "Notifications panel — system-wide notification feed with read/unread state."

**Classification: Required.** Both the feature (§3) and the screen (§7) are explicitly named in the proposal. A feed cannot be displayed without an endpoint to retrieve it — the capability is proposal-mandated, only the retrieval mechanism was left unspecified.

**Design Enhancement within this endpoint:** The `unread_count` field in the response and the `is_read` query-param filter are engineering additions for UI convenience — the proposal never describes a count badge, only "read/unread state."

---

## 4. `PUT /notifications/{id}/read`

**Why it was added:** The same §7 sentence that requires endpoint #3 ("read/unread state") also requires a mechanism to transition a notification from unread to read, which has no corresponding row in §6.

**Proposal requirement supported (quoted):**
> §7, Web application screens: "Notifications panel — system-wide notification feed with **read/unread state**."

**Classification: Required.** "Read/unread state" is meaningless without a way to change it — the mutation capability is a direct, explicit reading of the proposal's own screen description.

**Design Enhancement within this endpoint:** The idempotent "already read → 200 OK" behavior (rather than an error) is an engineering choice for a smoother client experience; the proposal is silent on this edge case.

---

## 5. `POST /fees/overdue/notify`

**Why it was added:** The proposal's Admin fee-management feature explicitly states Admin can send overdue notices, but §6 lists no endpoint for triggering this action — only `GET /fees/overdue` (listing overdue accounts) exists.

**Proposal requirement supported (quoted):**
> §5, Admin & Parent features: "Fee management (Optional) — Admin — Define fee structures per semester or department, track all payments, view real-time financial dashboard, **send overdue notices**."

**Classification: Required** (within the scope of the Fee module, which the proposal itself separately labels "(Optional)" — see `Requirement_Analysis.md` §14 item 1 and the prior audit's Fee-module scoping discussion). The capability to *send* overdue notices, as opposed to merely *viewing* them, is explicitly named in the same feature row.

**Design Enhancement within this endpoint:** The `scope: "selected" | "all_overdue"` parameter (supporting both a single-student notify and a bulk "notify everyone currently overdue" action) is an engineering enhancement — the proposal's three words ("send overdue notices") do not specify individual-vs-bulk semantics; both were added because the `UI_Wireframes.md` Admin Fee Dashboard reasonably needs both a per-row action and a bulk action, and one endpoint with a scope parameter avoids duplicating logic across two endpoints.

---

## 6. `GET /results/reports`

**Why it was added:** The proposal's Admin Reports feature explicitly names result reporting as a required capability, but §6 only provides an endpoint for attendance reporting (`GET /attendance/reports`) — result reporting has no corresponding row.

**Proposal requirement supported (quoted):**
> §5, Admin & Parent features: "Reports — Admin — Generate attendance, **result**, and fee reports by department, semester, or individual student."

**Classification: Required.** "Result... reports" is named in the same sentence, with the same three grouping dimensions (department/semester/student), as the attendance reports that did receive a proposal-listed endpoint. There is no textual basis for treating result reporting as less required than attendance reporting — only the §6 table happened to omit it.

**Design Enhancement within this endpoint:** The specific response shape (`grade_distribution` array, `pass_count`/`fail_count` fields) is an engineering interpretation of "generate result reports" — the proposal does not specify what a result report contains, only that one must exist.

**Design Enhancement, implemented Milestone 10:** An additive `average_gpa` field (approved Milestone 10 pre-implementation Finding A) reuses the existing credit-hour-weighted GPA formula already implemented for `GET /results/me` (`result_service.compute_credit_weighted_gpa`, extracted to a shared public function so neither endpoint duplicates the calculation) — no new business logic was written. `pass_count`/`fail_count` are determined by `grade_point > 0` (pass) / `grade_point == 0` (fail) rather than pattern-matching `grade_letter`, since `grade_letter` is Teacher-supplied free text with no fixed enum (`API_Contract.md` §5.2) — a further engineering interpretation of the same undefined "result report" content noted above.

---

## 7. `GET /fees/reports`

**Why it was added:** Same proposal sentence as endpoint #6 — fee reporting is named alongside attendance and result reporting, but has no corresponding row in §6.

**Proposal requirement supported (quoted):**
> §5, Admin & Parent features: "Reports — Admin — Generate attendance, result, and **fee** reports by department, semester, or individual student."

**Classification: Required** (within the Fee module's "(Optional)" scoping — same caveat as endpoint #5). Fee reporting is named in the identical sentence as attendance reporting, which the proposal did enumerate as an endpoint.

**Design Enhancement within this endpoint:** The specific aggregate fields returned (`total_collected`, `total_outstanding`, `total_overdue`) are an engineering interpretation — the proposal does not define what constitutes a "fee report," only that one must be generatable.

---

## Summary Table

| # | Endpoint | Proposal Section | Classification | Design Enhancement Present? |
|---|---|---|---|---|
| 1 | `POST /schedule/change-requests` | §4 (Teacher) | Required | Request payload shape |
| 2 | `POST /schedule/change-requests/{id}/resolve` | §4 (Teacher) | Required | Two-endpoint split (vs. one combined) |
| 3 | `GET /notifications` | §3 (Student), §7 (Screens) | Required | `unread_count`, `is_read` filter |
| 4 | `PUT /notifications/{id}/read` | §7 (Screens) | Required | Idempotent-read behavior |
| 5 | `POST /fees/overdue/notify` | §5 (Admin) | Required | Bulk vs. individual `scope` parameter |
| 6 | `GET /results/reports` | §5 (Admin) | Required | Response field shape |
| 7 | `GET /fees/reports` | §5 (Admin) | Required | Response field shape |

**No endpoint in this list is a pure Design Enhancement or pure Derived endpoint** — every one traces directly to explicit proposal prose. This is a meaningfully different situation from inventing scope: in every case, the proposal's own feature list (§3/§4/§5) or screen list (§7) already promised the capability to the client; the §6 API table was simply incomplete relative to the rest of the same document.

---

## Additional Items Identified Outside the Proposal's §6 API Table

Two categories of engineering-necessary endpoints, both absent from the proposal's §6 table, with two different resolutions:

### Reference data CRUD (Department, Course, Room, Semester) — formalized in Milestone 1
**Classification: Derived.** The proposal never names these as endpoints, and never even fully names them as standalone entities — but Required features cannot function without them: `POST /users/students` needs a `department_id` to reference, `POST /schedule` needs a `room_id`, `POST /fees` needs a `semester_id`, and so on. These are pure plumbing, logically unavoidable given the Required features that depend on them. **Status:** formalized as `API_Contract.md` §10 (12 endpoints: list/create/get-by-id for each of Department, Course, Room, Semester) and implemented in Milestone 1. Scope deliberately minimal — update/delete were not implemented, since nothing yet needs to edit or remove reference data; add them only when a later milestone actually requires it, not preemptively. **Auth note (resolved, Milestone 2):** these endpoints shipped unauthenticated in Milestone 1, tracked as a known, temporary state in `PROJECT_PROGRESS.md`, not a silent gap. Retrofitted with RBAC in Milestone 2: read endpoints (list/get-by-id) require authentication but accept any authenticated role; create endpoints require Admin, completing the "User Roles (intended): Admin" already documented for them since Milestone 1.

### `POST /schedule/class-sessions`, `POST /schedule/enrollments` — formalized in Milestone 4

**Classification: Derived.** Same category as the Reference Data CRUD above — the proposal never names `class_session` or `enrollment` as standalone entities or endpoints, but Required features cannot function without them: `POST /schedule` (FR-046) requires an existing `class_session_id`, and `GET /schedule/me`'s own documented Student response (`API_Contract.md` §7.1) depends on `enrollment` rows already existing. Without a way to create either, Milestone 4's own core deliverable — a working, testable scheduling workflow with conflict detection — cannot be exercised end-to-end, and Milestones 5/6 both explicitly depend on `class_session` existing. Found during the Milestone 4 pre-implementation review; presented to the user as a choice between adding minimal Admin CRUD (this option) or seed-only population (the Milestone 3 Parent-account precedent) — the user selected minimal Admin CRUD, since unlike Parent-linking, these two entities are load-bearing for the milestone that defines them, not a deferrable future feature. **Status:** formalized as `API_Contract.md` §7.8-7.9 and implemented in Milestone 4. Scope deliberately minimal — create-only, no list/update/delete, matching Milestone 1's reference-data precedent of adding exactly what's needed and no more.

### `GET /schedule/class-sessions/{class_session_id}/roster` — formalized in Milestone 5

**Classification: Derived.** The proposal never names a roster-listing capability — but `UI_Wireframes.md` §15 (Teacher: Attendance Marker) requires the roster to load with enrolled students pre-populated before marking begins, and no endpoint anywhere (not `GET /attendance/{classId}`, which only returns records that already exist, not `GET /users/students`, which has no `class_session_id` filter) provides this. Without it, the documented Attendance Marker workflow cannot function as specified for a class session's first-ever marking session. Found during the Milestone 5 pre-implementation review; presented to the user as a choice between adding this minimal endpoint or leaving the roster unbuildable for unmarked dates — the user selected adding it, consistent with the Milestone 4 precedent for `class_session`/`enrollment`. **Status:** formalized as `API_Contract.md` §7.10 and implemented in Milestone 5, via the schedule router/service (not attendance) since it operates on `enrollment`/`class_session`, both owned by Scheduling. Scope deliberately minimal — read-only, Teacher-of-that-class-session or Admin only.

### `POST /exams/{id}/start` — formalized in Milestone 6

**Classification: Derived.** The proposal never names an exam-start action — but `UI_Wireframes.md` §5 (Exam Room) describes zero server round-trips during an exam attempt except the final `POST /exams/{id}/submit`, and VR-004's time-limit enforcement (`Requirement_Analysis.md`) requires a server-recorded start time that predates that final call — trusting a client-supplied elapsed time would let a student falsify how long they'd been taking the exam. Found during the Milestone 6 pre-implementation review; presented to the user as a choice between adding this minimal endpoint or having `GET /exams/{id}` create the `exam_submission` row as a side effect — the user selected adding the dedicated endpoint, consistent with the Milestone 4/5 precedent of adding exactly the minimal capability needed and no more. **Status:** formalized as `API_Contract.md` §3.6 and implemented in Milestone 6. Scope deliberately minimal: Student-only, idempotent (returns the existing `in_progress` submission if one exists rather than erroring or creating a second), and `started_at` is set from the server clock only and is immutable once recorded — no endpoint ever updates it.

### `GET /exams/{id}/submissions/{submission_id}` — formalized in Milestone 6

**Classification: Derived.** The proposal never names a per-submission detail view — but `POST /exams/{id}/grade` (`API_Contract.md` §3.9) requires `answer_id` values per grade, and no endpoint returned a submission's actual answer content (`answer_text`/`selected_option_id`) alongside those ids, so a Teacher building the documented Grading Interface (`UI_Wireframes.md` §14) had no way to see what a student actually answered before assigning marks. Found during Milestone 6 frontend implementation, once the Grading Interface page was reached and could not be built against the existing endpoint set; presented to the user as a choice between (a) this dedicated endpoint, (b) extending `GET /exams/{id}/results` to embed per-answer detail, or (c) pausing frontend work — the user selected (a), keeping aggregate reporting (`/results`) and per-answer grading detail (`/submissions/{submission_id}`) as separate responsibilities rather than merging them into one response shape. **Status:** formalized as `API_Contract.md` §3.8 and implemented in Milestone 6. Scope deliberately minimal: read-only, Teacher-who-created-the-exam or Admin only, questions returned in `order_index` order with the student's answer and any existing `question_grade` already recorded for it — no fields beyond what the Grading Interface needs.

### `result.exam_id` column — added in Milestone 7

**Classification: Derived.** The proposal never names this column, and the original `Database_Design.md` §6.21 draft didn't include it — but `POST /results/{examId}/submit` (FR-034) submits results per-exam and the Admin: Result Approval wireframe (`UI_Wireframes.md` §11) groups its pending-results queue by Exam name; without a stored `exam_id`, neither the queue display nor Milestone 7's mandatory Domain Rule 6 (verifying a Result's `QuestionGrade` provenance) could be satisfied once a request completed. Found during the Milestone 7 pre-implementation review; presented to the user as a choice between adding the column (this option) or redesigning the Admin queue to group by Course instead of Exam — the user selected adding the column. **Status:** formalized as `Database_Design.md` §6.21 (Milestone 7 design note) and implemented in Milestone 7. Scope deliberately minimal: nullable, `ON DELETE RESTRICT`, records only which exam most recently triggered/updated the row — `(student_id, course_id, semester_id)` remains the actual business-uniqueness key, unchanged from the original design.

### `GET /results/pending` — formalized in Milestone 7

**Classification: Derived.** The proposal never names a pending-results queue action — but the Admin: Result Approval page (`UI_Wireframes.md` §11) requires a queue table (Exam/Class/Submitted By/Date) with an expandable per-student review panel, and none of Milestone 7's other four documented endpoints (`GET /results/me`, `POST /results/{examId}/submit`, `POST /results/{id}/approve`, `GET /results/{studentId}/transcript`) can list or retrieve pending results at all — `GET /results/reports` (§9.1) is a different, aggregate-only, published-results-only reporting endpoint, also out of Milestone 7's scope. Found during Milestone 7 implementation, once the Admin: Result Approval page was reached and could not be built against the existing endpoint set; presented to the user as a choice between (a) this dedicated endpoint or (b) reusing `GET /exams/{id}/results` (mixing the Results domain's approval-workflow UI with the Exams domain's grading-report endpoint) — the user selected (a). **Status:** formalized as `API_Contract.md` §5.3 and implemented in Milestone 7. Scope deliberately minimal: read-only, Admin-only, groups `result` rows by `(exam_id, course_id, submitted_by_teacher_id, submitted_at)` — the same batch a single submit call created/updated — with a `status` filter matching the wireframe's own Status dropdown.

### `GET /health` — deliberately kept out of `API_Contract.md`
**Classification: Design Enhancement.** A liveness-check endpoint has no proposal linkage whatsoever — it exists purely to verify deployment wiring (`Implementation_Roadmap.md` Milestone 0). It is the one item in this entire document that is pure engineering convenience with zero traceability to any proposal sentence, direct or indirect. Unlike Reference Data above, this one is **not** meant to be added to `API_Contract.md` — it's infrastructure, not a versioned business resource (see `backend/app/routers/health.py`'s own docstring), so its absence from the contract is the correct, permanent state, not a pending action.

---

## Backend Middleware & Utilities (Milestone 0 Foundation)

Found during a Milestone 0 self-review against the full documentation set (per the standing policy in `CLAUDE.md` §14 item 11): the pieces of backend infrastructure below are middleware and utility code with no proposal linkage, and had not been logged here despite the policy explicitly naming "middleware" and "utility" as things requiring an entry. Unlike the frontend items above, none of these need a "keep vs. remove" disposition — they are foundational plumbing, not optional/debug UI, and every one of them implements a mechanism already mandated by an approved planning document (`System_Architecture.md`), not an ad hoc invention.

| Item | Where | Classification | Why |
|---|---|---|---|
| Global exception handlers | `app/middleware/error_handlers.py` | Derived | No proposal sentence asks for a specific error shape, but `System_Architecture.md` §9 mandates the `{"error":{...}}` envelope, and no Required endpoint can be delivered without *some* error handling. |
| Request logging middleware | `app/middleware/logging.py` | Derived | Implements `System_Architecture.md` §10's structured logging strategy; a prerequisite for any endpoint to be operable/debuggable, not a feature in its own right. |
| Structured logging config | `app/core/logging_config.py` | Derived | Same rationale — `System_Architecture.md` §10. |
| Settings / config validation | `app/core/config.py` | Derived | Required for any endpoint to read `DATABASE_URL`, CORS origins, etc. — unavoidable given SQLAlchemy and CORS are both Required by the stack in `System_Architecture.md` §12. |
| SQLAlchemy engine/session (`get_db` dependency) | `app/db/session.py`, `app/db/base.py` | Derived | Direct implementation of `System_Architecture.md` §4 (PostgreSQL Architecture) — no Required feature that touches the database can exist without it. |
| CORS middleware | `app/main.py` (`CORSMiddleware`) | Derived | Required for the frontend (a Required deliverable) to call the backend (also Required) from a different origin at all — mandated implicitly by the decoupled SPA+API architecture in `System_Architecture.md` §1. |
| Alembic baseline revision | `alembic/versions/0001_initial_baseline.py` | Derived | Implements `System_Architecture.md` §4.3 (versioned migrations, never manual DDL) — establishes the migration chain before any schema exists. |

**Disposition:** N/A for all rows — none are optional or slated for removal; each is a permanent, unavoidable prerequisite for delivering the Required features layered on top of it in later milestones.

---

## Milestone 2 Schema Addition: `user.current_refresh_token_jti` / `user.refresh_token_expires_at`

**Classification: Derived.** Same category as the Milestone 0 middleware/utilities above — not a proposal feature, an unavoidable prerequisite for delivering ones that are. `Requirement_Analysis.md` NFR-004 (refresh-token rotation) and `System_Architecture.md` §5.6 (server-side logout invalidation) are both Required, but `Database_Design.md`'s original `user` table (§6.1) had no column to persist that state — the design was left open ("denylist or rotation record") rather than decided. Resolved by explicit user decision (2026-07-04, Milestone 2 kickoff): single active refresh token per user, tracked via two new nullable columns rather than a separate session table. Full rationale and the "one active session per user" consequence are documented in `Database_Design.md` §6.1's Milestone 2 design note.

**Disposition:** Permanent, not optional — required for `POST /auth/refresh` and `POST /auth/logout` (both Required, FR-002/FR-003) to function per their documented rotation/invalidation behavior.

**Also added, not originally enumerated in `Implementation_Roadmap.md`'s Milestone 2 file list:** `backend/app/repositories/user_repository.py`. Same precedent as Milestone 1 — `CLAUDE.md` §6's layering rule (services never touch the ORM session directly) is binding regardless of what a milestone's file list happens to spell out.

---

## Milestone 3 Addition: `frontend/src/features/departments/index.ts`

**Classification: Derived.** Not a proposal feature or a new API endpoint — the backend `GET /departments` endpoint it wraps already exists and is documented (Milestone 1, §10 of this document). Added because the Admin: User Management page's department selector and filter (`docs/UI_Wireframes.md` §10 — "Dept: All ▾" filter, and the Create/Edit Account form's Department field) genuinely need a typed React Query hook for it, per `CLAUDE.md` §7 ("components call these hooks, never `fetch`/`axios` directly"), and no frontend wrapper for any reference-data endpoint existed yet (Milestone 1 shipped backend-only; Milestone 0's scaffold never created a `features/departments/` or `features/reference-data/` placeholder).

**Disposition:** Permanent — every future milestone whose UI needs a department picker (Scheduling, Fees, Reports) will reuse this hook rather than duplicating it.

---

## Milestone 8 Addition: `frontend/src/features/semesters/index.ts`

**Classification: Derived.** Same precedent as `features/departments/index.ts` above — the backend `GET /semesters` endpoint it wraps already exists and is documented (Milestone 1, §10 of this document). Added because the Admin: Fee Dashboard's "New Fee Structure" form (`docs/UI_Wireframes.md` §12) needs a Semester selector, and no frontend wrapper for this reference-data endpoint existed yet.

**Disposition:** Permanent — every future milestone whose UI needs a semester picker will reuse this hook rather than duplicating it.

---

## Frontend / UI Engineering Decisions (Not API Endpoints)

Found during the Milestone 0 proposal-traceability review: two frontend elements shipped in Milestone 0 with no corresponding proposal sentence and no wireframe in `docs/UI_Wireframes.md`. Both were explicitly requested in the Milestone 0 implementation prompt ("Theme support," "Health API connectivity test") — they are authorized, not silently invented — but per the same traceability rule applied to endpoints above, they still need to be logged rather than left undocumented.

### Light/dark theme toggle
**Where:** `frontend/src/app/ThemeProvider.tsx`, toggle button in `frontend/src/components/AppLayout.tsx`.
**Classification: Design Enhancement.** No proposal sentence, feature-list row, or wireframe mentions a theme/dark-mode capability anywhere. It exists purely as a Milestone 0 foundation task (project-setup conventions), not a business requirement — zero proposal linkage, direct or indirect.
**Disposition:** Keep. It's inert with respect to every other requirement (doesn't touch data, auth, or any FR-mapped flow) and low-risk to carry forward. If a future UI pass wants pixel-exact parity with `UI_Wireframes.md`'s ASCII layouts, note that none of those wireframes depict a theme toggle in the header — reconcile at that time rather than removing a working, harmless feature now.

### Dashboard "Backend connectivity" health widget
**Where:** was `frontend/src/pages/Dashboard/index.tsx`, called `useHealthCheck()` (`frontend/src/lib/useHealthCheck.ts`).
**Classification: Design Enhancement**, paired with the already-logged `GET /health` endpoint above (same rationale: verifies deployment wiring, zero proposal linkage).
**Disposition: Removed in Milestone 10**, as planned above — `Dashboard/index.tsx` now renders the real role-specific widgets (Upcoming Exams/Attendance %/Fee Status/Recent Results for Student, etc.) per `docs/UI_Wireframes.md` page 2, converging on the approved wireframe. `useHealthCheck()` itself (`frontend/src/lib/useHealthCheck.ts`) remains unused after this removal — retained only as a candidate for a future ops/status page, not currently referenced by any route.

---

## Milestone 11 Additions: Rate limiting, API-docs gating

### `POST /auth/login` rate limiting
**Where:** `backend/app/middleware/rate_limit.py`, wired into `backend/app/routers/auth.py`'s `login` route via a FastAPI dependency.
**Classification: Derived.** Not a proposal feature — the proposal never mentions rate limiting. `Requirement_Analysis.md` §14 item 13 and `System_Architecture.md` §11 both flag this as an unspecified gap with a recommendation to add a reasonable default, which Milestone 11 (Hardening) now does: 5 attempts per 60-second window, per client IP, in-memory (single-process — see `PROJECT_PROGRESS.md`'s Milestone 11 Known Issues for the horizontal-scaling caveat).
**Disposition:** Permanent. A production deployment that scales the API tier horizontally (`System_Architecture.md` §8) would need to swap the in-memory store for a shared one (e.g. Redis) — noted as a known limitation, not implemented, since introducing a new external dependency wasn't part of the approved Milestone 11 scope.

### API docs (`/docs`, `/redoc`, `/openapi.json`) disabled in production
**Where:** `backend/app/main.py`'s `create_app()`, gated on the existing `Settings.is_production` property.
**Classification: Derived.** `System_Architecture.md` §11's Security Strategy doesn't name this specifically, but "closing off unnecessary attack surface" is the section's own stated intent, and `is_production` already existed (unused) precisely for environment-conditional behavior like this.
**Disposition:** Permanent. Development/staging/test environments are unaffected — docs remain available whenever `ENVIRONMENT` is not `production`.

### Frontend ESLint flat config
**Where:** `frontend/eslint.config.js`; new devDependencies `@eslint/js`, `typescript-eslint`, `globals`, `eslint-plugin-react-hooks`.
**Classification: Derived.** `CLAUDE.md`'s tech stack (Section 2) doesn't mandate a linter, but `frontend/package.json` already had an `eslint` devDependency and a `"lint": "eslint ."` script since Milestone 0, with no config file to back either — `npm run lint` would have failed outright. Milestone 11 completes what was already committed to rather than leaving it dangling. Kept deliberately minimal: ESLint's own recommended rules, `typescript-eslint`'s recommended rules, and only the two long-standing `eslint-plugin-react-hooks` rules (`rules-of-hooks`, `exhaustive-deps`) — not that plugin's full "recommended" set, which as of v7 also bundles a newer `set-state-in-effect` rule that would flag an idiomatic, already-tested pattern used throughout Milestones 0-10 (syncing local state from a React Query result inside `useEffect`). Enabling it would have meant refactoring frozen, working code purely to satisfy a new rule — out of scope for a hardening milestone that explicitly must not redesign or refactor for preference.
**Disposition:** Permanent. `npm run lint` now runs clean against the entire existing `src/` tree with zero errors/warnings — confirming no rule violations were introduced by keeping the scope minimal.

### Root error boundary
**Where:** `frontend/src/components/ErrorBoundary.tsx`, `frontend/src/lib/reportClientError.ts`, wrapping `<AppProviders>`/`<RouterProvider>` in `frontend/src/app/App.tsx`.
**Classification: Derived.** `System_Architecture.md` §10 (Logging Strategy) explicitly states client-side errors "are captured via an error boundary and reported to a central location distinct from routine console output" — this had never been implemented in any prior milestone. No backend endpoint exists to receive client error reports, and adding one would be new business functionality outside Milestone 11's hardening-only scope, so `reportClientError` is a single, distinctly-tagged local choke point (not a remote-logging integration) — a real deployment would only need to change that one function's body.
**Disposition:** Permanent.

### Frontend component tests
**Where:** `frontend/tests/pages/{ExamRoom,GradingInterface,ResultApproval}.test.tsx`, `frontend/tests/setup.ts`; new devDependencies `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, `jsdom`; `test` block added to `vite.config.ts`.
**Classification: Derived.** `CLAUDE.md` §10 explicitly names "exam timer, grading form, approval workflow" as the frontend's critical interaction logic requiring component tests, and `Implementation_Roadmap.md`'s own Milestone 11 file list names `frontend/tests/` — scaffolded empty since Milestone 0, never populated until now. Covers exactly those three named flows: the Exam Room countdown/auto-submit (`ExamRoomPage`), the Teacher Grading Interface's mark-entry/save and VR-006 max-marks error path (`GradingInterfacePage`), and the Admin Result Approval workflow's approve/reject-requires-comment behavior (`ResultApprovalPage`).
**Disposition:** Permanent — establishes the pattern (mock the relevant `features/*` hook module, render with a `MemoryRouter`, assert on the mutation call and rendered outcome) for any future frontend test in this project.

---

## Production-Polish Audit Additions (2026-07-05)

### Global keyboard focus-visible styling
**Where:** `frontend/src/styles/globals.css` (new `@layer base` rule).
**Classification: Derived.** `Requirement_Analysis.md`/`System_Architecture.md` don't mandate a specific focus style, but accessible keyboard navigation is an implicit baseline for any production web app, and no component in this codebase set one explicitly — focus fell back to each browser's inconsistent default, which is not guaranteed to have sufficient contrast against this app's dark-mode slate backgrounds. Applied once, globally, via `@layer base`, rather than a `focus:` utility repeated across every interactive element in every page — bounded, non-invasive, touches no component markup.
**Disposition:** Permanent.

A post-M11 production-quality audit, explicitly authorized by the user, found and fixed several places where raw database identifiers (UUIDs) were rendered to end users instead of human-readable names, and one long-standing documented gap (the Parent Portal's manual Student ID entry) that the user's own audit instructions explicitly asked to be revisited. Logged per `CLAUDE.md` §9/§14 item 11.

### `UserProfile.department_name` (additive field on `GET /users/me`)
**Where:** `backend/app/schemas/user.py` (`UserProfile.department_name`), `backend/app/services/user_service.py` (`_get_own_profile`), `frontend/src/features/users/index.ts`, `frontend/src/pages/Profile/index.tsx`.
**Classification: Design Enhancement.** The proposal never specifies whether the Profile page's Department field shows an ID or a name, but rendering a raw UUID to an end user is never acceptable UX and was flagged directly by the user's audit ("Investigate why Department displays a UUID. Replace with department name."). The existing `department_id` field is left untouched (additive, non-breaking) — `department_name` is a new, optional field populated via the same `DepartmentRepository.get()` lookup `_get_own_profile` already had a `department_id` for, so no new query pattern or N+1 risk is introduced.
**Disposition:** Permanent. The Profile page's Department field now renders `department_name` (falling back to `"—"` if a linked department was deleted), read-only, matching the read-only nature already documented for this field in `UI_Wireframes.md`.

### `GET /users/me/children` (Parent-only)
**Where:** `backend/app/routers/users.py`, `backend/app/services/user_service.py` (`get_my_children`), `backend/app/repositories/user_repository.py` (`list_linked_students`), `backend/app/schemas/user.py` (`ChildEntry`, `MyChildrenResponse`), `frontend/src/features/users/index.ts` (`useMyChildren`), `frontend/src/pages/Dashboard/ParentDashboard.tsx`.
**Classification: Derived.** This closes a gap that had been explicitly documented as a *permanent, accepted limitation* since Milestone 7 ("no endpoint anywhere enumerates a Parent's linked children... a real deployment would need such an endpoint"; see the now-superseded note in `ParentDashboard.tsx`'s prior revision and the Milestone 7/8/10 `PROJECT_PROGRESS.md` entries referencing it). The user's audit instructions explicitly revisited this exact limitation ("Typing Student IDs manually is not acceptable. If possible: show linked child automatically.") — treated as fresh, explicit authorization to implement it now, not silently invented scope. The endpoint is a thin, read-only wrapper around the `parent_student_link` table that already existed (Milestone 3) for ownership-scoping checks (`parent_has_linked_student`) — no new table, no new business rule, only a new way to *read* an existing relationship.
**Disposition:** Permanent. `ParentDashboard.tsx`'s manual "Student ID" text input is removed and replaced with a `<select>` populated from this endpoint (auto-selecting the first/only child); `FeeCentre`/`ResultsView`'s own manual student-ID entry points were not in scope for this pass and are unchanged.

### Table/UX polish pass: row hover states, status badges, empty states
**Where:** `frontend/src/pages/{Admin/FeeDashboard,ResultsView,FeeCentre,Dashboard/ParentDashboard,Dashboard/StudentDashboard,Admin/Reports,Dashboard/AdminDashboard,Admin/ResultApproval,Teacher/AttendanceMarker,Attendance,Admin/UserManagement,ExamList}/index.tsx`.
**Classification: Design Enhancement.** No business logic changed — purely presentational. Adds a consistent row-hover style (`hover:bg-slate-50`/dark equivalent) to every data table that previously had none (only `ExamList` had it before this pass), colored status badges for the three plain-text status columns that most read like an enum (`UserManagement`'s Active/Inactive, `FeeCentre`'s invoice status, `ExamList`'s exam status), and empty-state messages for three tables that previously rendered a bare empty `<table>` with no explanatory text (`Attendance`, `Admin/UserManagement`, `Teacher/AttendanceMarker`'s roster, plus the Admin Reports attendance-summary table, whose results table already had one).
**Disposition:** Permanent.

### Invoice download on Admin Fee Dashboard's Overdue Accounts table
**Where:** `frontend/src/pages/Admin/FeeDashboard/index.tsx` (new "Download Invoice" button per row).
**Classification: Design Enhancement.** No new endpoint or business logic — reuses the existing `GET /fees/invoices/{invoice_id}` endpoint (already Admin-accessible, per `_require_student_or_admin` in `backend/app/routers/fees.py`) and the existing `useDownloadInvoice()` hook (`frontend/src/features/fees/index.ts`), the same one already wired into the Student-facing `FeeCentre` page. The audit found the Admin Fee Dashboard's overdue-accounts table had no way to view/download the invoice PDF for an overdue account without navigating elsewhere — an inconsistency with the Student view, not a missing capability.
**Disposition:** Permanent.

---

## Post-M11 Gap Closure Audit Additions (2026-07-05)

A direct audit against `docs/product_proposal.pdf` (requested by the user) found the Parent role's proposal-promised attendance and timetable visibility (`product_proposal.pdf` Section 5) had no API support at all — not merely a missing frontend screen, as `Requirement_Traceability_Matrix.md`'s prior "Known Gaps" note had characterized it for FR-032/FR-037. See `PROJECT_PROGRESS.md`'s "Post-M11 Gap Closure" entry for the full summary; this section classifies each new/changed endpoint.

### `GET /attendance/me` Parent scoping (`student_id` query parameter)
**Where:** `backend/app/routers/attendance.py` (`_require_student_or_parent` dependency), `backend/app/schemas/attendance.py` (`AttendanceMeQuery.student_id`), `backend/app/services/attendance_service.py` (`get_me`), `backend/app/notifications/dispatcher.py` (`notify_attendance_warning` now fans out to linked Parents).
**Classification: Derived.** The proposal (Section 5) explicitly promises Parents "automatic alerts for absences" and an attendance summary — `GET /attendance/me` previously rejected any Parent request outright. Extended using the exact Parent-scoping convention already established by `GET /fees/me`/`GET /results/me` (required `student_id`, ownership-verified via `parent_student_link`) — no new endpoint path, no schema/migration change.
**Disposition:** Permanent.

### `GET /schedule/me` Parent scoping (`student_id` query parameter)
**Where:** `backend/app/routers/schedule.py` (`_require_student_teacher_or_parent` dependency), `backend/app/services/schedule_service.py` (`get_me`).
**Classification: Derived.** The proposal (Section 5, "Results & schedule") explicitly promises Parents their child's class timetable — `GET /schedule/me`'s RBAC previously excluded Parent from the allowed-roles list entirely (a request would 403 before reaching any ownership check). Same Parent-scoping convention as above.
**Disposition:** Permanent.

### `GET /fees/structures` (Derived, admin-only, paginated)
**Where:** `backend/app/routers/fees.py`, `backend/app/services/fee_service.py` (`list_fee_structures`), `backend/app/repositories/fee_repository.py` (`list_fee_structures`), `backend/app/schemas/fee.py` (`FeeStructureSummary`), `frontend/src/features/fees/index.ts` (`useFeeStructures`), `frontend/src/pages/Admin/FeeDashboard/index.tsx` (Record Payment's Fee Structure field is now a `<select>`).
**Classification: Derived.** No endpoint anywhere listed existing fee structures — the Admin Fee Dashboard's Record Payment form required an Admin to already know and hand-type a `fee_structure_id` UUID, the same class of known limitation as Milestone 4's Admin schedule panel (`PROJECT_PROGRESS.md` Milestone 8 entry). Follows the existing reference-data pagination convention (`PaginatedResponse`, per `CLAUDE.md` §11) rather than an unbounded list.
**Disposition:** Permanent.

### Attendance page Calendar view
**Where:** `frontend/src/pages/Attendance/index.tsx` (`CalendarMonthView`).
**Classification: Derived.** `UI_Wireframes.md`'s "calendar or table view" toggle existed since Milestone 5 with Calendar mode showing a placeholder message. Implemented as a month-grid rendering of the same `GET /attendance/me` data already fetched for Table view — no new endpoint.
**Disposition:** Permanent.

### Profile photo upload (Student/Teacher)
**Where:** `frontend/src/pages/Profile/index.tsx` (client-side resize-to-JPEG-data-URI, then `PUT /users/me` with `profile_photo_url`).
**Classification: Derived.** The proposal (Section 3, Student — Profile) explicitly requires a profile photo; `MeUpdate.profile_photo_url` and the `student`/`teacher` table columns already existed (since Milestone 3) but no frontend page ever offered a way to set them. No new backend endpoint — the existing `PUT /users/me` field is reused as-is. Not suitable for large-scale production use (a data-URI string in a `VARCHAR` column doesn't belong in a real object-storage architecture), but proportionate to this project's scope and explicitly avoids inventing new storage infrastructure/folders outside `System_Architecture.md` §7's documented structure.
**Disposition:** Permanent, with the production caveat above noted for any future hardening pass.

### Profile page academic history / assigned courses sections
**Where:** `frontend/src/pages/Profile/index.tsx` (`AcademicHistorySection` for Student, `AssignedCoursesSection` for Teacher).
**Classification: Derived.** FR-008 (Student — "views academic history alongside profile data") and the Teacher Profile & courses feature (Section 4) were both previously satisfied only by data being reachable on a *different* page (Results View, Timetable) — this pass adds Profile-page sections that reuse `GET /results/me`/`GET /schedule/me` directly, no new endpoints. Teacher "teaching history" across past semesters (as distinct from the current semester's assignments) remains unbuilt — no endpoint exposes it, and the section is labeled "this semester" rather than overclaiming.
**Disposition:** Permanent, with the teaching-history limitation noted above tracked as a known, honestly-labeled gap.

---
