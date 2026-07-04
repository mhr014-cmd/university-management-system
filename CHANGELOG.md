# Changelog

All notable changes to this project are documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/) — grouped under `### Added` / `### Changed` / `### Fixed` per release. This project is pre-release throughout implementation, so all entries accumulate under `[Unreleased]` until a milestone is judged ready to tag (see `PROJECT_PROGRESS.md` for milestone-level status).

---

## [Unreleased]

### Added (Milestone 11 — Hardening, Testing & Deployment)
- `POST /auth/login` rate limiting (`app/middleware/rate_limit.py`): 5 attempts per 60-second window, per client IP, in-memory fixed window — resolves `Requirement_Analysis.md` §14 item 13
- `/docs`, `/redoc`, `/openapi.json` disabled when `ENVIRONMENT=production` (via the existing `Settings.is_production` property) — unaffected in every other environment
- Frontend root error boundary (`components/ErrorBoundary.tsx`, `lib/reportClientError.ts`) — implements `System_Architecture.md` §10's client-side error capture requirement, never built in any prior milestone
- Minimal ESLint flat config (`frontend/eslint.config.js`) completing the `lint` script/`eslint` devDependency that existed unconfigured since Milestone 0
- Frontend component tests (`frontend/tests/pages/{ExamRoom,GradingInterface,ResultApproval}.test.tsx`) — covers the three flows `CLAUDE.md` §10 names explicitly: exam timer/auto-submit, grading form entry + VR-006 error path, result approval/reject-requires-comment workflow
- `backend/scripts/seed_demo_data.py` fully implemented per `Database_Design.md` §11 (2 departments, 2 semesters, 4 rooms, 1 admin, 3 teachers, 8 students, 2 parents, 5 courses, 6 class sessions, exams in every lifecycle state, attendance/results/fees/notifications data) — idempotent, same precedent as `seed_admin.py`
- `.github/workflows/backend-ci.yml`/`frontend-ci.yml` wired to real pipelines (disposable Postgres service + pytest/alembic for backend; tsc/lint/vitest/build for frontend), replacing the Milestone 0 placeholders

### Removed (Milestone 11)
- `frontend/src/pages/Parent/ChildView/index.tsx` — orphaned placeholder, never routed, never built across Milestones 7–10 (no endpoint anywhere enumerates a Parent's linked children). The underlying FR-032/FR-037 requirement is recorded as a final, permanent, tracked limitation in `docs/UI_Wireframes.md` §17 and `docs/Requirement_Traceability_Matrix.md`, not silently dropped.

### Changed (Milestone 11 — Documentation)
- `docs/API_Contract.md` §1.1: documents the new rate-limit policy and `429` status code
- `docs/UI_Wireframes.md` §17: final Known Limitation note for the Parent: Child View screen
- `docs/Requirement_Traceability_Matrix.md`: FR-032/FR-037 updated to reflect the screen's final (not "deferred") status
- `docs/Proposal_vs_Engineering_Additions.md`: six new entries (rate limiting, docs-gating, ESLint config, error boundary, component tests, and the Parent: Child View removal), each added in the same change as the item it documents
- `docs/Implementation_Roadmap.md`: corrected stale Milestone 11 file paths (`infra/docker/` → `docker/`, `infra/ci/pipeline.yml` → `.github/workflows/*.yml`)
- `docs/Database_Design.md` §11: removed a stale note about the attendance-warning threshold "needing confirmation" (resolved in Milestone 5)
- `backend/.env.example`: removed a duplicate `ENVIRONMENT` line
- `README.md`: updated from its Milestone-0-era status line to reflect Milestones 0–10 complete
- `PROJECT_PROGRESS.md`: Milestone 10's Review Status updated to Approved (user sign-off, git tag `v1.1-milestone10`); Milestone 11 row and full Milestone Detail Log entry added; Summary section updated (100% overall progress — all 12 milestones complete)

### Known Issues (Milestone 11)
- The GitHub Actions CI runner itself was not exercised (both workflows are valid YAML with steps verified locally, but a real Actions run requires pushing to GitHub).
- The login rate limiter is in-memory/single-process — would need a shared store (e.g. Redis) for a horizontally-scaled deployment.
- The Parent: Child View dedicated screen is now a permanent, accepted limitation, not a deferred one — see the Removed section above.
- Frontend component test coverage is scoped to the three flows `CLAUDE.md` §10 names explicitly, not exhaustive coverage of every page.

### Added (Milestone 10 — Dashboards & Reporting)
- `GET /results/reports`: Admin result reports (grade distribution, pass/fail counts, additive `average_gpa` — Finding A) by department/semester/student, `published` results only; pass/fail determined by `grade_point > 0`/`== 0` since `grade_letter` is Teacher-supplied free text
- `GET /fees/reports`: Admin fee reports (`total_collected`/`total_outstanding`/`total_overdue`) by department/semester/student; `total_overdue` is a subset of `total_outstanding`, matching the Admin: Fee Dashboard's existing (M8) semantics
- `POST /fees/overdue/notify`: Admin manually triggers an overdue fee notice, individually (`scope: "selected"`, whole batch validated before any write) or in bulk (`scope: "all_overdue"`) — reuses the existing `dispatcher.notify_fee_due` unchanged, no second notification system
- Additive `created_at` field on `GET /users/students`/`GET /users/teachers` response DTOs (Finding D) — no business-logic, schema, or new-endpoint change
- Frontend: Student/Teacher/Parent/Admin Dashboard widgets (`pages/Dashboard/{Student,Teacher,Parent,Admin}Dashboard.tsx`), replacing the Milestone 0 placeholder's "Backend connectivity" health-check widget; Admin: Reports page (Attendance/Results/Fees tabs, `pages/Admin/Reports/index.tsx`); Admin: Fee Dashboard gained the wireframe's Notify/Send Bulk Overdue Notice actions, deferred since Milestone 8
- New feature hooks: `features/attendance/index.ts` (`useAttendanceReports`), `features/results/index.ts` (`useResultsReport`), `features/fees/index.ts` (`useFeesReport`, `useNotifyOverdueAccounts`)
- Backend test suite: `tests/unit/test_report_service.py`, additions to `tests/unit/test_fee_service.py`, `tests/integration/test_reports_router.py` — 23 new tests, 341 total passing

### Changed (Milestone 10)
- `result_service.py`: extracted `compute_credit_weighted_gpa` as a shared public function (previously private inline logic in `_build_semester_entries`) so `GET /results/me` and the new `GET /results/reports` reuse one GPA implementation, per Finding A

### Changed (Milestone 10 — Documentation)
- `docs/API_Contract.md`: added the additive `average_gpa` field to §9.1 and `created_at` to §2.3 (both noted as Milestone 10 additions); §9.1/§9.2/§6.7 (the report/notify endpoints themselves) were already fully documented pre-implementation during the Project Readiness Audit
- `docs/Proposal_vs_Engineering_Additions.md` §6: added a note on the `average_gpa`/pass-fail-threshold engineering decisions
- `docs/UI_Wireframes.md` Section 2: added a Known Limitations subsection documenting Findings B/C/D/E's resolutions (Teacher Pending Grading computed client-side, Teacher Schedule-change-request widget omitted, Admin Recent Signups backed by `created_at`, Parent Dashboard's partial widget availability); Section 18's Results tab description updated for `average_gpa`
- `docs/Requirement_Traceability_Matrix.md`: FR-054, FR-055, FR-056 updated to Verified (M10)
- `PROJECT_PROGRESS.md`: Milestone 9's Review Status updated to Approved (user sign-off, git tag `v1.0-milestone9`); Milestone 10 row and full Milestone Detail Log entry added; Summary section updated (92% overall progress, current/last/next milestone)

