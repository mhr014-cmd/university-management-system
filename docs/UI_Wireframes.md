# UI Wireframes
## University Management System (ICT Education)

**Source inputs:** `docs/Requirement_Analysis.md` §7 (Required Pages), §5 (Permissions), `docs/API_Contract.md`, `docs/System_Architecture.md` §3
**Format:** Text/markdown wireframes only (ASCII box layout). No images, no React/JSX code — layout description only.

All 18 pages from `Requirement_Analysis.md` §7 are covered below, in the same order (17 from the original proposal-derived list, plus 1 gap-fill page — Admin: Reports — added during the Project Readiness Audit to close the Reporting feature's screen gap; see `Requirement_Analysis.md` §14 item 15).

---

## 1. Login

### Purpose
Authenticate a user and route them to their role-specific Dashboard (FR-001, FR-005).

### Wireframe
```
┌──────────────────────────────────────────────┐
│                  [ICT Education]                │
│                                                  │
│              ┌────────────────────┐            │
│              │   Sign in            │            │
│              │                      │            │
│              │  Email                │            │
│              │  [______________]     │            │
│              │                        │            │
│              │  Password              │            │
│              │  [______________] [👁] │            │
│              │                        │            │
│              │  ( ) Remember me       │            │
│              │                        │            │
│              │  [    Log In    ]      │            │
│              │                        │            │
│              │  ⚠ error message area  │            │
│              └────────────────────┘            │
└──────────────────────────────────────────────┘
```

### Components
- App logo/name header
- Centered auth card
- Inline error banner (shown on 401/403 from `POST /auth/login`)

### Buttons
- **Log In** (primary, submits form) — disabled while request in flight
- Show/hide password toggle (icon button, non-form-submitting)

### Tables
None.

### Forms
- Email field (text input)
- Password field (masked input)
- "Remember me" checkbox (controls refresh-token persistence duration, client-side only)

### Validation
- Email: required, must match a valid email pattern (VR-001) — inline error on blur.
- Password: required, non-empty — inline error on blur.
- Submit disabled until both fields pass client-side checks.
- Server error (401 invalid credentials, 403 deactivated account) surfaces as a single banner above the form, not tied to a specific field.

### Navigation
- On success: redirect to `/dashboard` (role resolved from login response) — FR-005.
- No navigation elements to other pages (this is the unauthenticated entry point).

### Role Visibility
- Public — no authentication required to view; the only role-aware behavior is the post-login redirect target.

### Responsive Behaviour
- **Desktop:** centered card, fixed width ~400px, vertically centered in viewport.
- **Mobile:** card expands to full width minus 16px gutters; logo shrinks; no layout reflow needed since it's already single-column.

---

## 2. Dashboard

### Purpose
Role-specific home screen showing summary widgets: upcoming exams, attendance %, fee status, recent results (per `Requirement_Analysis.md` §7).

### Wireframe
```
┌──────────────────────────────────────────────────────┐
│ [Logo]   Dashboard  Profile  Exams  Attendance ... [🔔][👤]│
├──────────────────────────────────────────────────────┤
│  Welcome back, {first_name}                             │
│                                                            │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐  │
│  │ Upcoming Exams  │ │ Attendance %    │ │ Fee Status      │  │
│  │ • Exam A  Jul 5  │ │   [87%]  ▓▓▓▓▓░ │ │ Due: 5,000 BDT   │  │
│  │ • Exam B  Jul 9  │ │ Low-attendance? │ │ [View Fee Centre]│  │
│  │ [View all]       │ │   warning badge │ │                  │  │
│  └───────────────┘ └───────────────┘ └───────────────┘  │
│                                                            │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Recent Results                                       │  │
│  │  Course      Grade   Semester                        │  │
│  │  ─────────────────────────────                        │  │
│  │  DB Systems   A       Spring 2026                     │  │
│  │  [View full results]                                  │  │
│  └───────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

### Components
- Top navigation bar (role-composed links, notification bell, avatar/profile menu)
- Widget cards: Upcoming Exams, Attendance %, Fee Status (Student/Parent only), Recent Results
- Admin/Teacher variants replace widgets with: pending approvals count (Admin), classes-today list (Teacher)

### Buttons
- "View all" (per widget, links to the relevant full page)
- "View Fee Centre" / "View full results" (navigation buttons)

### Tables
- Recent Results mini-table (Course, Grade, Semester) — top 3–5 rows only, not paginated (full list lives on Results view).

### Forms
None — read-only summary screen.

### Validation
Not applicable (no user input beyond navigation clicks).

### Navigation
- Top nav bar links to: Profile, Exam list, Attendance, Timetable, Fee centre, Notifications — items shown vary by role (see Role Visibility).
- Widget "View all"/"View X" buttons deep-link to the corresponding full page.

### Role Visibility
- **Student:** Upcoming Exams, Attendance %, Fee Status, Recent Results widgets.
- **Teacher:** Classes Today, Pending Grading count — no Fee Status widget. Schedule-change-request status is **not implemented** (see Milestone 10 Known Limitation note below).
- **Admin:** Pending Result Approvals count, Overdue Fees count, Recent User Signups — links to Admin screens.
- **Parent:** Fee Status and Recent Results widgets only, scoped to the linked child (with a child-selector if multiple children are linked, per `Requirement_Analysis.md` §14 item 2). Upcoming Exams and Attendance % render an honest **"Not available"** state (see Milestone 10 Known Limitation note below) rather than fabricated data.

### Known Limitations (Milestone 10)
- **Teacher Schedule-change-request status widget — omitted.** No endpoint exists (or was added) to query "my pending schedule-change-request status" for the calling Teacher; `schedule_change_request` rows are only ever read via the Admin-facing resolve flow (`API_Contract.md` §1/§2). Resolved as approved Finding C during Milestone 10 pre-implementation review: rather than inventing an undocumented endpoint, this widget is omitted from the Teacher Dashboard. A Teacher's own pending requests remain visible via the Schedule page itself.
- **Teacher Pending Grading widget — computed client-side.** No dedicated backend aggregate endpoint was added for this count (approved Finding B); the frontend derives it from the existing per-exam submission/grading endpoints already used by the Exam Room / grading pages, so no backend scope was expanded for a single dashboard number.
- **Parent Dashboard — Attendance % and Upcoming Exams unavailable.** No endpoint exists exposing a linked child's attendance percentage or upcoming-exam schedule to the Parent role (`GET /attendance/reports` is Admin-only per `API_Contract.md` §4.5; Student's own `/attendance/me`-equivalent and exam-list endpoints are Student/Teacher-scoped, not Parent-linked). Resolved as approved Finding E: the Parent Dashboard implements only Fee Status and Recent Results (both already Parent-accessible via `GET /fees/me` and `GET /results/me` with `student_id`), and renders an honest "Not available" state for the two widgets it cannot back with real data, rather than fabricating figures or adding an undocumented Parent-scoped endpoint.
- **Admin Dashboard — Recent User Signups now backed by `created_at`.** Approved Finding D added an additive `created_at` field to the existing `GET /users/students` and `GET /users/teachers` response DTOs (see `API_Contract.md` §2.3) so this widget can be populated from real data without a new endpoint or schema change.

### Responsive Behaviour
- **Desktop:** widgets in a 3-column grid.
- **Tablet:** widgets reflow to 2-column grid.
- **Mobile:** widgets stack single-column; top nav collapses into a hamburger menu; notification bell and avatar remain visible in the header.

---

## 3. Profile Page

### Purpose
View and edit personal details, profile photo, and password (FR-006, FR-007, FR-004).

### Wireframe
```
┌──────────────────────────────────────────────┐
│ [Logo]  ... nav ...                    [🔔][👤]│
├──────────────────────────────────────────────┤
│  Profile                                        │
│                                                  │
│  ┌────────┐   First Name  [______________]     │
│  │ [photo] │   Last Name   [______________]     │
│  │ [Change]│   Email       (read-only)           │
│  └────────┘   Department   (read-only, if any)   │
│                                                    │
│               [    Save Changes    ]              │
│                                                    │
│  ──────────────────────────────────────────      │
│  Change Password                                   │
│  Current Password [________________]               │
│  New Password      [________________]               │
│  Confirm Password  [________________]               │
│               [   Update Password   ]               │
└──────────────────────────────────────────────┘
```

### Components
- Profile photo thumbnail + "Change" upload trigger
- Personal-info form section
- Separate "Change Password" form section

### Buttons
- **Save Changes** (submits `PUT /users/me`)
- **Change** (photo upload trigger, opens file picker)
- **Update Password** (submits `PUT /auth/password`)

### Tables
None.

### Forms
- Personal info: First Name, Last Name (editable); Email, Department, Role (read-only, per VR-009)
- Password change: Current Password, New Password, Confirm Password

### Validation
- First/Last Name: required, non-empty.
- Photo upload: file type restricted to image formats, size limit (client-side pre-check before upload).
- New Password vs Confirm Password: must match (client-side check before submit).
- New Password: must differ from Current Password, must meet complexity policy (VR-002) — inline error from server response if policy fails.
- Read-only fields are rendered disabled and never included in the `PUT /users/me` payload (VR-009 enforced client-side as UX, server-side as the real gate).

### Navigation
- Reached via top nav "Profile" link or avatar menu, from any authenticated page.
- No further downstream navigation from this page besides Save/Update actions (which stay on-page with a success toast).

### Role Visibility
- All roles see this page with identical layout; the Department field only renders for Student/Teacher (not Parent/Admin, who have no `department_id`).

### Responsive Behaviour
- **Desktop:** two-column layout (photo left, form fields right).
- **Mobile:** single column — photo/upload control stacks above the form fields; password section stacks below.

---

## 4. Exam List

### Purpose
Upcoming and past exams with status badges (FR-017, FR-019).

### Wireframe
```
┌──────────────────────────────────────────────┐
│ [Logo] ... nav ...                     [🔔][👤]│
├──────────────────────────────────────────────┤
│  Exams              [Filter: Class ▾] [Status ▾]│
│                                                  │
│  ┌────────────────────────────────────────┐    │
│  │ Title        Class      Status    Date   │    │
│  │ ──────────────────────────────────────   │    │
│  │ Midterm 1    DB Systems [Open]    Jul 5  →│    │
│  │ Quiz 2       Networks   [Graded]  Jun 28 →│    │
│  │ Final Exam   DB Systems [Scheduled]Jul 20→│    │
│  └────────────────────────────────────────┘    │
│                          [◀ Prev]  [Next ▶]       │
└──────────────────────────────────────────────┘
```

### Components
- Filter dropdowns: Class/Course, Status
- Exam table with status badges (scheduled, open, graded, published — per `Requirement_Analysis.md` §7). "Graded" is a **derived display label**, not the literal `exam.status` value — it is shown when `exam.status = closed` AND every submission for that exam has been fully graded (see `Database_Design.md` §6.14 terminology note); "Draft" exams are never shown on the Student-facing list.
- Pagination controls

### Buttons
- Row click / "→" affordance navigates to Exam Room (if open, Student) or exam detail (Teacher/Admin read view)
- Prev/Next pagination buttons

### Tables
- **Exams table**: columns Title, Class, Status, Date. Row click navigates; no inline row actions on this list screen.

### Forms
None (filters are dropdowns, not a submitted form).

### Validation
Not applicable — read-only list with filter state only.

### Navigation
- Row click → Exam Room (Student, only if `status = open`) or exam detail/read view (Teacher/Admin).
- Reached from Dashboard "View all" (Upcoming Exams widget) or top nav "Exams" link.

### Role Visibility
- **Student:** exams for their enrolled classes only; "Open" exams are clickable into Exam Room, "Scheduled"/"Graded"/"Published" are view-only.
- **Teacher:** exams they created; row click leads to Exam Builder (edit mode) or Grading Interface depending on status.
- **Admin:** all exams, read-only, for oversight.

### Responsive Behaviour
- **Desktop:** full table with all columns visible.
- **Mobile:** table collapses into a stacked card list — one card per exam (Title + Status badge on top row, Class + Date on second row), same tap targets.

---

## 5. Exam Room

### Purpose
Timed exam-taking interface supporting MCQ, written, and coding question formats (FR-022).

### Wireframe
```
┌──────────────────────────────────────────────┐
│  Midterm 1 — DB Systems        ⏱ 42:17 remaining│
├──────────────────────────────────────────────┤
│  Question 3 of 10                    [5 marks]  │
│                                                  │
│  What normal form removes transitive             │
│  dependencies?                                    │
│                                                    │
│  ( ) 1NF                                          │
│  ( ) 2NF                                          │
│  (•) 3NF                                          │
│  ( ) BCNF                                         │
│                                                    │
│  ── OR (written/coding types) ──                  │
│  [ multi-line answer / code editor textarea    ]  │
│  [                                              ]  │
│                                                    │
│  [◀ Previous]     [1][2][3•][4]...[10]  [Next ▶]  │
│                                                    │
│                          [    Submit Exam    ]     │
└──────────────────────────────────────────────┘
```

### Components
- Persistent countdown timer (derived from `exam.time_limit_minutes` and submission `started_at`)
- Question navigator (numbered jump list, current question highlighted, answered questions marked)
- Question body: MCQ radio group, or textarea (written), or code-editor-style textarea (coding)
- Marks-per-question indicator

### Buttons
- **Previous / Next** (navigate between questions, autosaves current answer locally)
- Question number jump buttons
- **Submit Exam** (final action, triggers confirmation dialog before calling `POST /exams/{id}/submit`)

### Tables
None.

### Forms
- One answer field per question (radio group for MCQ, textarea for written/coding) — the exam as a whole is one large form submitted at the end.

### Validation
- Timer expiry auto-submits whatever answers are currently filled (client-enforced countdown, server re-validates elapsed time per VR-004).
- Submit button shows a warning if any questions are unanswered, but does not block submission (partial submissions allowed unless the business rules dictate otherwise — flagged as an implementation decision).
- Confirmation dialog ("Are you sure? This cannot be undone") before final submit, given exam submissions are one-time only (FR-022, `exam_submission` uniqueness).

### Navigation
- Entered only from Exam List (row click on an `open` exam) — no direct URL access without that context in normal flow.
- On submit success: redirect to Exam List with a "Submitted" confirmation toast; cannot navigate back into the same exam room afterward.
- Browser back/refresh during an active exam should warn before leaving (unsaved-changes-style guard).

### Role Visibility
- **Student only.** Not accessible to Teacher/Admin/Parent — attempting to load this page as another role returns a 403 from the underlying API and the UI redirects to Dashboard.

### Responsive Behaviour
- **Desktop:** two-region layout — question navigator as a persistent sidebar, question body in the main area.
- **Mobile:** question navigator collapses into a horizontally scrollable strip above the question body; timer remains pinned to the top of the viewport at all times.

---

## 6. Results View

### Purpose
Per-subject grades, GPA, semester selector, transcript PDF download (FR-033, FR-036).

### Wireframe
```
┌──────────────────────────────────────────────┐
│ [Logo] ... nav ...                     [🔔][👤]│
├──────────────────────────────────────────────┤
│  Results        Semester: [Spring 2026 ▾]        │
│                                                  │
│  GPA this semester: 3.72                          │
│                                                    │
│  ┌────────────────────────────────────────┐      │
│  │ Course          Grade   GPA Points        │      │
│  │ ──────────────────────────────────────    │      │
│  │ DB Systems       A       4.0               │      │
│  │ Networks         B+      3.3               │      │
│  │ Software Eng.    A-      3.7                │      │
│  └────────────────────────────────────────┘      │
│                                                    │
│               [   Download Transcript (PDF)   ]    │
└──────────────────────────────────────────────┘
```

### Components
- Semester selector dropdown
- GPA summary line
- Results table

### Buttons
- **Download Transcript (PDF)** (calls `GET /results/{studentId}/transcript`)

### Tables
- **Results table**: columns Course, Grade Letter, Grade Points. One row per course in the selected semester.

### Forms
None — semester selector is the only input, not a submitted form.

### Validation
Not applicable (read-only); Download button disabled if no published results exist yet for the student (per BR-002).

### Navigation
- Reached from Dashboard "View full results" or top nav.
- No further drill-down beyond this page (transcript opens/downloads as a file, doesn't navigate away).

### Role Visibility
- **Student:** own results only, only `published` rows visible (BR-002).
- **Parent:** same layout, scoped to linked child, with a child selector if multiple children (reused per `Requirement_Analysis.md` §14 item 2 — see Page 17).
- **Admin:** can reach an equivalent read-only view per student via Admin: user management (not a separate top-level page).

### Responsive Behaviour
- **Desktop:** table with all 3 columns visible side by side.
- **Mobile:** table becomes a stacked card list, one card per course (Course name as heading, Grade + GPA points below); semester selector and GPA summary remain full-width above.

---

## 7. Attendance Page

### Purpose
Calendar or table view of attendance records with percentage indicator (FR-026).

### Wireframe
```
┌──────────────────────────────────────────────┐
│ [Logo] ... nav ...                     [🔔][👤]│
├──────────────────────────────────────────────┤
│  Attendance     [Table view] [Calendar view]      │
│  Class: [All ▾]   Date range: [___] to [___]       │
│                                                    │
│  Overall: 87%  ▓▓▓▓▓▓▓▓▓░  ⚠ Below 80% in Networks │
│                                                    │
│  ┌────────────────────────────────────────┐      │
│  │ Date        Class        Status           │      │
│  │ ──────────────────────────────────────    │      │
│  │ Jul 1       DB Systems   Present            │      │
│  │ Jun 30      Networks     Absent              │      │
│  │ Jun 29      DB Systems   Present              │      │
│  └────────────────────────────────────────┘      │
└──────────────────────────────────────────────┘
```

### Components
- View toggle (Table / Calendar)
- Class filter dropdown, date range filter
- Overall percentage bar with low-attendance warning badge (BR-008)
- Attendance records table (or calendar grid in Calendar view)

### Buttons
- Table/Calendar view toggle (segmented control)
- No mutating actions — Student view is entirely read-only

### Tables
- **Attendance records table**: columns Date, Class, Status (present/absent/late/excused).

### Forms
- Filter controls only (class dropdown, date range pickers) — not a submitted form, applies live via query params to `GET /attendance/me`.

### Validation
- Date range: `date_from <= date_to` enforced client-side before the range is applied (mirrors server-side check).

### Navigation
- Reached from Dashboard (Attendance % widget) or top nav.
- No downstream navigation from this page.

### Role Visibility
- **Student:** own attendance only.
- **Parent:** same layout scoped to linked child, reused for Page 17.
- Not applicable to Teacher/Admin (they use Attendance Marker / Reports instead — see Pages 15, 12-adjacent Admin reporting).

### Responsive Behaviour
- **Desktop:** Table view shows full table; Calendar view shows a month grid with color-coded day cells.
- **Mobile:** Table view becomes a stacked list; Calendar view switches to a simplified week-strip rather than a full month grid to fit the viewport.

---

## 8. Fee Centre

### Purpose
Outstanding balance card, payment history table, invoice PDF download (FR-038, FR-042).

### Wireframe
```
┌──────────────────────────────────────────────┐
│ [Logo] ... nav ...                     [🔔][👤]│
├──────────────────────────────────────────────┤
│  Fee Centre                                       │
│                                                    │
│  ┌────────────────────────────┐                  │
│  │ Outstanding Balance           │                  │
│  │      5,000 BDT                │                  │
│  │ Due: Jul 15, 2026              │                  │
│  └────────────────────────────┘                  │
│                                                    │
│  Payment History                                    │
│  ┌────────────────────────────────────────┐      │
│  │ Date        Amount    Method   Invoice     │      │
│  │ ──────────────────────────────────────    │      │
│  │ Jun 1      10,000 BDT  Bank    [Download]  │      │
│  │ Mar 1      10,000 BDT  Bank    [Download]  │      │
│  └────────────────────────────────────────┘      │
└──────────────────────────────────────────────┘
```

### Components
- Outstanding balance summary card, with due date
- Payment history table with per-row invoice download

### Buttons
- **Download** (per row, calls `GET /fees/invoices/{id}`)

### Tables
- **Payment history table**: columns Date, Amount, Method, Invoice (download action).

### Forms
None (Student/Parent view is read-only; payment recording is Admin-only, see Page 12).

### Validation
Not applicable — read-only page.

### Navigation
- Reached from Dashboard "View Fee Centre" widget or top nav.
- No downstream navigation besides file download.

### Role Visibility
- **Student:** own fee data.
- **Parent:** linked child's fee data, with child selector if multiple children.
- Not shown to Teacher. Admin uses the separate Fee Dashboard (Page 12) instead.
- Per `Requirement_Analysis.md`, Fees is an Optional module — this page may be a lower build priority (see `Implementation_Roadmap.md` Milestone 8).

### Responsive Behaviour
- **Desktop:** balance card and table side by side is unnecessary — single column is used at all breakpoints for this page given limited content width, but the table itself uses full available width on desktop.
- **Mobile:** balance card stays full-width at top; payment history becomes a stacked card list (Date/Amount as heading, Method + Download link below).

---

## 9. Timetable

### Purpose
Weekly grid view of class schedule with room and teacher information (FR-045).

### Wireframe
```
┌──────────────────────────────────────────────┐
│ [Logo] ... nav ...                     [🔔][👤]│
├──────────────────────────────────────────────┤
│  Timetable            Week of: [Jul 1 – Jul 5 ▾]   │
│                                                    │
│       Mon        Tue        Wed        Thu    Fri │
│  9AM [DB Sys]   [────]   [DB Sys]    [────]  [Net]│
│      Rm 201               Rm 201              Rm105│
│ 11AM [────]    [Network]  [────]     [Network][────]│
│                Rm 105                 Rm 105        │
└──────────────────────────────────────────────┘
```

### Components
- Week selector (prev/next week navigation)
- Weekly grid: rows = time slots, columns = days, cells = class blocks (Course name, Room, and for Teacher view, Class roster link)
- (Teacher only) "Request Change" button per cell

### Buttons
- Week navigation (◀ Prev Week / Next Week ▶)
- **Request Change** (Teacher only, per schedule entry — opens a small form, see Forms below)

### Tables
- Grid is rendered as a table (days × time slots) rather than a list table.

### Forms
- (Teacher only) Schedule Change Request form: new day/time/room fields, submitted via `POST /schedule/change-requests` — appears in a modal triggered by "Request Change."

### Validation
- (Teacher change request form) VR-007 — start time before end time; required fields for the new slot.

### Navigation
- Reached from Dashboard or top nav "Timetable" link.
- Teacher "Request Change" opens an in-page modal, does not navigate away.

### Role Visibility
- **Student:** own enrolled-class schedule, read-only.
- **Teacher:** own teaching schedule, with "Request Change" action available per cell (BR-004 — cannot edit directly).
- **Admin:** not this page — Admin manages schedules via Admin schedule management (implied within Timetable's admin mode per `Requirement_Traceability_Matrix.md` FR-046–FR-049 note), which adds Create/Edit/Delete controls and a conflict-check button on top of the same grid layout.
- **Parent:** child's timetable, read-only, reused for Page 17.

### Responsive Behaviour
- **Desktop:** full 5-day grid visible at once.
- **Mobile:** grid becomes a single-day view with a day-selector tab strip (Mon/Tue/Wed/Thu/Fri), since a 5-column grid does not fit a narrow viewport.

---

## 10. Admin: User Management

### Purpose
Searchable table of students and teachers with create/edit/deactivate actions (FR-009–FR-016).

### Wireframe
```
┌──────────────────────────────────────────────┐
│ [Logo] ... nav ...                     [🔔][👤]│
├──────────────────────────────────────────────┤
│  User Management     [Students] [Teachers]        │
│  [Search: ____________]  [Dept: All ▾] [+ New]     │
│                                                    │
│  ┌────────────────────────────────────────┐      │
│  │ Name         Email          Dept   Status │      │
│  │ ──────────────────────────────────────    │      │
│  │ A. Rahman    a@x.com        CS    Active [Edit][Deactivate]│
│  │ B. Karim     b@x.com        BBA   Active [Edit][Deactivate]│
│  │ C. Islam     c@x.com        CS    Inactive[Edit][Reactivate]│
│  └────────────────────────────────────────┘      │
│                          [◀ Prev]  [Next ▶]         │
└──────────────────────────────────────────────┘
```

### Components
- Students/Teachers tab toggle
- Search input, department filter
- User table with inline row actions
- "+ New" button opening a create form (modal or side panel)

### Buttons
- **+ New** (opens create-account form)
- **Edit** (per row, opens edit form pre-filled)
- **Deactivate / Reactivate** (per row, toggles `is_active` — confirmation dialog required before deactivating, per the destructive-action pattern)

### Tables
- **User table**: columns Name, Email, Department, Status, Actions. Paginated.

### Forms
- **Create/Edit Account form** (modal): First Name, Last Name, Email, Department, and for create-only: initial Password/invite method.

### Validation
- Email: required, valid format, uniqueness enforced server-side (VR-001, 409 on duplicate surfaced inline on the Email field).
- Department: required selection from existing departments.
- Deactivate action requires an explicit confirmation step ("Are you sure you want to deactivate this account? Historical records will be preserved" — reflecting BR-006).

### Navigation
- Reached from Dashboard (Admin) or top nav "Admin" section.
- Create/Edit forms open as an in-page modal, no separate route.

### Role Visibility
- **Admin only.** Not visible in navigation for any other role.

### Responsive Behaviour
- **Desktop:** full table with all columns and inline action buttons.
- **Mobile:** table becomes a stacked card list; row actions collapse into a "⋮" overflow menu per card to avoid cramped buttons.

---

## 11. Admin: Result Approval

### Purpose
Pending results queue with approve/reject workflow (FR-035, BR-002).

### Wireframe
```
┌──────────────────────────────────────────────┐
│ [Logo] ... nav ...                     [🔔][👤]│
├──────────────────────────────────────────────┤
│  Result Approval        Status: [Submitted ▾]      │
│                                                    │
│  ┌────────────────────────────────────────┐      │
│  │ Exam         Class      Submitted By  Date│      │
│  │ ──────────────────────────────────────    │      │
│  │ Midterm 1    DB Systems  T. Ahmed    Jul 1 [Review]│
│  │ Quiz 2       Networks    S. Karim    Jun 28[Review]│
│  └────────────────────────────────────────┘      │
│                                                    │
│  ── Review panel (on row expand/click) ──          │
│  Student        Grade   Points                     │
│  M. Hasan        A       4.0                        │
│  N. Chowdhury     B+      3.3                        │
│                                                        │
│  Comment (required if reject): [__________________] │
│         [  Approve  ]     [  Reject  ]                │
└──────────────────────────────────────────────┘
```

### Components
- Status filter (Submitted / Approved / Rejected / Published)
- Pending-results queue table
- Expandable/drill-in review panel per exam showing per-student grades

### Buttons
- **Review** (expands/opens the detail panel for one exam's submitted results)
- **Approve** (calls `POST /results/{id}/approve` with `decision: approve`)
- **Reject** (calls the same endpoint with `decision: reject`, requires a comment)

### Tables
- **Queue table**: columns Exam, Class, Submitted By, Date, Actions.
- **Review panel table**: columns Student, Grade, Points — read-only within the review.

### Forms
- Reject comment field (required only when rejecting).

### Validation
- Reject action blocked client-side until the Comment field is non-empty (mirrors server 422 if comment required by policy).
- Approve/Reject buttons disabled while the request is in flight to prevent double-submission.

### Navigation
- Reached from Dashboard (Pending Approvals widget) or top nav "Admin" section.
- Approve/Reject keeps the Admin on this page, removing the resolved item from the queue with a success toast.

### Role Visibility
- **Admin only.**

### Responsive Behaviour
- **Desktop:** queue table and review panel can sit side-by-side (list left, detail right) or stacked, depending on final layout choice; queue table shows all columns.
- **Mobile:** queue becomes a stacked card list; tapping a card opens the review panel as a full-screen view (not a side panel) given limited width.

---

## 12. Admin: Fee Dashboard

### Purpose
Real-time revenue view, overdue list, bulk notice sender (FR-039, FR-040, FR-043, FR-044).

### Wireframe
```
┌──────────────────────────────────────────────┐
│ [Logo] ... nav ...                     [🔔][👤]│
├──────────────────────────────────────────────┤
│  Fee Dashboard                                    │
│                                                    │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐       │
│  │ Collected   │ │ Outstanding │ │ Overdue     │       │
│  │ 1,200,000   │ │  300,000    │ │  25 accounts │       │
│  └───────────┘ └───────────┘ └───────────┘       │
│                                                    │
│  [+ New Fee Structure]  [Record Payment]           │
│                                                    │
│  Overdue Accounts                                   │
│  ┌────────────────────────────────────────┐      │
│  │ Student      Amount Due   Days Overdue     │      │
│  │ ──────────────────────────────────────    │      │
│  │ M. Hasan      5,000 BDT     12    [Notify]  │      │
│  │ N. Chowdhury   3,000 BDT      4    [Notify]  │      │
│  └────────────────────────────────────────┘      │
│                     [  Send Bulk Overdue Notice  ]  │
└──────────────────────────────────────────────┘
```

### Components
- Summary stat cards (Collected, Outstanding, Overdue count)
- Fee structure creation trigger, payment recording trigger
- Overdue accounts table with per-row and bulk notify actions

### Buttons
- **+ New Fee Structure** (opens form, `POST /fees`)
- **Record Payment** (opens form, `POST /fees/payments`)
- **Notify** (per row, calls `POST /fees/overdue/notify` with `scope: "selected"` for that one student — gap-fill endpoint, see `API_Contract.md` §6.7)
- **Send Bulk Overdue Notice** (calls `POST /fees/overdue/notify` with `scope: "all_overdue"`)

### Tables
- **Overdue accounts table**: columns Student, Amount Due, Days Overdue, Actions.

### Forms
- **Fee Structure form**: Department (optional), Semester, Name, Amount, Due Date (VR-008 on Amount).
- **Record Payment form**: Student (search/select), Fee Structure (select), Amount, Payment Date, Method (VR-008 on Amount, overpayment rule per §14 flag).

### Validation
- Amount fields: required, positive numbers only (VR-008), inline error if non-positive or non-numeric.
- Due Date: required, must be a valid future-or-current date for new fee structures.
- Bulk Notify: confirmation dialog before sending, since it affects multiple accounts at once.

### Navigation
- Reached from Dashboard (Admin) or top nav "Admin" section.
- Forms open as modals; no separate routes.

### Role Visibility
- **Admin only.** Entire page/module is Optional per the proposal (`Requirement_Analysis.md` §14 item 1) — build priority is lower than core Admin screens.

### Responsive Behaviour
- **Desktop:** 3-column stat cards, full overdue table.
- **Mobile:** stat cards stack single-column; overdue table becomes a stacked card list with "Notify" as the primary visible action per card.

---

## 13. Teacher: Exam Builder

### Purpose
Question editor with type selector, marks field, hint input, and preview (FR-018, FR-020).

### Wireframe
```
┌──────────────────────────────────────────────┐
│ [Logo] ... nav ...                     [🔔][👤]│
├──────────────────────────────────────────────┤
│  Exam Builder — Midterm 1              [Preview]  │
│  Class: [DB Systems ▾]  Time Limit: [60] min       │
│                                                    │
│  ┌────────────────────────────────────────┐      │
│  │ Q1. Type: [MCQ ▾]   Marks: [5]            │      │
│  │ Question text: [__________________]       │      │
│  │ Options:                                    │      │
│  │  (•) [option A text______] [correct?✓]      │      │
│  │  ( ) [option B text______] [ ]              │      │
│  │  [+ Add option]                              │      │
│  │ Hint (optional): [________________]          │      │
│  │                              [Delete question]│      │
│  └────────────────────────────────────────┘      │
│  [+ Add Question]                                   │
│                                                    │
│         [ Save Draft ]     [ Publish Exam ]          │
└──────────────────────────────────────────────┘
```

### Components
- Exam-level fields: Class selector, Time Limit
- Repeatable question editor blocks (type selector: MCQ/short answer/descriptive/coding, marks, question text, hint, MCQ option sub-editor)
- Preview toggle (renders the exam as a Student would see it, read-only)

### Buttons
- **+ Add Question** / **Delete question** (per block)
- **+ Add option** (MCQ sub-editor)
- **Preview** (toggles preview mode)
- **Save Draft** (calls `POST /exams` or `PUT /exams/{id}`, keeps `status: draft`)
- **Publish Exam** (transitions status, disabled after publication per BR-003)

### Tables
None — question list is a repeatable form block list, not a table.

### Forms
- Full exam + nested questions + nested MCQ options, as described in `POST /exams` request body (`API_Contract.md` §3.2).

### Validation
- Time Limit: required, positive integer (VR-004).
- Each question's Marks: required, positive number (VR-003).
- MCQ questions: at least one option marked correct, at least two options total.
- Publish action disabled until all questions pass validation; a summary of validation errors is shown if Publish is attempted while invalid.
- Once `status = published`, all fields become read-only (BR-003) — Save Draft/Publish buttons are replaced with a "This exam is published and cannot be edited" notice.

### Navigation
- Reached from Exam List (row click, Teacher role) or a "+ New Exam" action on the Exam List page.
- Save Draft keeps the Teacher on this page; Publish redirects to Exam List with a success toast.

### Role Visibility
- **Teacher only**, and only for exams they created.

### Responsive Behaviour
- **Desktop:** question editor blocks at full width with type/marks fields side by side.
- **Mobile:** each question block's fields stack vertically (Type above Marks above Question text); Preview becomes a full-screen overlay instead of a side-by-side view.

---

## 14. Teacher: Grading Interface

### Purpose
Per-student submission view with inline marking and feedback fields (FR-023, FR-024).

### Wireframe
```
┌──────────────────────────────────────────────┐
│ [Logo] ... nav ...                     [🔔][👤]│
├──────────────────────────────────────────────┤
│  Grading — Midterm 1        Student: [M. Hasan ▾] │
│                              [◀ Prev] [Next ▶]      │
│                                                    │
│  Q3 (5 marks): What normal form removes...          │
│  Student answer: "3NF"                                │
│  Awarded marks: [5___] / 5                             │
│  Feedback: [_____________________]                     │
│                                                          │
│  Q4 (10 marks): Write a query that...                   │
│  Student answer: [code block shown read-only]             │
│  Awarded marks: [7___] / 10                                │
│  Feedback: [_____________________]                          │
│                                                              │
│                    [   Save Grades   ]                       │
│         [  Submit Results for Approval  ] (after all graded) │
└──────────────────────────────────────────────┘
```

### Components
- Student selector (dropdown or Prev/Next through the roster of submissions)
- Per-question grading blocks: read-only student answer, editable Awarded Marks, editable Feedback

### Buttons
- **Prev / Next** (move between student submissions)
- **Save Grades** (calls `POST /exams/{id}/grade`, per-submission)
- **Submit Results for Approval** (calls `POST /results/{examId}/submit`, enabled only once every submission is graded — BR-002 precondition)

### Tables
None (form-per-question layout, not tabular).

### Forms
- Per-question: Awarded Marks (numeric), Feedback (text) — one form per submission, submitted per student or batched, per implementation choice.

### Validation
- Awarded Marks: required, must be ≥ 0 and ≤ the question's max marks (VR-006) — inline error and submit-block if violated.
- "Submit Results for Approval" disabled/hidden until all students' submissions for the exam show `status: graded`.

### Navigation
- Reached from Exam List (row click on a `closed`/awaiting-grading exam, Teacher role) or from `GET /exams/{id}/results` summary.
- "Submit Results for Approval" redirects to Exam List with a success toast; the exam then appears read-only until Admin resolves it (BR-002).

### Role Visibility
- **Teacher only**, and only for exams they created.

### Responsive Behaviour
- **Desktop:** student selector as a persistent top bar, question grading blocks in a scrollable main area.
- **Mobile:** same structure but Prev/Next becomes the primary navigation (dropdown selector collapses into a compact picker) to preserve vertical space for the grading form.

---

## 15. Teacher: Attendance Marker

### Purpose
Class roster with present/absent toggle per student per session (FR-027, FR-029).

### Wireframe
```
┌──────────────────────────────────────────────┐
│ [Logo] ... nav ...                     [🔔][👤]│
├──────────────────────────────────────────────┤
│  Mark Attendance                                  │
│  Class: [DB Systems ▾]   Date: [Jul 3, 2026 ▾]      │
│                                                    │
│  ┌────────────────────────────────────────┐      │
│  │ Student          Status                     │      │
│  │ ──────────────────────────────────────      │      │
│  │ A. Rahman        [Present ▾]                 │      │
│  │ B. Karim         [Absent ▾]                  │      │
│  │ C. Islam         [Late ▾]                    │      │
│  └────────────────────────────────────────┘      │
│  [Mark all present]                                 │
│                          [   Save Attendance   ]     │
└──────────────────────────────────────────────┘
```

### Components
- Class + Date selectors
- Student roster table with a status control per row (toggle or dropdown: present/absent/late/excused)
- Bulk "Mark all present" shortcut

### Buttons
- **Mark all present** (bulk-sets all rows to Present, still editable individually afterward)
- **Save Attendance** (calls `POST /attendance` for new records, or `PUT /attendance/{id}` per-record for corrections to an already-marked date)

### Tables
- **Roster table**: columns Student Name, Status control.

### Forms
- Implicit — the roster table itself is the form; per-row Status dropdown is the input.

### Validation
- VR-005: only one record per student/class/date — if the selected date already has records, the page loads in "correction" mode (pre-filled with existing statuses, calling `PUT` instead of `POST` on save).
- Class and Date are required before the roster loads.

### Navigation
- Reached from Dashboard (Teacher) or top nav "Attendance" link.
- Save keeps the Teacher on this page with a success toast; no forced redirect.

### Role Visibility
- **Teacher only**, scoped to their own assigned classes.

### Responsive Behaviour
- **Desktop:** full roster table, Status dropdowns inline per row.
- **Mobile:** roster becomes a stacked card list — Student name as heading, Status dropdown directly below; "Mark all present" and "Save" remain pinned/full-width at the bottom.

---

## 16. Notifications Panel

### Purpose
System-wide notification feed with read/unread state (FR-052, FR-053).

### Wireframe
```
┌──────────────────────────────────────────────┐
│ [Logo] ... nav ...                     [🔔][👤]│
├──────────────────────────────────────────────┤
│  Notifications          [Mark all as read]         │
│                                                    │
│  ● Result published: DB Systems Midterm 1  2h ago  │
│  ● Attendance warning: Networks below 80%  1d ago  │
│  ○ Schedule change: DB Systems moved to Rm 305 3d  │
│  ○ Fee due: 5,000 BDT due Jul 15            5d ago  │
│                                                        │
│                          [◀ Prev]  [Next ▶]            │
└──────────────────────────────────────────────┘
```

### Components
- Notification list (chronological, newest first), unread items visually distinguished (filled vs. hollow dot in wireframe)
- "Mark all as read" bulk action
- Pagination

### Buttons
- **Mark all as read** (calls `PUT /notifications/{id}/read` for all unread, or a bulk variant)
- Individual notification click marks that item as read and optionally deep-links to the relevant page (e.g., a result-published notification links to Results view)

### Tables
None — list format, not tabular.

### Forms
None.

### Validation
Not applicable — read/navigation-only interactions.

### Navigation
- Reached via the persistent notification bell icon in the top nav (present on every authenticated page) or a dedicated route.
- Clicking a notification navigates to the relevant page (Results view, Attendance page, Timetable, Fee Centre) based on `notification.type`.

### Role Visibility
- All roles — content differs based on the notifications generated for that user (result publication and attendance warnings for Student; schedule changes for Student/Teacher; fee due for Student/Parent).

### Responsive Behaviour
- **Desktop:** can render as a dropdown panel from the bell icon for quick access, in addition to the full page.
- **Mobile:** bell icon opens the full Notifications page directly (no dropdown, given limited screen space) with the same stacked list layout.

---

## 17. Parent: Child Attendance/Results/Schedule/Fee View

### Purpose
Read-only aggregation of a linked child's attendance, results, timetable, and fee status (FR-032, FR-037, FR-038, FR-041). Per `Requirement_Analysis.md` §14 item 2, the proposal does not name a distinct screen for this — this wireframe documents the reused-Student-screens approach with a child selector, the resolution adopted in `System_Architecture.md`.

### Wireframe
```
┌──────────────────────────────────────────────┐
│ [Logo] ... nav ...                     [🔔][👤]│
├──────────────────────────────────────────────┤
│  Viewing: [M. Hasan (child) ▾]                    │
│                                                    │
│  [Attendance] [Results] [Timetable] [Fees]         │
│  ┌────────────────────────────────────────┐      │
│  │  (renders the same layout as Pages 7, 6,   │      │
│  │   9, 8 respectively, in fully read-only     │      │
│  │   mode — no action buttons that mutate       │      │
│  │   data)                                       │      │
│  └────────────────────────────────────────┘      │
└──────────────────────────────────────────────┘
```

### Components
- Child selector dropdown (only rendered if the Parent has more than one linked student, per `parent_student_link` M:N relationship, Assumption A-003)
- Sub-navigation tabs: Attendance, Results, Timetable, Fees
- Content area reuses the same components as Pages 6/7/8/9, with all mutating controls (download-only actions excepted) hidden

### Buttons
- Child selector (dropdown, if applicable)
- Sub-nav tabs (Attendance/Results/Timetable/Fees)
- Download-only buttons carried over from reused pages (Transcript PDF, Invoice PDF) remain available, since they are read actions

### Tables
- Same tables as the reused pages (Attendance records, Results, Payment history) — no additional tables introduced here.

### Forms
None — entirely read-only, consistent with Parent's permissions (`Requirement_Analysis.md` §5: "Cannot — no create/update/delete permissions anywhere").

### Validation
Not applicable.

### Navigation
- Reached from Dashboard or a dedicated top-nav "My Children" / "Child Portal" entry.
- Switching the child selector re-fetches all four sub-tabs' data scoped to the newly selected `student_id`.

### Role Visibility
- **Parent only.** Every API call underlying this page is ownership-checked against `parent_student_link` (BR-007, NFR-003) — a Parent cannot view a student they are not linked to, enforced server-side regardless of what the UI shows.

### Responsive Behaviour
- **Desktop:** sub-nav tabs rendered as a horizontal tab strip above the content area.
- **Mobile:** sub-nav tabs become a horizontally scrollable strip (same pattern as Timetable's mobile day-selector) to fit narrow viewports; child selector remains pinned at the top regardless of viewport size, since it governs all tabs' content.

---

## 18. Admin: Reports *(gap-fill page — not explicitly named in proposal §7)*

### Purpose
Generate attendance, result, and fee reports by department, semester, or individual student (FR-030, FR-054, FR-055). Per `Requirement_Analysis.md` §14 item 15, the proposal names this capability as an Admin feature (§5) but does not name a dedicated screen for it in §7 — this wireframe documents the resolution adopted during the Project Readiness Audit.

### Wireframe
```
┌──────────────────────────────────────────────┐
│ [Logo] ... nav ...                     [🔔][👤]│
├──────────────────────────────────────────────┤
│  Reports        [Attendance] [Results] [Fees]     │
│  Dept: [All ▾]  Semester: [Spring 2026 ▾]          │
│                                                    │
│  ┌────────────────────────────────────────┐      │
│  │ (Attendance tab) Student   Percentage      │      │
│  │ ──────────────────────────────────────    │      │
│  │ M. Hasan          62%  ⚠                    │      │
│  │ N. Chowdhury       91%                       │      │
│  └────────────────────────────────────────┘      │
│                          [ Export CSV ]             │
└──────────────────────────────────────────────┘
```

### Components
- Report-type tabs: Attendance, Results, Fees
- Department and Semester filter dropdowns (shared across tabs)
- Report table (columns vary per tab — Attendance: Student/Percentage; Results: grade distribution + pass/fail counts; Fees: collected/outstanding/overdue totals)

### Buttons
- Report-type tabs (Attendance/Results/Fees)
- **Export CSV** (client-side export of the currently displayed table; no dedicated export endpoint — generated from the already-fetched report data)

### Tables
- **Attendance tab**: columns Student, Percentage (from `GET /attendance/reports`).
- **Results tab**: grade distribution table (Grade Letter, Count), a Pass/Fail summary, and an Average GPA figure (`average_gpa`, added Milestone 10 — reuses the same credit-hour-weighted formula as the Student Results view, see `Proposal_vs_Engineering_Additions.md` §6) (from `GET /results/reports`).
- **Fees tab**: summary cards (Collected, Outstanding, Overdue) rather than a row-per-student table (from `GET /fees/reports`).

### Forms
None — filter dropdowns only, not a submitted form.

### Validation
Not applicable — read-only page; Department/Semester filters apply live via query params.

### Navigation
- Reached from Dashboard (Admin) or top nav "Admin" section.
- No downstream navigation besides CSV export (client-side file download, no route change).

### Role Visibility
- **Admin only.**

### Responsive Behaviour
- **Desktop:** report-type tabs as a horizontal strip above the filter row and table.
- **Mobile:** report-type tabs become a horizontally scrollable strip (same pattern as Timetable's mobile day-selector); tables collapse into stacked card lists per the same convention as other Admin tables.

---

## Cross-Page Conventions

- **Top navigation bar**: present on all 18 pages except Login; composition (which links appear) is role-dependent, per `System_Architecture.md` §3.3 (shared shell, conditional widgets/links).
- **Notification bell**: present in the header on every authenticated page, showing an unread-count badge sourced from `GET /notifications`.
- **Loading states**: every data-driven table/widget shows a skeleton/spinner state while its underlying React Query request is in flight (NFR-008); empty states are shown distinctly from loading states (e.g., "No exams scheduled" vs. a spinner).
- **Error states**: failed requests show an inline retry affordance on the affected widget/table rather than a full-page failure, except for 401 (global redirect to Login) and 403 on page-level access (redirect to Dashboard with a permission-denied toast), per `System_Architecture.md` §9.
- **Destructive/state-changing actions** (Deactivate account, Reject result, Delete exam, Bulk overdue notice) always require an explicit confirmation step before the underlying API call fires.
