# Screenshot Evidence Guide

**Project:** ICT Education — University Management System
**Version:** v2.4.1 (final)
**Purpose:** This guide specifies the exact screenshots required as visual evidence for academic submission. It is not a UI feature list — it is a checklist for capturing proof that each documented capability actually runs, for use alongside `PROJECT_REPORT.md`, `TEST_REPORT.md`, and `USER_MANUAL.md`.

**Demo accounts** (from `backend/scripts/seed_demo_data.py`) to use when capturing:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@ictedu.example` | `DemoAdmin123!` |
| Teacher | `teacher1@ictedu.example` | `DemoTeacher123!` |
| Student | `student1@ictedu.example` | `DemoStudent123!` |
| Parent | `parent1@ictedu.example` | `DemoParent123!` |

**Conventions used below:**
- Filenames are two-digit zero-padded, in capture order, `snake_Case_With_Underscores.png`.
- "What should be visible" lists the minimum on-screen content that makes the screenshot usable as evidence — capture more if useful, but not less.
- Capture both light and dark mode only where explicitly noted; otherwise either theme is acceptable as long as it's consistent across the set.

---

## 1. GitHub (01–05)

| # | Module | Page | What should be visible | Why this screenshot is important | Suggested filename |
|---|---|---|---|---|---|
| 01 | GitHub | Repository home | Repo name, description, file/folder listing, star/commit count, `v2.4.1` visible as latest activity | Establishes the project exists as a real, version-controlled repository, not just local files | `01_GitHub_Repository_Overview.png` |
| 02 | GitHub | Commit history | A scrollable list of commits with messages following the imperative-present-tense convention (`Section 8`, `CLAUDE.md`), spanning multiple dates | Demonstrates incremental, traceable development over time rather than a single dump commit | `02_GitHub_Commit_History.png` |
| 03 | GitHub | Tags / Releases | Tag list including `v2.4.1` and prior milestone tags (`v1.0-milestone9`, `v2.0.0`, etc.) | Proves the milestone-based release discipline described in `Implementation_Roadmap.md` was actually followed | `03_GitHub_Tags_Releases.png` |
| 04 | GitHub | Actions tab | `backend-ci.yml` and `frontend-ci.yml` workflow runs, most recent run(s) showing a green/passing status | Independent, automated proof that the test suite passes — not just a local claim | `04_GitHub_CI_Workflow_Passing.png` |
| 05 | GitHub | Repository file tree | Top-level folders (`backend/`, `frontend/`, `docs/`, `.github/`) expanded one level | Confirms the folder structure matches `System_Architecture.md` §7 / `PROJECT_STRUCTURE.md` | `05_GitHub_Repository_Structure.png` |

## 2. Login (06–08)

| # | Module | Page | What should be visible | Why this screenshot is important | Suggested filename |
|---|---|---|---|---|---|
| 06 | Login | `/login` | Full login form — email/password fields, password visibility toggle, "ICT Education" branding | The single entry point for all four roles; establishes baseline UI quality | `06_Login_Page.png` |
| 07 | Login | `/login` (error state) | An inline validation/error message after submitting wrong credentials | Evidence that authentication failures are handled gracefully, not with a raw stack trace or blank screen | `07_Login_Invalid_Credentials_Error.png` |
| 08 | Login | `/login` → `/dashboard` | Browser address bar showing the redirect from `/login` to `/dashboard` immediately after a successful login | Demonstrates the JWT-based auth + route-guard flow described in `System_Architecture.md` §6 actually redirects correctly | `08_Login_Successful_Redirect.png` |

## 3. Admin (09–20)

| # | Module | Page | What should be visible | Why this screenshot is important | Suggested filename |
|---|---|---|---|---|---|
| 09 | Admin | `/dashboard` | Admin summary widgets (user counts, pending approvals, system health) | Shows the Admin's consolidated operational overview, the core value proposition of the system | `09_Admin_Dashboard.png` |
| 10 | Admin | `/admin/users` | User Management table — list of students/teachers/parents with role, status, and create/edit controls | Evidence of full account lifecycle management (FR-xxx account creation/deactivation) | `10_Admin_User_Management.png` |
| 11 | Admin | `/admin/academic-setup/departments` | Department list with create/edit/delete controls | Confirms reference-data management exists beyond raw database seeding | `11_Admin_Academic_Setup_Departments.png` |
| 12 | Admin | `/admin/academic-setup/courses` | Course list including code, name, credit hours, department | Same as above, for Course entity | `12_Admin_Academic_Setup_Courses.png` |
| 13 | Admin | `/admin/academic-setup/rooms` | Room list including capacity | Same as above, for Room entity; also evidences the capacity-validation rule (VR-xxx) | `13_Admin_Academic_Setup_Rooms.png` |
| 14 | Admin | `/admin/academic-setup/semesters` | Semester list including start/end dates | Same as above, for Semester entity | `14_Admin_Academic_Setup_Semesters.png` |
| 15 | Admin | `/timetable` | Admin schedule-management view — class session list plus the create/assign form (course, teacher, room, semester via `SearchableSelect`) | Shows scheduling with conflict detection (FR-046), the backbone all other modules depend on | `15_Admin_Timetable_Schedule_Management.png` |
| 16 | Admin | `/timetable` (change-request panel) | `PendingChangeRequestsPanel` with at least one pending Teacher-submitted change request and its Approve/Reject controls | Evidence of the full Teacher-request → Admin-approval workflow, not just one-sided scheduling | `16_Admin_Schedule_Change_Approval_Queue.png` |
| 17 | Admin | `/admin/result-approval` | Pending results queue grouped by exam, with Approve/Reject actions | Evidence of the result submitted → approved → published workflow (BR-002) | `17_Admin_Result_Approval.png` |
| 18 | Admin | `/admin/fee-dashboard` | Fee structures, payment recording form, and a student's payment history | Evidence of the finance-tracking module replacing the "siloed finance tools" described in the problem statement | `18_Admin_Fee_Dashboard.png` |
| 19 | Admin | `/admin/reports` | Report generation controls (attendance/result/fee, filterable by department/semester/student) with a rendered report on screen | Evidence of the cross-cutting Reports module (FR-030/054/055) | `19_Admin_Reports.png` |
| 20 | Admin | `/notifications` | Notification list showing system-generated entries (approvals, schedule changes, account events) | Evidence of the audit/notification trail described in `System_Architecture.md` §10 | `20_Admin_Notifications.png` |

## 4. Teacher (21–28)

| # | Module | Page | What should be visible | Why this screenshot is important | Suggested filename |
|---|---|---|---|---|---|
| 21 | Teacher | `/dashboard` | Teacher summary widgets (assigned classes, pending grading count) | Shows the Teacher's own operational overview | `21_Teacher_Dashboard.png` |
| 22 | Teacher | `/profile` | "Teaching History" section listing every course the Teacher has ever been assigned, across semesters | Evidence of the v2.4.1 fix correcting the previously mislabeled "this semester" claim — now proven accurate | `22_Teacher_Profile_Teaching_History.png` |
| 23 | Teacher | `/timetable` | Teacher's own class schedule (read-only view) plus the "Request Change" action | Evidence the Teacher-initiated side of the change-request workflow exists | `23_Teacher_Timetable.png` |
| 24 | Teacher | `/teacher/attendance-marker` | Attendance-marking grid for one class session, some students marked present/absent | Evidence of the daily attendance capture that all downstream attendance % calculations depend on | `24_Teacher_Attendance_Marker.png` |
| 25 | Teacher | `/teacher/exam-builder` | Exam builder form — title, type, time limit, and at least one question with options being authored | Evidence of the Exam Builder (a core, complex feature) actually functioning | `25_Teacher_Exam_Builder.png` |
| 26 | Teacher | `/exams` | Exam list showing draft/scheduled/open/closed/published statuses | Evidence of the full exam status lifecycle, not just creation | `26_Teacher_Exam_List.png` |
| 27 | Teacher | `/teacher/grading/:examId` | Grading interface with a submitted student answer and a marks/feedback input | Evidence of manual grading for non-MCQ question types (short answer, descriptive, coding) | `27_Teacher_Grading_Interface.png` |
| 28 | Teacher | `/results` | Teacher's course-level results view before Admin approval (submitted status) | Evidence that result entry is visible to its author pre-publication | `28_Teacher_Results_View.png` |

## 5. Student (29–36)

| # | Module | Page | What should be visible | Why this screenshot is important | Suggested filename |
|---|---|---|---|---|---|
| 29 | Student | `/dashboard` | Attendance %, upcoming exams, and recent results summary widgets | Shows the Student's consolidated at-a-glance view, the core promise of the platform | `29_Student_Dashboard.png` |
| 30 | Student | `/profile` | "Academic History" section showing past semester results alongside profile fields | Evidence of FR-008 (academic history alongside profile) | `30_Student_Profile.png` |
| 31 | Student | `/timetable` | Student's class schedule, table or calendar view | Evidence of Student-facing timetable visibility | `31_Student_Timetable.png` |
| 32 | Student | `/attendance` | Attendance page with the Calendar view toggled on, showing present/absent days | Evidence of the Calendar view (an engineering addition, documented in `Proposal_vs_Engineering_Additions.md`) | `32_Student_Attendance_Calendar.png` |
| 33 | Student | `/exams` | Exam list showing only non-draft exams available to this Student | Evidence that draft-hiding RBAC works from the Student's own perspective | `33_Student_Exam_List.png` |
| 34 | Student | `/exams/:examId/room` | Exam-taking interface — timer, question, and answer input mid-attempt | Evidence of the live exam-taking experience (a real-time, stateful feature) | `34_Student_Exam_Room.png` |
| 35 | Student | `/results` | Published results table with grade letters and semester GPA | Evidence of the result publication workflow reaching its intended end-viewer | `35_Student_Results_View.png` |
| 36 | Student | `/fees` | Outstanding balance, invoice list, and a downloadable invoice/receipt | Evidence of Student-facing fee visibility and the PDF invoice generator | `36_Student_Fee_Centre.png` |

## 6. Parent (37–42)

| # | Module | Page | What should be visible | Why this screenshot is important | Suggested filename |
|---|---|---|---|---|---|
| 37 | Parent | `/dashboard` | Linked-child selector, Fee Status, Attendance %, and the new **Upcoming Exams** widget populated with real scheduled/open exam data | Evidence of the v2.4.1 gap-closure — this widget previously showed "Not available"; this screenshot is the single most important proof of the final release's added scope | `37_Parent_Dashboard_Upcoming_Exams.png` |
| 38 | Parent | `/attendance` | Linked child's attendance view with the PDF/Excel/CSV export toolbar visible | Evidence of Parent report-export capability, matching the proposal's "automatic alerts for absences" promise | `38_Parent_Attendance_View.png` |
| 39 | Parent | `/results` | `ParentResultsView` showing the linked child's results only | Evidence of correct ownership-scoped data — must visibly correspond to the same child selected on the dashboard | `39_Parent_Results_View.png` |
| 40 | Parent | `/fees` | `ParentFeeCentre` showing the linked child's fee balance and invoice history | Evidence of Parent fee visibility, a proposal-promised Section 5 feature | `40_Parent_Fee_Centre.png` |
| 41 | Parent | `/timetable` | Linked child's class timetable (read-only) | Evidence of the Parent-scoped `GET /schedule/me` gap-closure | `41_Parent_Timetable_View.png` |
| 42 | Parent | `/notifications` | Notification list including a result-published or schedule-change entry addressed to the Parent | Evidence that notification fan-out to linked Parents (not just the Student) actually works | `42_Parent_Notifications.png` |

## 7. Reports (43–46)

| # | Module | Page | What should be visible | Why this screenshot is important | Suggested filename |
|---|---|---|---|---|---|
| 43 | Reports | Downloaded attendance report (PDF) | Opened PDF showing the report header, date range, and a per-student attendance table | Evidence of the PDF generation pipeline (background task, per `System_Architecture.md` §2.4) | `43_Reports_Attendance_PDF.png` |
| 44 | Reports | Downloaded attendance report (Excel) | Opened `.xlsx` file in a spreadsheet application showing the same data in tabular form | Evidence of the Excel export path (openpyxl-based), a distinct code path from the PDF one | `44_Reports_Attendance_Excel.png` |
| 45 | Reports | Downloaded transcript (PDF) | Opened PDF showing the seal graphic, student details, and per-semester grade table | Evidence of the transcript generator, including the custom-drawn seal (a documented Design Enhancement) | `45_Reports_Transcript_PDF.png` |
| 46 | Reports | Downloaded fee invoice/receipt (PDF) | Opened PDF, labeled "Fee Receipt" if the invoice status is paid, "Fee Invoice" otherwise | Evidence of the paid/unpaid label-switching logic on a single generator | `46_Reports_Fee_Invoice_PDF.png` |

## 8. Testing (47–49)

| # | Module | Page | What should be visible | Why this screenshot is important | Suggested filename |
|---|---|---|---|---|---|
| 47 | Testing | Terminal — `pytest` run | Full backend test run output ending in a passing summary line (test count, 0 failures) | Direct proof the backend test suite passes, matching the counts claimed in `TEST_REPORT.md` | `47_Testing_Backend_Pytest_Results.png` |
| 48 | Testing | Terminal — `vitest run` | Full frontend test run output ending in a passing summary line | Direct proof the frontend test suite passes | `48_Testing_Frontend_Vitest_Results.png` |
| 49 | Testing | GitHub Actions run detail | Expanded log of a single `backend-ci.yml` or `frontend-ci.yml` run, showing each CI step (lint, type-check, test) succeeding | Evidence the tests pass in a clean CI environment, not only on the developer's own machine | `49_Testing_CI_Pipeline_Detail.png` |

## 9. Database (50–52)

| # | Module | Page | What should be visible | Why this screenshot is important | Suggested filename |
|---|---|---|---|---|---|
| 50 | Database | ERD / schema diagram | Entity-relationship diagram from `Database_Design.md`, showing all tables and foreign-key relationships | Visual proof the implemented schema matches the documented design | `50_Database_ERD.png` |
| 51 | Database | Database client (psql / pgAdmin / DBeaver) — table list | Full list of tables in the running database (`user`, `student`, `teacher`, `parent_student_link`, `exam`, `result`, `fee_structure`, etc.) | Evidence the schema was actually created, not just designed on paper | `51_Database_Table_List.png` |
| 52 | Database | Terminal — `alembic history` | Full migration chain output, oldest to newest, ending at the current head revision | Evidence of version-controlled, incremental schema evolution (10 migrations) rather than one hand-built schema dump | `52_Database_Migration_History.png` |

## 10. Architecture (53–54)

| # | Module | Page | What should be visible | Why this screenshot is important | Suggested filename |
|---|---|---|---|---|---|
| 53 | Architecture | System architecture diagram | The layered diagram from `System_Architecture.md` §1 (SPA frontend / REST API / PostgreSQL, with auth flow) | Visual summary of the decoupled architecture for a reader who won't read the full document | `53_Architecture_System_Diagram.png` |
| 54 | Architecture | IDE — project folder tree | Expanded `backend/app/{core,db,models,schemas,routers,services,repositories}` and `frontend/src/{app,pages,features,components,auth}` in an editor sidebar | Evidence the folder-per-layer convention (`CLAUDE.md` §5, `System_Architecture.md` §7) was followed exactly, not just described | `54_Architecture_Folder_Structure.png` |

---

## Capture checklist summary

| Category | Screenshot range | Count |
|---|---|---|
| GitHub | 01–05 | 5 |
| Login | 06–08 | 3 |
| Admin | 09–20 | 12 |
| Teacher | 21–28 | 8 |
| Student | 29–36 | 8 |
| Parent | 37–42 | 6 |
| Reports | 43–46 | 4 |
| Testing | 47–49 | 3 |
| Database | 50–52 | 3 |
| Architecture | 53–54 | 2 |
| **Total** | | **54** |

**Notes for the person capturing these:**
- Use the seeded demo accounts above so every screenshot shows realistic, non-empty data (empty tables/zero-state screens are not useful evidence).
- Capture the Parent Dashboard (#37) only after confirming the Upcoming Exams widget shows at least one populated entry — re-run `backend/scripts/seed_demo_data.py` against a scratch database first if the currently seeded exam dates have already passed.
- Redact or crop out any real personal data if the database has ever been pointed at anything other than seed/demo data; the seed dataset itself is synthetic and safe to show as-is.
- Store the final image files under a `docs/submission/screenshots/` folder (not created by this guide) using the filenames above, in order.
