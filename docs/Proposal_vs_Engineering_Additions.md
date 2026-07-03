# Proposal vs. Engineering Additions
## University Management System (ICT Education) — REST API

**Source inputs:** `docs/product_proposal.pdf` §3–§7, `docs/API_Contract.md`, `docs/UI_Wireframes.md`, `docs/Requirement_Analysis.md` §14
**Purpose:** A single, explicit ledger of every endpoint **and, per the Milestone 0 proposal-traceability review, every frontend addition** that does **not** appear in the proposal itself, so implementation starts with — and stays on — a clear line between what the client (ICT Bangladesh) asked for and what this project added to make that request buildable or verifiable. Extended beyond API endpoints on 2026-07-03 after a traceability check found two undocumented frontend additions (see "Frontend / UI Engineering Decisions" below).
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

## Additional Items Identified But Not Yet Formally Specified

Two further categories of engineering-necessary endpoints were noted in `Implementation_Roadmap.md` (Milestones 0–1) but have **not** been written up as formal entries in `API_Contract.md`. They are surfaced here for completeness and correct classification, since they are also absent from the proposal's §6 table:

### Reference data CRUD (Department, Course, Room, Semester)
**Classification: Derived.** The proposal never names these as endpoints, and never even fully names them as standalone entities — but Required features cannot function without them: `POST /users/students` needs a `department_id` to reference, `POST /schedule` needs a `room_id`, `POST /fees` needs a `semester_id`, and so on. These are pure plumbing, logically unavoidable given the Required features that depend on them. **Action:** formalize as a "Reference Data" section in `API_Contract.md` before Milestone 1 begins.

### `GET /health`
**Classification: Design Enhancement.** A liveness-check endpoint has no proposal linkage whatsoever — it exists purely to verify deployment wiring (`Implementation_Roadmap.md` Milestone 0). It is the one item in this entire document that is pure engineering convenience with zero traceability to any proposal sentence, direct or indirect.

These two items are noted rather than fully specified here because doing so is outside this document's original stated purpose (reviewing what's already in `API_Contract.md`); they should be added to `API_Contract.md` as their own entries before implementation reaches the milestone that needs them.

---

## Frontend / UI Engineering Decisions (Not API Endpoints)

Found during the Milestone 0 proposal-traceability review: two frontend elements shipped in Milestone 0 with no corresponding proposal sentence and no wireframe in `docs/UI_Wireframes.md`. Both were explicitly requested in the Milestone 0 implementation prompt ("Theme support," "Health API connectivity test") — they are authorized, not silently invented — but per the same traceability rule applied to endpoints above, they still need to be logged rather than left undocumented.

### Light/dark theme toggle
**Where:** `frontend/src/app/ThemeProvider.tsx`, toggle button in `frontend/src/components/AppLayout.tsx`.
**Classification: Design Enhancement.** No proposal sentence, feature-list row, or wireframe mentions a theme/dark-mode capability anywhere. It exists purely as a Milestone 0 foundation task (project-setup conventions), not a business requirement — zero proposal linkage, direct or indirect.
**Disposition:** Keep. It's inert with respect to every other requirement (doesn't touch data, auth, or any FR-mapped flow) and low-risk to carry forward. If a future UI pass wants pixel-exact parity with `UI_Wireframes.md`'s ASCII layouts, note that none of those wireframes depict a theme toggle in the header — reconcile at that time rather than removing a working, harmless feature now.

### Dashboard "Backend connectivity" health widget
**Where:** `frontend/src/pages/Dashboard/index.tsx`, calls `useHealthCheck()` (`frontend/src/lib/useHealthCheck.ts`).
**Classification: Design Enhancement**, paired with the already-logged `GET /health` endpoint above (same rationale: verifies deployment wiring, zero proposal linkage).
**Disposition:** Temporary, not permanent. `docs/UI_Wireframes.md`'s Dashboard wireframe (page 2) specifies Upcoming Exams / Attendance % / Fee Status / Recent Results widgets — none of which is a connectivity debug panel. This widget exists only because Milestone 0 has no business data yet to populate the real widgets. **Action:** remove the health-check widget from `Dashboard/index.tsx` when Milestone 10 (Dashboards & Reporting) implements the real widgets from `UI_Wireframes.md`, so the page converges on the approved wireframe rather than accumulating debug UI permanently. Track this removal in `PROJECT_PROGRESS.md`'s M10 Notes.
