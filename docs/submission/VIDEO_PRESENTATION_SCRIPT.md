# Video Presentation Script

**Project:** University Management System (ICT Education)
**Version:** v2.4.1
**Target duration:** 12–15 minutes
**Style:** Natural, first-person, spoken — written to be read aloud comfortably, not read as a formal report

**Demo accounts used throughout this script** (from `backend/scripts/seed_demo_data.py`):

| Role | Email | Password |
|---|---|---|
| Admin | `admin@ictedu.example` | `DemoAdmin123!` |
| Teacher | `teacher1@ictedu.example` | `DemoTeacher123!` |
| Student | `student1@ictedu.example` | `DemoStudent123!` |
| Parent | `parent1@ictedu.example` | `DemoParent123!` |

**Before recording:** run `backend/scripts/seed_demo_data.py` against a fresh scratch/demo database so every screen shows realistic, non-empty data, and confirm the seeded exam dates are still in the future (the Parent dashboard's Upcoming Exams widget needs at least one upcoming, non-draft exam to look right on camera).

**Running total at the end of each section** is given so you can check your pacing live while recording.

---

## 1. Introduction — ~0:45 (running total 0:45)

**What I should say:**
> "Hi, I'm Mahabbat Hossain, and this is my final-year project — a University Management System built for ICT Education. It's a full-stack, role-based web platform that brings attendance, exams, results, fees, and scheduling into one system, instead of the usual mix of spreadsheets, email, and separate finance tools. I'm currently on version 2.4.1, which is the final, most polished build. Over the next few minutes I'll walk through the problem it solves, how it's built under the hood, and then I'll actually log in as each of the four roles — Admin, Teacher, Student, and Parent — to show you it really works, not just on paper."

**What I should click:**
- Nothing yet — talk over the Login page (`/login`) already loaded in the browser, or a title slide if you're using one as a cold open.

**Approximate duration:** 0:45

**Transition sentence:**
> "So — what's actually wrong with how universities usually do this? Let's start there."

---

## 2. Problem Statement — ~1:00 (running total 1:45)

**What I should say:**
> "Most universities I looked at manage this stuff through a mix of tools that were never designed to talk to each other. Attendance gets tracked in a spreadsheet somewhere. Results get emailed out. Fees live in a completely separate finance system. And that causes three real problems. First, data duplication — the same fact, like a student's enrollment, might get typed into two different places and quietly drift out of sync. Second, weak accountability — there's no single trail showing who approved a result or who recorded a payment. And third, inconsistent access control — you genuinely cannot guarantee, with a shared spreadsheet, that a parent only sees their own child's data and nobody else's. So the goal of this project was simple to state, even if it wasn't simple to build: one system, one source of truth, with access control enforced by the server itself — not just hidden behind a nicer interface."

**What I should click:**
- Stay on the Login page or a simple problem-statement slide/diagram if you have one prepared. No live app interaction needed for this section.

**Approximate duration:** 1:00

**Transition sentence:**
> "To solve that properly, I had to be deliberate about the technology underneath it — so let me show you the stack."

---

## 3. Technology Stack — ~1:00 (running total 2:45)

**What I should say:**
> "On the backend, I used FastAPI with Python 3.12, talking to a PostgreSQL database through SQLAlchemy — so there's no raw SQL anywhere in the codebase, every query goes through the ORM. Every schema change is a proper, versioned Alembic migration — I've got ten of them right now, and they're always kept in sync with zero drift, which I actually check automatically. On the frontend, it's React 18 with TypeScript and TailwindCSS, and all the data that comes from the server lives in React Query — nothing gets duplicated into some separate piece of local state. For authentication I used JWT — access tokens plus refresh tokens that rotate every time they're used — and role-based access control is enforced on literally every protected route. And for documents — things like transcripts and invoices — I used ReportLab for PDFs and openpyxl for Excel exports, both pure Python, so there's nothing extra to install on the server."

**What I should click:**
- Optionally show `backend/requirements.txt` and `frontend/package.json` briefly in an editor, or a tech-stack slide with the logos. Keep this section screen-light — it's mostly narrated.

**Approximate duration:** 1:00

**Transition sentence:**
> "Now let's zoom out and look at how all of that fits together architecturally."

---

## 4. Architecture — ~1:15 (running total 4:00)

**What I should say:**
> "The system is a decoupled two-tier architecture — a single-page frontend talking to a versioned REST API, backed by PostgreSQL. The backend itself is strictly layered into three pieces. Routers only handle shaping the request and response — no business logic lives there. Services own all the actual business rules and workflow transitions — for example, the rule that a result has to go from submitted, to approved, to published, in that order. And repositories are the only place that touches the database directly through SQLAlchemy. That separation sounds a bit academic, but it's what let this grow to eleven backend domains and eighty-two endpoints without turning into spaghetti. On the frontend, there's an equivalent boundary — pages call typed hooks built on React Query, and those hooks are the only thing that ever talks to the API. No component ever calls fetch directly. And two things that could slow a request down — generating a PDF, and sending out a notification — both run in the background, not inline, so the user isn't sitting there waiting on them."

**What I should click:**
- Show an architecture diagram if you have one (`System_Architecture.md` §1), or briefly show the `backend/app` folder tree in an editor — `core/`, `db/`, `models/`, `schemas/`, `routers/`, `services/`, `repositories/` — to visually back up the layering claim.

**Approximate duration:** 1:15

**Transition sentence:**
> "All of that architecture exists to protect one thing underneath it — the database. Let's look at that next."

---

## 5. Database — ~1:00 (running total 5:00)

**What I should say:**
> "The database has 26 tables, all properly relationally constrained with foreign keys — nothing is held together by convention alone. I made two deliberate design decisions I want to call out. First, reference data — things like departments, courses, and rooms — uses hard deletes, protected by 'on delete restrict,' so you literally cannot delete a course that's still being used somewhere. But identity records — Users, Students, Teachers — are never deleted, only deactivated, because you need to preserve historical data like someone's past results even after they've left. Second, and this one I'm genuinely proud of — figures like attendance percentage or GPA are never stored as a column anywhere. They're always calculated live, at the moment they're requested, straight from the underlying attendance and result records. That means they can never silently go out of sync with reality, which was a real risk I wanted to design out from the start."

**What I should click:**
- Open a database client (pgAdmin, DBeaver, or `psql`) showing the table list, or show the ER diagram from `Database_Design.md`.

**Approximate duration:** 1:00

**Transition sentence:**
> "Okay — enough architecture talk. Let's actually log in and see this thing working, starting with the Admin."

---

## 6. Admin Demo — ~1:45 (running total 6:45)

**What I should say:**
> "I'm going to log in as an Admin now. This is the operational control center for the whole university. Here on the dashboard you can see a system-wide summary — user counts, pending approvals, that kind of thing. Let's go into User Management — this is where an Admin creates and manages accounts for every role, and can deactivate someone without ever deleting their history. Over in Academic Setup, an Admin manages the reference data everything else depends on — departments, courses, rooms, and semesters. Now here's the Timetable page — this is where class sessions get created, and it actually has conflict detection built in, so you can't accidentally double-book a teacher or a room. And right here is something I'm proud of — the schedule change-request queue. If a teacher requests a room or time change, it lands right here for the Admin to approve or reject, so that workflow is never one-sided. Let's also peek at Result Approval, which is the final checkpoint before any result becomes visible to a student, and the Fee Dashboard, where payments actually get recorded."

**What I should click:**
1. Go to `/login`, sign in with `admin@ictedu.example` / `DemoAdmin123!`.
2. Land on `/dashboard` — point out the summary widgets.
3. Click **User Management** (`/admin/users`) — show the list, briefly open the create/edit form.
4. Click **Academic Setup → Departments/Courses** (`/admin/academic-setup/departments`, `/courses`) — show the lists.
5. Click **Timetable** (`/timetable`) — show the class-session list and the create form.
6. Scroll to the **Pending Change Requests** panel — show at least one pending request, click Approve.
7. Click **Result Approval** (`/admin/result-approval`) — show the pending queue.
8. Click **Fee Dashboard** (`/admin/fee-dashboard`) — show a payment record.

**Approximate duration:** 1:45

**Transition sentence:**
> "That's the Admin's-eye view. Now let's log out and see what the system looks like from a Teacher's side."

---

## 7. Teacher Demo — ~1:30 (running total 8:15)

**What I should say:**
> "Now I'm logged in as a Teacher. On the profile page, there's a Teaching History section — and I want to point out, this now correctly shows every course I've ever taught, across every semester, not just the current one. That was actually a small but important fix I made in this latest version — the data was always there on the backend, the label on the frontend just used to say 'this semester' incorrectly. Moving on — here's the Attendance Marker, where I mark students present or absent for a specific class session, and that feeds directly into the live attendance percentage everyone else sees. This is the Exam Builder — I can create an exam, set a time limit, and add questions across four different types: multiple choice, short answer, descriptive, and even coding questions. And once students have taken an exam, anything that needs a human to grade it — like a descriptive answer — comes through this Grading Interface, where I award marks and leave feedback per question."

**What I should click:**
1. Log out, log in with `teacher1@ictedu.example` / `DemoTeacher123!`.
2. Click **Profile** (`/profile`) — scroll to Teaching History, point out multiple semesters/courses listed.
3. Click **Attendance Marker** (`/teacher/attendance-marker`) — select a class session, mark a few students.
4. Click **Exam Builder** (`/teacher/exam-builder`) — show the form, add one question live if time allows.
5. Click **Exams** (`/exams`) — show the status column (draft/scheduled/open/closed/published).
6. Click into **Grading** (`/teacher/grading/:examId`) for a submitted exam — show a descriptive answer and award marks.

**Approximate duration:** 1:30

**Transition sentence:**
> "Everything a teacher just did feeds straight into what a student sees — so let's switch to that view."

---

## 8. Student Demo — ~1:30 (running total 9:45)

**What I should say:**
> "This is the Student view now. Right on the dashboard, I can see my attendance percentage, my upcoming exams, and my most recent results, all in one place. If I go into Attendance, I can see my full record, and there's actually a calendar view as well as a table view. Let's go take an exam — this is the live exam room. There's a real countdown timer running, and if I run out of time it auto-submits whatever I've answered so far. Once a result has actually been published by the Admin — not before — it shows up here on the Results page with a grade letter and my GPA for the semester. And finally, the Fee Centre — I can see my outstanding balance, my invoice history, and download a PDF of any invoice directly."

**What I should click:**
1. Log out, log in with `student1@ictedu.example` / `DemoStudent123!`.
2. Land on `/dashboard` — point out the three summary widgets.
3. Click **Attendance** (`/attendance`) — toggle to Calendar view.
4. Click **Exams** (`/exams`) → open an available exam → show the Exam Room (`/exams/:examId/room`) with the timer running (answer one question live).
5. Click **Results** (`/results`) — show a published result with grade + GPA.
6. Click **Fee Centre** (`/fees`) — show the balance and download an invoice PDF.

**Approximate duration:** 1:30

**Transition sentence:**
> "Now, the role I actually think is the most interesting from an engineering perspective — the Parent."

---

## 9. Parent Demo — ~1:15 (running total 11:00)

**What I should say:**
> "This is the Parent account, and it's linked to one specific child. Notice this dropdown at the top — if a parent has more than one child linked, they can switch between them, and every single widget on this page re-scopes itself to whichever child is selected. Here's the dashboard — Fee Status, Attendance percentage, and this — Upcoming Exams — which is actually the newest feature I added in this final version. Up until recently, this space just said 'Not available,' because there was no way for a parent to see their child's exam schedule at all. I went back, built a proper backend endpoint for it that checks the parent is genuinely linked to that student before returning anything, and now it shows real, upcoming exam dates. Let's also check Attendance and Results — same thing, everything you see here is scoped specifically to this one child, verified on the server, not just hidden in the interface."

**What I should click:**
1. Log out, log in with `parent1@ictedu.example` / `DemoParent123!`.
2. Land on `/dashboard` — point at the linked-child dropdown, then the Fee Status / Attendance % / **Upcoming Exams** widgets (pause on Upcoming Exams).
3. Click **Attendance** (`/attendance`) — show the child's record and the export toolbar.
4. Click **Results** (`/results`) — show the child's published results.

**Approximate duration:** 1:15

**Transition sentence:**
> "Speaking of exports — let's look at the reporting side of the system, since that ties every role together."

---

## 10. Reporting — ~1:00 (running total 12:00)

**What I should say:**
> "Reports are available as PDF, Excel, and CSV throughout the system — attendance reports, transcripts, fee invoices. Let me download an attendance report as a PDF here — and here's the same data as an Excel spreadsheet. These aren't generated inline while you wait, by the way — they run as a background task on the server, so requesting a big report never slows down the rest of the app for that user. And here's the transcript PDF — it's got a proper credit-weighted GPA per semester, and even a little institutional seal I drew programmatically since there's no real university logo asset to use."

**What I should click:**
1. As Admin (or Parent, if already logged in), go to **Reports** (`/admin/reports`) or the **Attendance** export toolbar.
2. Click **Export PDF** — open the downloaded file.
3. Click **Export Excel** — open the downloaded file briefly.
4. Show a downloaded **transcript PDF** (from Results view) — point out the seal graphic.

**Approximate duration:** 1:00

**Transition sentence:**
> "All of this only matters if it's actually correct — so let me show you how I verified that."

---

## 11. Testing — ~1:00 (running total 13:00)

**What I should say:**
> "I didn't just eyeball this and hope it worked. There are 549 automated tests in this project — 484 on the backend using pytest, and 65 on the frontend using Vitest — and all of them are currently passing. Let me run the backend suite right now... and there it is, all green. On the frontend side, same thing. What I actually care about most here isn't just the number — it's what's covered. Every business rule has a dedicated test. And every access-control boundary has what's called a negative test — meaning I didn't just prove the right role can do something, I proved the wrong role, or the wrong parent trying to see someone else's child's data, actually gets rejected. All of this runs automatically through GitHub Actions on every single push, so it's not just tested once and forgotten."

**What I should click:**
1. Open a terminal, run `pytest` in `backend/` — let it scroll to the final passing summary line.
2. Open another terminal (or split pane), run `npm run test` / `npx vitest run` in `frontend/` — show the final passing summary.

**Approximate duration:** 1:00

**Transition sentence:**
> "And you can verify all of this yourself, because the entire history is public on GitHub — let me show you."

---

## 12. GitHub Repository — ~0:45 (running total 13:45)

**What I should say:**
> "Here's the repository. You can see the full commit history — this wasn't built in one sitting, it went through a proper milestone-based process, and you can actually see that in the tags — version 0.1 all the way through to 2.0 for the final milestone release, and then a few more hardening passes after that up to 2.4.1, which is what I'm demoing today. And here in Actions, you can see the CI pipeline — it runs the backend and frontend test suites automatically on every push, so there's independent proof this actually passes, not just on my machine."

**What I should click:**
1. Open the GitHub repository home page.
2. Scroll the commit history briefly.
3. Click **Tags/Releases** — show the version list up to `v2.4.1`.
4. Click the **Actions** tab — show a recent passing CI run.

**Approximate duration:** 0:45

**Transition sentence:**
> "So, to wrap up —"

---

## 13. Conclusion — ~0:45 (running total 14:30)

**What I should say:**
> "This project set out to replace the fragmented, spreadsheet-and-email way universities often manage themselves, with one system where access control is actually enforced by the server, and every number you see — a percentage, a balance, a grade — is computed live from real data, not cached or guessed at. It covers all four roles end to end, it's backed by 549 automated tests, and the entire build history is public and auditable on GitHub. That's the University Management System, version 2.4.1. Thanks for watching."

**What I should click:**
- Return to the Login page or a closing title slide.

**Approximate duration:** 0:45

**Transition sentence:**
> *(End of video — no further transition needed.)*

---

## Pacing summary

| # | Section | Duration | Running total |
|---|---|---|---|
| 1 | Introduction | 0:45 | 0:45 |
| 2 | Problem Statement | 1:00 | 1:45 |
| 3 | Technology Stack | 1:00 | 2:45 |
| 4 | Architecture | 1:15 | 4:00 |
| 5 | Database | 1:00 | 5:00 |
| 6 | Admin Demo | 1:45 | 6:45 |
| 7 | Teacher Demo | 1:30 | 8:15 |
| 8 | Student Demo | 1:30 | 9:45 |
| 9 | Parent Demo | 1:15 | 11:00 |
| 10 | Reporting | 1:00 | 12:00 |
| 11 | Testing | 1:00 | 13:00 |
| 12 | GitHub Repository | 0:45 | 13:45 |
| 13 | Conclusion | 0:45 | 14:30 |

**Total target: ~14:30**, comfortably inside the 12–15 minute window with a little slack for natural pauses, mis-clicks, or a slower speaking pace on the day.

## Recording notes

- Read each "What I should say" block conversationally, not word-for-word robotic — it's written the way a student would actually talk, including small verbal connectors ("okay," "let's," "and here's the thing"), so treat it as a guide rather than a strict script if that feels more natural to you.
- Rehearse the click sequence once before recording so role-switching (logout → login as the next role) doesn't eat into your spoken time.
- If you fall behind schedule, the safest sections to trim are Technology Stack (§3) and Reporting (§10) — both are narration-heavy and can be shortened without losing a demoed feature.
- Keep the Parent Demo's Upcoming Exams moment (§9) intact regardless of time pressure — it's the clearest evidence of the v2.4.1 release and worth protecting from cuts.