### Known Issues (Milestone 10)
- Frontend UI not visually exercised in an interactive browser this milestone — per this session's established preview-tooling restriction (a prior `.claude/launch.json` `env`-field incident), verification relied on `tsc`/`npm run build`/a live API-contract smoke test/code review instead.
- Teacher Dashboard's Pending Grading count issues one HTTP request per not-yet-published exam (Finding B's "compute client-side" resolution) — acceptable at this system's scale, not a single aggregate call.
- Parent Dashboard has no linked-children selector, only a manual Student ID field — the underlying gap (no endpoint anywhere enumerates a Parent's linked children) predates this milestone (M7-M8) and remains open.
- Teacher Schedule-change-request status widget is not implemented (Finding C) — no endpoint exists for a Teacher to query their own pending change-request status.

### Added (Milestone 9 — Notifications)
- `notification` table (Alembic revision `0010_notifications`), matching `Database_Design.md` §6.26 column-for-column, with `Index`/`is_read` default declared on the model itself so `alembic revision --autogenerate` produced an empty diff on the first attempt
- `GET /notifications`: authenticated user's own feed (newest first), with `is_read` filter and pagination, plus `unread_count`
- `PUT /notifications/{id}/read`: idempotent mark-as-read, ownership-hidden as 404 for another user's notification
- `app/notifications/dispatcher.py`: four automatic notification triggers, each dispatched by its originating service only after that service's own transaction commits, and each wrapped so a dispatch failure can never break or roll back the originating business operation —
  - `result_published` on `POST /results/{id}/approve` (`decision: approve`), to the Student only
  - `schedule_change` on `PUT`/`DELETE /schedule/{id}`, to enrolled students **and** the assigned Teacher (see Fixed, below)
  - `attendance_warning` on `POST /attendance`, only on a genuine threshold crossing (`>=80%` before the new record, `<80%` after) — not repeated while the student stays below 80%
  - `fee_due` on `POST /fees`'s invoice auto-generation, to each newly-invoiced Student and any linked Parent
- Frontend: `features/notifications/index.ts`, `pages/Notifications/index.tsx` (chronological feed, unread styling, "Mark all as read", per-item deep-link by type), a persistent notification bell with an unread-count badge in `AppLayout`
- Backend test suite: `tests/unit/test_notification_dispatcher.py`, `tests/unit/test_notification_service.py`, `tests/integration/test_notifications_router.py` — 25 new tests, 318 total passing

### Fixed (Milestone 9)
- `Requirement_Analysis.md` FR-051 and `API_Contract.md` both said schedule-change notifications go to Students only — `UI_Wireframes.md` §16's own Role Visibility line explicitly lists "schedule changes for Student/Teacher." Corrected during pre-implementation review; the entry's assigned Teacher is now notified alongside enrolled students.

### Changed (Milestone 9 — Documentation)
- `docs/API_Contract.md`: added Section 8.3 (Notification Triggers, Recipients, and Message Templates) documenting all four automatic triggers exactly; updated §4.2 (attendance), §5.4 (result approval), §6.2 (fee structure creation), and §7.3/§7.4 (schedule update/delete) to reference the now-implemented dispatch
- `docs/Requirement_Analysis.md`: FR-051 corrected to include Teacher recipients
- `docs/Requirement_Traceability_Matrix.md`: FR-031, FR-044, FR-051, FR-052, FR-053 updated (FR-044 honestly marked partially implemented — the invoice-issuance `fee_due` notification is built, a scheduled day-before-due-date reminder is not, since no cron/scheduler exists anywhere in this project); added notes for the FR-051 recipients correction, the attendance-warning threshold-crossing resolution, and the exam-notification-scope resolution
- `docs/Implementation_Roadmap.md`: added a Milestone 9 scope note recording all three pre-implementation resolutions
- `PROJECT_PROGRESS.md`: Milestone 8's Review Status updated to Approved (user sign-off, git tag `v0.9-milestone8`); Milestone 9 row and full Milestone Detail Log entry added; Summary section updated (83% overall progress, current/last/next milestone, HEAD commit)

### Known Issues (Milestone 9)
- FR-044's scheduled-reminder half (a due-date reminder sent some days before `due_date`) is not implemented — no cron/scheduler mechanism exists anywhere in this project; only the event-driven `fee_due` notification at invoice-issuance time is built.
- The notification bell links directly to the full Notifications page rather than also offering the wireframe's optional desktop dropdown panel — a documented simplification, same class as Milestone 5's Attendance Calendar view.
- `POST /fees/overdue/notify` (FR-056, manual overdue-notify action) is explicitly Milestone 10 scope per `Implementation_Roadmap.md`'s own note — not built here even though the `notification` table it needs now exists.
- Migration `0010_notifications` is hand-authored, not `alembic revision --autogenerate`'d, though its upgrade/downgrade cycle and an autogenerate diff-check are both confirmed clean.
- Frontend UI not visually exercised in a browser this milestone — per the standing instruction not to rely on preview tooling, verification was `tsc`/`npm run build`/code review only.

### Added (Milestone 8 — Fees, Optional)
- `fee_structure`, `invoice`, `payment` tables (Alembic revision `0009_fees`), matching `Database_Design.md` §6.23-6.25 column-for-column, including the Milestone 8 addition of a unique `(student_id, fee_structure_id)` constraint on `invoice`, with `index=True`/`UniqueConstraint`/`CheckConstraint` declared on the models themselves so `alembic revision --autogenerate` produced an empty diff on the first attempt
- `POST /fees`: Admin defines a fee structure (department/semester-scoped or university-wide); automatically generates one `unpaid` invoice for every currently-active, enrolled-that-semester, department-matching student — the only place `invoice` rows are created (resolved during pre-implementation review, confirmed with the user)
- `GET /fees/me`: Student's own fee status (Parent-scoped via a required `student_id` query param, verified against `parent_student_link`), with `outstanding_balance` and per-invoice `status` computed server-side from persisted `payment` rows; `overdue` is derived at read time from `due_date`, never stored
- `POST /fees/payments`: Admin records a payment; strictly rejects overpayment beyond the invoice's remaining balance and any payment against an already fully-`paid` invoice (both 409) — resolves VR-008's previously "unresolved" overpayment policy per this milestone's own Fees Domain Requirements
- `GET /fees/payments/{studentId}`: Admin/Parent payment history, Parent ownership-checked via `parent_student_link`
- `GET /fees/invoices/{id}`: PDF invoice via `reportlab`, ownership-checked (Student: own only; Admin: any)
- `GET /fees/overdue`: Admin list of accounts with an unpaid/partially-paid invoice past its `due_date`, with `amount_due` computed from persisted payments
- Frontend: `features/fees/index.ts`, `features/semesters/index.ts` (Derived, same precedent as `features/departments`), `pages/FeeCentre/index.tsx` (balance card, payment history, invoice download — Student-facing only, see Known Issues), `pages/Admin/FeeDashboard/index.tsx` (stat cards, New Fee Structure / Record Payment forms, overdue accounts table)
- Backend test suite: `tests/unit/test_fee_service.py`, `tests/integration/test_fees_router.py` — 40 new tests, 293 total passing

### Changed (Milestone 8 — Documentation)
- `docs/Database_Design.md` §6.25: added the invoice-creation design note (auto-generation eligibility, confirmed with the user), the `status`-recalculation/derived-`overdue` note, and the `pdf_url`-stays-null note; added a unique constraint row for `(student_id, fee_structure_id)`
- `docs/API_Contract.md`: documented invoice auto-generation on `POST /fees` (§6.2), the resolved strict-overpayment policy and invoice-must-exist requirement on `POST /fees/payments` (§6.3), Parent `student_id` scoping and the derived-`overdue`/`student_id`-response-field additions on `GET /fees/me` (§6.1), and the no-grace-period overdue determination on `GET /fees/overdue` (§6.6)
- `docs/Requirement_Traceability_Matrix.md`: FR-038-FR-043 updated to Verified; FR-044 left honestly Pending (depends on the Milestone 9 `notification` module)
- `docs/Requirement_Analysis.md`: VR-008's overpayment ambiguity marked resolved (strictly disallowed)
- `docs/Implementation_Roadmap.md`: added a Milestone 8 scope note recording the invoice-creation resolution
- `docs/Proposal_vs_Engineering_Additions.md`: logged `frontend/src/features/semesters/index.ts` as a Derived addition (same precedent as `features/departments`)
- `PROJECT_PROGRESS.md`: Milestone 7's Review Status updated to Approved (user sign-off, git tag `v0.8-milestone7`); Milestone 8 row and full Milestone Detail Log entry added; Summary section updated (75% overall progress, current/last/next milestone, HEAD commit)

### Known Issues (Milestone 8)
- Parent-facing frontend UI for Fees is not built — the backend fully implements and tests FR-038/FR-041 Parent access, but no endpoint anywhere enumerates a Parent's linked children, and the full Parent Portal page isn't scheduled for this milestone (same known gap as Milestone 7's Results View).
- The Admin: Fee Dashboard's "Notify"/"Send Bulk Overdue Notice" actions (FR-056, `POST /fees/overdue/notify`) are not implemented — explicitly deferred to Milestone 9 per `Implementation_Roadmap.md`'s own Milestone 8 note, since that endpoint writes to the `notification` table.
- The Record Payment form's Fee Structure field is a raw UUID text input, not a dropdown — no `GET /fees` list endpoint exists in the documented API contract (same class of known limitation as Milestone 4's Admin schedule panel).
- Migration `0009_fees` is hand-authored, not `alembic revision --autogenerate`'d, though its upgrade/downgrade cycle and an autogenerate diff-check are both confirmed clean.
- Frontend UI not visually exercised in a browser this milestone — per the standing instruction not to rely on preview tooling, verification was `tsc`/`npm run build`/code review only.
- FR-044 (automatic due-date reminders/overdue notices) is not implemented — depends on the Milestone 9 notification module.

### Added (Milestone 7 — Results & Transcripts)
- `result` table (Alembic revision `0008_results`), matching `Database_Design.md` §6.21 column-for-column, including the Milestone 7 `exam_id` addition (nullable FK, for Admin queue display/traceability — `(student_id, course_id, semester_id)` remains the authoritative business key), with `index=True`/`UniqueConstraint` declared on the model itself so `alembic revision --autogenerate` produced an empty diff on the first attempt
- `GET /results/me`: Student's own results (Parent-scoped via a required `student_id` query param, verified against `parent_student_link`), with a credit-hour-weighted GPA per semester (resolves `Requirement_Analysis.md` §14 item 6)
- `POST /results/{examId}/submit`: Teacher submits a course's final results, gated on the exam being `published` and fully graded, with all 15 Milestone 7 mandatory Domain Rules enforced before any write, and resubmission-in-place allowed only for previously `rejected` rows
- `GET /results/pending` (Derived Engineering Addition, confirmed with the user): Admin-only queue of pending results grouped by exam, matching the Admin: Result Approval wireframe — no other endpoint could list/retrieve pending results
- `POST /results/{id}/approve`: Admin approves (publishes) or rejects a submitted result; a comment is required for reject (closes the contract's own previously-flagged "policy TBD", resolved from wireframe evidence)
- `GET /results/{studentId}/transcript`: PDF transcript via `reportlab`, ownership-checked (Student: own only; Admin: any), returns a valid (possibly empty-results) PDF rather than a 409 when no results are published yet
- Frontend: `features/results/index.ts`, `pages/ResultsView/index.tsx` (semester selector, GPA summary, results table, transcript download — Student-facing only, see Known Issues), `pages/Admin/ResultApproval/index.tsx` (pending queue, expandable review panel, approve/reject)
- Backend test suite: `tests/unit/test_result_service.py`, `tests/integration/test_results_router.py` — 42 new tests, 253 total passing
- `reportlab==5.0.0` (+ `pillow`, `charset-normalizer` transitive deps) added to `backend/requirements.txt`/`pyproject.toml`, finalizing `System_Architecture.md` §12's "PDF library TBD"

### Fixed (Milestone 7)
- `GET /results/me`'s documented response had no `student_id`, so the frontend had no way to construct the `GET /results/{studentId}/transcript` URL for a "download my own transcript" action — added `student_id` to the response in the same change (same class of fix as Milestone 5's `GET /attendance/{classId}` `id`-field addition)

### Changed (Milestone 7 — Documentation)
- `docs/Database_Design.md` §6.21: added the `exam_id` column and a design note explaining the schema decision and the resubmission-after-reject policy, both confirmed with the user during pre-implementation review
- `docs/API_Contract.md`: added Section 5.3 `GET /results/pending` (renumbering approve/transcript to §5.4/§5.5); documented the resolved GPA formula, Parent `student_id` scoping, mandatory reject comment, empty-transcript-is-200 policy, and the `student_id` response-field fix, all in §5.1/§5.2/§5.4/§5.5
- `docs/Requirement_Traceability_Matrix.md`: FR-033-FR-037 updated to Verified; FR-037 honestly annotated as backend-only (no frontend page yet); added notes for both Derived additions and the resolved workflow policies
- `docs/Proposal_vs_Engineering_Additions.md`: classified `result.exam_id` and `GET /results/pending` as Derived, documenting why each is required
- `docs/Requirement_Analysis.md` §14 item 6 (GPA formula) marked resolved, per that document's own A-004 assumption
- `docs/Implementation_Roadmap.md`: added two Milestone 7 scope notes recording both Derived additions and their rationale
- `PROJECT_PROGRESS.md`: Milestone 6's Review Status updated to Approved (user sign-off, git tag `v0.7-milestone6`); Milestone 7 row and full Milestone Detail Log entry added; Summary section updated (67% overall progress, current/last/next milestone, HEAD commit)

### Known Issues (Milestone 7)
- Parent-facing frontend UI for Results is not built — the backend fully implements and tests FR-037, but no endpoint anywhere enumerates a Parent's linked children, and the full Parent Portal page isn't scheduled for this milestone.
- `POST /results/{id}/approve`'s reject `comment` is validated but not persisted — the `result` table has no comment/rejection-reason column (a pre-existing schema limitation, not introduced this milestone), and the documented response doesn't echo one back either.
- Migration `0008_results` is hand-authored, not `alembic revision --autogenerate`'d, though its upgrade/downgrade cycle and an autogenerate diff-check are both confirmed clean.
- Frontend UI not visually exercised in a browser this milestone — per the standing instruction not to rely on preview tooling, verification was `tsc`/`npm run build`/code review only.
- Result-publication notifications (FR-052) are not implemented — depends on the Milestone 9 notification module.

### Added (Milestone 6 — Exams & Grading)
- `exam`, `question`, `question_option`, `exam_submission`, `answer`, `question_grade` tables (Alembic revision `0007_exams`), matching `Database_Design.md` §6.14-6.19 column-for-column, with `index=True`/`UniqueConstraint`/`CheckConstraint` declared on the models themselves so `alembic revision --autogenerate` produced an empty diff on the first attempt
- `GET /exams`, `POST /exams`, `GET /exams/{id}`, `PUT /exams/{id}`, `DELETE /exams/{id}`: exam CRUD with BR-003 (published exams immutable, forward-only status transitions via `PUT`'s optional `status` field) and BR-001 (correct-answer/grading data hidden from Students until `exam.status = published`, always visible to the creating Teacher)
- `POST /exams/{id}/start` (Derived Engineering Addition, confirmed with the user): Student begins an exam attempt, recording `started_at` from the server clock only — idempotent (returns the existing `in_progress` submission unchanged on a second call), required for VR-004 to be genuinely enforceable server-side
- `POST /exams/{id}/submit`: Student submits answers; VR-004 (time limit) computed entirely server-side from the stored `started_at`, never a client timestamp
- `POST /exams/{id}/grade`: Teacher grades a submission; VR-006 (`awarded_marks` cannot exceed a question's max marks) validated for the whole batch before any write; grading is re-saveable (upsert per answer), `exam_submission.status` becomes `graded` only once every answer has a `question_grade`
- `GET /exams/{id}/submissions/{submission_id}` (Derived Engineering Addition, confirmed with the user): Teacher(creator)/Admin-only endpoint returning a submission's questions in order with each answer and any existing grading — added because `POST /exams/{id}/grade` needs `answer_id` values but nothing else exposed a submission's actual answer content, and `GET /exams/{id}/results` is deliberately aggregate-only reporting
- `GET /exams/{id}/results`: Teacher/Admin aggregate per-submission totals
- Frontend: `features/exams/index.ts` (React Query hooks for all 9 endpoints), `pages/ExamList/index.tsx` (role-scoped table with Class/Status filters), `pages/ExamRoom/index.tsx` (timed exam-taking interface — server-recorded countdown, question navigator, MCQ/free-text inputs, confirmation-gated submit, timer-expiry auto-submit), `pages/Teacher/ExamBuilder/index.tsx` (question/option editor, Save Draft vs. Publish Exam), `pages/Teacher/GradingInterface/index.tsx` (per-question marks/feedback, Save Grades, Publish Exam once fully graded)
- Backend test suite: `tests/unit/test_exam_service.py`, `tests/unit/test_grading_service.py`, `tests/integration/test_exams_router.py` — 77 new tests, 211 total passing

### Changed (Milestone 6 — Documentation)
- `docs/API_Contract.md`: added Section 3.6 `POST /exams/{id}/start` and Section 3.8 `GET /exams/{id}/submissions/{submission_id}` (both Derived Engineering Additions), renumbering `POST /exams/{id}/submit` → 3.7, `POST /exams/{id}/grade` → 3.9, `GET /exams/{id}/results` → 3.10
- `docs/Requirement_Traceability_Matrix.md`: FR-017-FR-025 updated to Verified; corrected FR-025's endpoint/table mapping (was incorrectly pointing at `GET /exams/{id}/results`/the Milestone 7 `result` table; corrected to `GET /exams/{id}` with `exam.status = published` as the BR-001 gate); added notes for both Derived additions and the exam-status-transition/grading-re-save-policy resolutions
- `docs/Proposal_vs_Engineering_Additions.md`: classified both new endpoints as Derived, documenting why each is required and why `GET /exams/{id}/results` was deliberately not extended instead
- `docs/Implementation_Roadmap.md`: added two Milestone 6 scope notes recording both Derived additions and their rationale
- `PROJECT_PROGRESS.md`: Milestone 5's Review Status updated to Approved (user sign-off, git tag `v0.6-milestone5`); Milestone 6 row and full Milestone Detail Log entry added; Summary section updated (58% overall progress, current/last/next milestone, HEAD commit)

### Known Issues (Milestone 6)
- Migration `0007_exams` is hand-authored, not `alembic revision --autogenerate`'d, though its upgrade/downgrade cycle and an autogenerate diff-check are both confirmed clean.
- Frontend UI not visually exercised in a browser this milestone — per the standing instruction not to rely on preview tooling, verification was `tsc`/`npm run build`/code review only.
- Milestone 6 deliberately does not calculate or persist final course results (GPA, transcripts, aggregated per-course marks) — that is explicitly Milestone 7 scope, per this milestone's own kickoff instructions.

### Added (Milestone 5 — Attendance)
- `attendance_record` table (Alembic revision `0006_attendance`), matching `Database_Design.md` §6.22 column-for-column (deliberately no `created_at`/`updated_at` — the schema doesn't call for them), with `UniqueConstraint`/`Index` declared on the model itself so `alembic revision --autogenerate` produced an empty diff on the first attempt
- `POST /attendance`: Teacher marks attendance, enforcing all 10 mandatory Attendance Domain Rules explicitly at the service layer before any write — student exists and is active, class session exists, a schedule entry exists for it, Teacher is assigned to it, student has a valid enrollment, no duplicate record, and the whole batch is validated before any record is created
- `GET /attendance/me`: Student's own attendance summary with a computed `overall_percentage` and `low_attendance_warning` (BR-008, 80% threshold), never cached (NFR-016)
- `GET /attendance/{classId}`: Teacher/Admin class-level view, plus Parent access scoped via `ParentStudentLink` and a required `student_id` — the only endpoint where Parent access to attendance is granted at all
- `PUT /attendance/{id}`: Teacher/Admin correction, same ownership check as marking
- `GET /attendance/reports`: Admin department/semester-scoped percentage summary
- `GET /schedule/class-sessions/{class_session_id}/roster` (Derived Engineering Addition, confirmed with the user): minimal endpoint listing enrolled students for a class session — no endpoint anywhere provided this, and the Teacher: Attendance Marker page's documented roster-preview workflow couldn't function without it
- Frontend: `features/attendance/index.ts`, `pages/Attendance/index.tsx` (percentage bar, warning badge, filters, records table — Calendar view present but not implemented), `pages/Teacher/AttendanceMarker/index.tsx` (roster table, bulk "Mark all present," Save with automatic correction-mode detection)
- Backend test suite: `tests/unit/test_attendance_service.py`, `tests/integration/test_attendance_router.py` — 35 new tests, 134 total passing

### Fixed (Milestone 5)
- A real routing bug: `GET /attendance/reports` was going to be captured by `GET /attendance/{class_id}`'s UUID path parameter (matching `class_id="reports"` and failing validation) since FastAPI matches routes in declaration order — fixed by registering `/reports` before `/{class_id}`, caught during implementation before it ever shipped
- `GET /attendance/{classId}`'s documented response shape (`API_Contract.md` §4.3) had no record `id`, only `student_id`/`date`/`status` — the Teacher: Attendance Marker's correction workflow (`PUT /attendance/{id}`) had no way to resolve which record to correct from that response alone. Added `id` to the response schema and updated `API_Contract.md` in the same change; existing unit tests re-run clean afterward
- `docs/Requirement_Traceability_Matrix.md`'s note claiming Parent-facing attendance access "reuses Student-facing endpoints" was overly broad — FR-032 actually reuses the Teacher/Admin class-based endpoint, not `GET /attendance/me`; narrowed the wording during pre-implementation review

### Changed (Milestone 5 — Documentation)
- `docs/Requirement_Analysis.md`: BR-008/FR-031's previously-undefined low-attendance threshold resolved to 80%, evidenced by two independent "Below 80%" mockups in `UI_Wireframes.md` (§14 item 4); added a new §14 item 17 recording the attendance percentage formula as a documented engineering assumption (`present`+`late` counted, `excused` excluded from the denominator) since no proposal/wireframe evidence exists for this one
- `docs/API_Contract.md`: added Section 7.10 `GET /schedule/class-sessions/{class_session_id}/roster`; annotated `GET /attendance/me`'s response with the computed `low_attendance_warning` field; added `id` to `GET /attendance/{classId}`'s response shape
- `docs/Requirement_Traceability_Matrix.md`: FR-026-FR-032 and NFR-002/NFR-003/NFR-016 updated — FR-031/FR-032 and the three NFRs marked honestly as partially implemented where a later milestone (results, fees, notifications) owns the remainder, not silently marked complete
- `docs/Proposal_vs_Engineering_Additions.md`: classified the roster endpoint as Derived, documenting why it's implemented via the schedule domain rather than attendance
- `docs/Implementation_Roadmap.md`: added a Milestone 5 scope note recording both pre-implementation resolutions and the roster endpoint's addition to M5's API list
- `docs/System_Architecture.md`: added the attendance/roster ownership checks (Teacher-assigned-to-class-session, Parent-via-ParentStudentLink) to Section 6's ownership-check list, which had never enumerated them
- `PROJECT_PROGRESS.md`: Milestone 4's Review Status updated to Approved (user sign-off, git tag `v0.5-milestone4`); Milestone 5 row and full Milestone Detail Log entry added; Summary section updated (50% overall progress, current/last/next milestone, HEAD commit)

### Known Issues (Milestone 5)
- Calendar view on the Student Attendance page is not implemented — Table view is fully functional.
- FR-031/FR-032's notification-dispatch half (instant warnings/absence alerts) is not implemented — depends on the Milestone 9 notification module. The computed indicators themselves are fully implemented and tested.
- The attendance percentage formula is a documented engineering assumption with no proposal/wireframe evidence — flagged for revisit if the institution's actual policy is specified.
- Migration `0006_attendance` is hand-authored, not `alembic revision --autogenerate`'d, though its upgrade/downgrade cycle and an autogenerate diff-check are both confirmed clean.
- Frontend UI not visually exercised in a browser this milestone — per the standing instruction not to rely on preview tooling, verification was `tsc`/`npm run build`/code review only.

### Added (Milestone 4 — Scheduling & Timetable)
- `class_session`, `enrollment`, `schedule_entry`, `schedule_change_request` tables (Alembic revision `0005_scheduling`, corrected from the roadmap's stale `0004_scheduling` filename), matching `Database_Design.md` §6.9-6.13 column-for-column, with `index=True`/`UniqueConstraint`/`Index` declared on the models themselves so `alembic revision --autogenerate` produced an empty diff on the first attempt
- `GET /schedule/me`: Student/Teacher own timetable, scoped via `enrollment`/`teacher_id` respectively
- `POST/PUT/DELETE /schedule`: Admin schedule-entry management, with VR-007 (start before end) and BR-005 (no double-booking) enforced on both create and update — conflict detection is a genuine interval-overlap query (`existing.start < new.end AND new.start < existing.end`), not just the DB-level exact-duplicate `UniqueConstraint`, so two bookings with different `start_time` values that still overlap are correctly caught
- `GET /schedule/conflicts`: computes all overlapping room/teacher pairs across the current schedule state
- `POST /schedule/change-requests` / `POST /schedule/change-requests/{id}/resolve`: Teacher-submit/Admin-resolve schedule change workflow (BR-004 — a Teacher may only request a change to their own schedule entry; approving re-validates VR-007/BR-005 against the requested new time before applying it)
- `POST /schedule/class-sessions`, `POST /schedule/enrollments` (Derived Engineering Additions, confirmed with the user): minimal Admin-only creation endpoints for two tables referenced as foreign keys throughout Scheduling/Exams/Attendance but with no creation endpoint anywhere in the source documents — without them, `POST /schedule` could not be exercised at all
- Frontend: `features/schedule/index.ts` (React Query hooks for all schedule endpoints), `pages/Timetable/index.tsx` (role-branched: Student/Teacher read-only weekly grid with a Teacher-only "Request Change" action per cell; Admin schedule-management panel)
- Backend test suite: `tests/unit/test_schedule_service.py`, `tests/integration/test_schedule_router.py` — 27 new tests, 99 total passing

### Fixed (Milestone 4)
- `make_department()`'s fixed default name/code in `tests/conftest.py` collided when a single test called two fixtures that each independently created a department (same class of test-isolation bug found once in Milestone 3) — fixed by making the fixture generate a unique department by default; no application code affected

### Changed (Milestone 4 — Documentation)
- `docs/Implementation_Roadmap.md`: fixed the systemic migration-filename off-by-one across every milestone entry — M1's entry was still wrong after two reactive fixes for M2/M3, and M4-M9 all had the same bug; migrations now read `0002` (M1) through `0010` (M9), matching the actual sequential numbering Alembic requires. Added the two schedule-change-request endpoints to M4's API list (already scoped to M4 by `API_Contract.md`'s own text, but omitted from the roadmap's bullet list). Added a Milestone 4 scope note for the two new Derived endpoints, confirmed with the user.
- `docs/Requirement_Traceability_Matrix.md`: corrected a note that incorrectly grouped FR-050 (schedule-change-request) with the Milestone 9 notification gaps — the correct owner is Milestone 4, per `API_Contract.md`'s own endpoint-level text and `schedule_change_request.py` being an M4 file. FR-045-FR-050 and NFR-015 updated to Verified; FR-051 left honestly `Pending` (the `notification` module doesn't exist until Milestone 9).
- `docs/API_Contract.md`: added Section 7.8 `POST /schedule/class-sessions` and 7.9 `POST /schedule/enrollments`.
- `docs/Proposal_vs_Engineering_Additions.md`: classified both new endpoints as Derived, documenting why minimal Admin-only create was chosen over Milestone 3's seed-only precedent (these two are load-bearing for M4's own deliverables, not a deferrable feature).
- `PROJECT_PROGRESS.md`: Milestone 3's Review Status updated to Approved (user sign-off, git tag `v0.4-milestone3`); Milestone 4 row and full Milestone Detail Log entry added; Summary section updated (42% overall progress, current/last/next milestone, HEAD commit).

### Known Issues (Milestone 4)
- The Admin panel's `class_session_id` fields are raw UUID text inputs, not dropdowns — no `GET /schedule/class-sessions` list endpoint exists, since the Derived endpoints approved for this milestone were deliberately scoped to create-only.
- FR-051 (instant schedule-change notifications) is not implemented — depends on the Milestone 9 notification module.
- Migration `0005_scheduling` is hand-authored, not `alembic revision --autogenerate`'d, though its upgrade/downgrade cycle and an autogenerate diff-check are both confirmed clean.
- Frontend UI not visually exercised in a browser this milestone — per the standing instruction not to rely on preview tooling, verification was `tsc`/`npm run build`/code review only.

### Added (Milestone 3 — User Management & Profiles)
- `student`, `teacher`, `parent`, `admin`, `parent_student_link` tables (Alembic revision `0004_role_profiles`, corrected from the roadmap's stale `0003_role_profiles` filename — `0003` was already consumed by Milestone 2), matching `Database_Design.md` §6.2-6.6 column-for-column, with `index=True`/`UniqueConstraint` declared on the models themselves so `alembic revision --autogenerate` stayed clean on the first attempt (applying the Milestone 2 review's finding proactively this time)
- `GET /users/me` / `PUT /users/me`: self-service profile retrieval/update, merged with role-specific fields (Student/Teacher/Parent/Admin), VR-009 (role/`is_active`/`department_id` cannot be edited via this endpoint) enforced structurally by the request schema having no such field, not just a runtime check
- Admin-driven Student account lifecycle: `GET/POST /users/students`, `GET/PUT/DELETE /users/students/{id}` (Admin+Teacher read, Admin write, per `API_Contract.md` §2.3-2.7); `user` + `student` rows created in a single atomic transaction so a duplicate-email failure never orphans either row
- Admin-driven Teacher account management: `GET/POST /users/teachers`, `PUT /users/teachers/{id}` (Admin-only for both read and write, narrower than `/users/students`, per `API_Contract.md` §2.8-2.10)
- `backend/scripts/seed_admin.py`: bootstraps the first Admin account from process-level environment variables, idempotent, verified via the bare `python -m scripts.seed_admin` invocation
- Frontend: `features/users/index.ts` (React Query hooks for `/users/me` and Student/Teacher CRUD), `features/departments/index.ts` (new — thin wrapper around the existing Milestone 1 `GET /departments` endpoint, needed for the Admin page's department selector; logged in `Proposal_vs_Engineering_Additions.md`), `pages/Profile/index.tsx` (personal-info form + Change Password form reusing the existing Milestone 2 `useChangePassword()` hook), `pages/Admin/UserManagement/index.tsx` (Students/Teachers tab toggle, department filter, create/edit modals, deactivate/reactivate with confirmation)
- Backend test suite: `tests/unit/test_user_service.py` (repository-stubbed) and `tests/integration/test_users_router.py` (disposable-database, full RBAC + lifecycle coverage) — 49 new tests, 72 total passing

### Fixed (Milestone 3)
- `backend/pyproject.toml` still listed `passlib[bcrypt]` and was missing `email-validator`, having drifted out of sync with `requirements.txt` since Milestone 2's passlib removal despite the file's own header comment claiming it's "kept in sync" — found during this milestone's pre-implementation review, corrected in the same commit as the M3 work that surfaced it

### Changed (Milestone 3 — Documentation)
- `docs/Implementation_Roadmap.md`: corrected Milestone 3's migration filename (`0003_role_profiles.py` → `0004_role_profiles.py`, the same class of stale-reference issue already fixed once for Milestone 2's own migration) and the `schemas/user_profile.py` reference (Milestone 0 had actually scaffolded this placeholder as `schemas/user.py`); added a Milestone 3 scope note (confirmed with the user before implementation) that Parent account creation/linking and invite-based password provisioning are out of scope for this milestone — no endpoint, seed data, or invite mechanism exists in the proposal, the API contract, or the codebase for either
- `docs/Requirement_Traceability_Matrix.md`: FR-006-FR-016 Testing/Implementation/Verification Status columns updated; FR-008 left honestly `Pending` with an explanatory note, since `GET /users/me`'s actual contracted response has no academic-history fields and the underlying `enrollment`/`result` tables don't exist until later milestones
- `docs/Proposal_vs_Engineering_Additions.md`: added the `features/departments/index.ts` Derived-addition entry
- `PROJECT_PROGRESS.md`: Milestone 2's Review Status updated to Approved (per explicit user sign-off, git tag `v0.3-milestone2`); Milestone 3 row and full Milestone Detail Log entry added; Summary section updated (33% overall progress, current/last/next milestone, HEAD commit)

### Known Issues (Milestone 3)
- The Profile and Admin: User Management frontend pages have not been visually exercised in a browser this milestone — per this milestone's explicit environment-safety instructions, the preview tooling (subject of the prior milestone's `.env`-drift audit) was not used; verification was limited to `tsc --noEmit`, `npm run build`, and manual code review.
- FR-008 (student academic history via `GET /users/me`) is not deliverable by the endpoint as actually contracted — see the RTM note above.
- Migration `0004_role_profiles` is hand-authored, not `alembic revision --autogenerate`'d, though its upgrade/downgrade cycle and an autogenerate diff-check are both confirmed clean.
- Parent account creation/linking and invite-based provisioning remain explicitly unimplemented — a deliberate scope decision confirmed with the user, not a silently dropped requirement.

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
- `User.is_active` declared only a Python-side `default=True` while its migration declared a DB-level `server_default=sa.true()` — the two representations of the same column had silently diverged (Alembic doesn't compare `server_default` by default, so this never surfaced as an autogenerate diff). Added `server_default=true()` to the model so it matches the migration; both defaults are kept, each serving a different purpose (ORM pre-flush value vs. raw-`INSERT` fallback)
- `alembic revision --autogenerate` was logging `Detected removed index` for `ix_course_department_id` and `ix_user_role` — both indexes exist in the database (created via explicit `op.create_index()` in the hand-written migrations) but weren't declared on the corresponding model columns, so the ORM metadata didn't fully represent the live schema. Added `index=True` to `Course.department_id` and `User.role` (both already required by `Database_Design.md` §9); re-verified `alembic revision --autogenerate` now produces a genuinely empty migration

### Changed (Milestone 2 — Documentation)
- `docs/Database_Design.md` §6.1 (`user` table): added `current_refresh_token_jti`/`refresh_token_expires_at` columns and the "Milestone 2 design note" explaining the single-active-session-per-user design, as part of resolving the refresh-token storage gap the original design had left open
- `docs/API_Contract.md` §1.2/§1.3 (refresh/logout): removed "if tracked separately" hedge language and referenced the resolved `user` table columns directly, now that the storage mechanism is decided; §10 (Reference Data, added in Milestone 1) updated across all 12 entries to remove "Deferred to M2" language and record the actual enforced roles (any authenticated role for GET, Admin for POST) plus 401/403 status codes, now that the RBAC retrofit is complete
- `docs/Proposal_vs_Engineering_Additions.md`: added the "Milestone 2 Schema Addition" entry for the two new `user` columns (classified Derived, permanent); updated the Reference Data CRUD entry's "Auth note" to mark the RBAC retrofit resolved
- `docs/Requirement_Traceability_Matrix.md`: FR-001–FR-005 and NFR-001/NFR-004 Testing/Implementation/Verification Status columns updated from Pending to their actual Milestone 2 status
- `docs/Implementation_Roadmap.md`: fixed M2's migration filename reference (`0002_user.py` → `0003_user.py`, since `0002` was already consumed by Milestone 1); added `backend/app/repositories/user_repository.py` to M2's file list (not originally enumerated, same precedent as Milestone 1's repository); added a Milestone 2 scope note clarifying that `rbac.py`'s "role + ownership check dependency" wording describes the milestone's role in the overall dependency chain, not something M2 itself delivers — M2 has no `/me`-scoped or parent-linked endpoints yet, so ownership checks are deferred to whichever future milestone (M3+) first introduces an ownership-scoped resource, per `CLAUDE.md` §6
- `PROJECT_PROGRESS.md`: Milestone 1's Review Status updated to Approved (per explicit user sign-off at Milestone 2 kickoff); Milestone 2 row and full Milestone Detail Log entry added; Summary section (Overall Progress, Current/Last/Next Milestone, Current Git Commit) updated

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
