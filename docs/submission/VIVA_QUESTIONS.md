# Viva Preparation Guide

**Project:** University Management System (ICT Education)
**Version:** v2.4.1
**Format:** ~100 oral-examination questions with detailed model answers, grouped into 23 sections matching the areas an examiner is most likely to probe. Within each section, questions run beginner → difficult, so you can warm up before the harder ones. Every answer is grounded in what is actually implemented in this codebase — not generic textbook material — so cite specifics (endpoint paths, table names, counts) when you answer live, the same way they're cited here.

**Headline facts to have memorized before you walk in:**
- 82 REST endpoints across 11 backend domains
- 26 database tables, 10 Alembic migrations, single head, zero schema drift
- 549 automated tests, all passing (484 backend/pytest, 65 frontend/Vitest)
- Four roles: Student, Teacher, Parent, Admin — RBAC + per-record ownership enforced server-side
- Stack: FastAPI (Python 3.12), PostgreSQL, SQLAlchemy, Alembic, React 18 + TypeScript, TailwindCSS, React Query, JWT auth, ReportLab (PDF), openpyxl (Excel)

---

## 1. Project Overview (Q1–Q5)

**Q1. In one or two sentences, what does your system do?**
It's a role-based web platform that consolidates university operations — attendance, exams and results, fees, and class scheduling — into a single system of record, replacing the usual mix of spreadsheets, email, and disconnected finance tools, with every access-control decision enforced on the server.

**Q2. Who are the users of this system, and how do their permissions differ?**
Four roles: Student (views their own attendance, exams, results, fees, timetable), Teacher (marks attendance, builds/grades exams, submits results, requests schedule changes), Parent (views their linked child's data only, verified by an ownership check, not just a role check), and Admin (manages accounts, reference data, approves results and schedule changes, records payments, runs reports). Every endpoint enforces both the caller's role and, where relevant, ownership of the specific record requested.

**Q3. What is the current version of the system, and what changed most recently?**
Version 2.4.1. The most recent change closed two proposal-compliance gaps: the Teacher's Profile page was relabeled from "Assigned Courses (this semester)" to "Teaching History" because the backend already returned the full cross-semester history — only the label was wrong; and the Parent Dashboard's "Upcoming Exams" widget, which previously showed "Not available," now shows real exam data scoped to the linked child, closing a genuine backend gap (the exam-listing endpoint had no Parent-ownership branch at all before this change).

**Q4. Why did you choose this project topic?**
University administrative processes are a well-understood, real-world domain with clear, testable business rules (approval workflows, access control, derived calculations like GPA and attendance percentage), which makes it a strong vehicle for demonstrating full-stack engineering discipline — layered architecture, RBAC, automated testing — rather than just UI work.

**Q5. What was out of scope, and why does that matter for a viva?**
A Parent-Teacher messaging module, scheduled/cron-based reminders (e.g. fee due-date alerts), and an overall cross-semester CGPA figure were all deliberately left unbuilt and are documented as such in `docs/Proposal_vs_Engineering_Additions.md` and the Limitations section of the project report. It matters because an examiner will respect "I chose not to build X because Y" far more than an undocumented gap discovered live — it shows the scope was actively managed, not just abandoned.

---

## 2. Problem Statement (Q6–Q8)

**Q6. State the problem this system solves.**
Given a university managing student records, attendance, results, fees, and scheduling through a mixture of spreadsheets, email, and disconnected finance tools, design and implement a single web-based system that gives each role exactly the access they're authorized to have, makes every workflow explicit and auditable, enforces access control server-side, and ensures every reported figure is always computed from — and therefore consistent with — its underlying source records.

**Q7. What three specific problems does fragmentation cause, according to your analysis?**
Data duplication (the same fact recorded in more than one place can drift out of sync), weak accountability (no single audit trail for who approved a result or recorded a payment), and inconsistent access control (a shared spreadsheet has no way to guarantee a parent only sees their own child's record).

**Q8. Examiner probe: Couldn't a university just use an existing product like Moodle or a commercial ERP instead of building this?**
Yes, and that trade-off is addressed directly in the literature review. Moodle-class LMS platforms are strong for course content delivery but aren't designed as an institution-wide system of record for fees, attendance, and administrative scheduling together. Commercial ERPs like Banner or PeopleSoft are comprehensive but heavyweight, licensed, and architected for large-scale multi-institution deployment. This project occupies a deliberately narrower niche: a purpose-built system covering exactly the processes this institution needs, with RBAC as a first-class design constraint from day one rather than a bolt-on.

---

## 3. Objectives (Q9–Q11)

**Q9. List your project's primary objectives.**
Replace fragmented tracking with one system of record; enforce RBAC and ownership at the API layer, never trusting the frontend alone; provide a complete workflow lifecycle for exams and results with server-validated transitions; compute derived figures live so they can never drift out of sync; deliver role-appropriate dashboards for all four roles; achieve verifiable correctness through automated testing; and produce a system that's independently deployable and continuously CI-verified.

**Q10. Which objective was hardest to satisfy, and why?**
Enforcing ownership — not just role — consistently across every Parent-facing endpoint. It's easy to check "is this user a Parent"; it's harder to guarantee that check is paired with "and are they linked to *this specific* student" on every single relevant endpoint. A later audit actually found one gap — the exam-listing endpoint had no Parent branch at all — which is direct evidence this objective required deliberate, repeated verification, not a one-time implementation.

**Q11. Examiner probe: How would you measure whether you actually met the "verifiable correctness" objective?**
By the size and shape of the test suite, not just its existence: 549 tests, but more specifically, every documented business rule and validation rule has a dedicated test, every RBAC/ownership boundary has an explicit *negative* test proving the wrong-role or wrong-owner case is rejected (not just that the correct case succeeds), and every workflow state machine is tested for both valid and invalid transitions. That structural coverage, not the raw count, is the actual evidence.

---

## 4. FastAPI (Q12–Q17)

**Q12. What is FastAPI and why did you choose it over Flask or Django?**
FastAPI is a modern, async-capable Python web framework built on Starlette and Pydantic. It was chosen over Flask because it gives native async/await support and automatic request/response validation via Pydantic without extra libraries, and over Django because this project doesn't need Django's built-in ORM/admin/templating — SQLAlchemy and a separate SPA frontend were architectural choices made independently, so Django's batteries would have been unused weight.

**Q13. How does FastAPI use Pydantic, and why does that matter for this project?**
Every request body is validated against a Pydantic schema before it reaches business logic, and every response is also shaped by a Pydantic schema — routers never return raw ORM models directly. This matters for two reasons: it guarantees malformed input is rejected with a structured 422 error before any business logic runs, and it prevents accidentally leaking internal database fields (like a password hash) in an API response.

**Q14. Explain FastAPI's dependency injection system and give a concrete example from your project.**
Dependencies are functions declared as parameters (via `Depends()`) that FastAPI resolves before the route handler runs. This project uses it for three things: database sessions (`get_db()`, a generator dependency that yields a session and guarantees cleanup), the currently authenticated user (decoding and validating the JWT), and RBAC role checks (`require_roles("admin")`), which can raise a 403 before the route body ever executes.

**Q15. Where does async/await matter in your backend, and where doesn't it?**
It matters for I/O-bound work — database queries and, most visibly, background tasks like PDF/Excel generation and notification dispatch, which are scheduled via FastAPI's `BackgroundTasks` so the response returns immediately rather than blocking on report generation. It doesn't meaningfully matter for CPU-bound work, and this project has very little of that — no heavy computation happens inline in a request.

**Q16. How does FastAPI generate API documentation, and is it exposed in production?**
FastAPI auto-generates an OpenAPI schema from the route signatures and Pydantic schemas, served at `/docs` (Swagger UI), `/redoc`, and `/openapi.json`. In this project, those routes are explicitly gated behind an `is_production` check and disabled in production, since exposing the full API surface and schema shapes publicly is an unnecessary information-disclosure risk for a system handling student PII.

**Q17. Examiner probe: If two requests hit the same database row at the same time, how does FastAPI/SQLAlchemy prevent a race condition?**
FastAPI itself doesn't prevent this — it's a database-level concern. This project relies on PostgreSQL's transactional guarantees and unique constraints (e.g. the attendance table's duplicate-prevention constraint) so that a race condition surfaces as an `IntegrityError`, which the service layer catches and translates into a clean `409 Conflict` response rather than a raw 500 or silent duplicate row.

---

## 5. React (Q18–Q22)

**Q18. Why React, and specifically why React 18?**
React was chosen for its component model and the maturity of its ecosystem, particularly TanStack React Query for server-state management, which was a fixed requirement of the technology stack. React 18 specifically brings automatic batching and concurrent-rendering primitives, though this project doesn't lean heavily on the more advanced concurrent features — the main benefit realized is the stable, well-supported hooks API.

**Q19. What is a React hook, and name a custom hook from your project.**
A hook is a function starting with `use` that lets a function component tap into React's state/lifecycle features. This project wraps every API domain in a custom React Query hook — for example `useExams(params)`, which handles fetching, caching, and re-fetching the exam list, including an optional `studentId` parameter for Parent-scoped requests.

**Q20. How does your frontend avoid prop-drilling or a heavy global state manager?**
Server state (anything from the API) lives entirely in React Query's cache, accessed via feature hooks — never duplicated into component state or a Redux-style store. Client-only UI state (modals, active tab, form drafts) uses local component state or a lightweight context. Because most of the data on any given page *is* server state, this split alone removes most of the reason to reach for a heavier state manager.

**Q21. How is routing and authentication guarding implemented?**
`react-router-dom`'s `createBrowserRouter` defines routes; every protected route is wrapped in a `RouteGuard` component that checks for a valid token and redirects unauthenticated users to `/login`. This is explicitly documented as a UX convenience only — the real enforcement is server-side RBAC middleware, so even if a route guard were bypassed, the API would still reject an unauthorized request.

**Q22. Examiner probe: React Query caches API responses — how do you handle a mutation (e.g. approving a result) making that cache stale?**
Every mutation hook calls `queryClient.invalidateQueries()` targeting the relevant query key on success — for example, approving a result invalidates the `["results"]` query key, so any component displaying results automatically refetches fresh data. This avoids manually pushing updated data into the cache by hand, which is more error-prone than just invalidating and letting React Query refetch.

---

## 6. TypeScript (Q23–Q26)

**Q23. Why TypeScript instead of plain JavaScript for the frontend?**
TypeScript catches an entire class of bugs — wrong property names, mismatched function signatures, `undefined` access — at compile time instead of at runtime in a user's browser. For a project with 82 backend endpoints and correspondingly complex response shapes, having the compiler verify that a component actually matches the shape the API returns is a significant reliability gain over plain JS.

**Q24. What TypeScript convention does this project enforce, and why?**
No use of `any` — every API response and request payload has an explicit interface or type (for example, `ExamListItem`, `ExamCreateInput`). This is enforced by convention and ESLint; `any` would silently disable type-checking exactly where it matters most, at the API boundary.

**Q25. How do frontend types stay in sync with backend Pydantic schemas?**
There is no automated codegen step in this project — TypeScript interfaces in `frontend/src/features/*/index.ts` are hand-written to mirror the backend Pydantic response schemas. This is a known manual-sync point; a mismatch would surface as a runtime shape error or a failed component test rather than a compile error, since TypeScript can't verify against a schema it's never seen.

**Q26. Examiner probe: What's the difference between an `interface` and a `type` in TypeScript, and does it matter which this project uses?**
Both can describe object shapes; `interface` supports declaration merging and is conventionally used for object/data shapes, while `type` is more flexible for unions, intersections, and mapped types. This project predominantly uses `interface` for API response/request shapes (e.g. `Exam`, `Question`) and `type` for narrower unions like `ExamStatus = "draft" | "scheduled" | "open" | "closed" | "published"`. It doesn't materially matter for correctness here, but using `type` for the status unions gives exhaustiveness checking in switch statements that `interface` couldn't.

---

## 7. PostgreSQL (Q27–Q31)

**Q27. Why PostgreSQL over MySQL or a NoSQL database?**
PostgreSQL was fixed by the project's technology stack requirements. Practically, it fits well here because the data is highly relational (students, courses, exams, results, fees all reference each other with strict foreign-key integrity requirements), and PostgreSQL's constraint enforcement, transactional guarantees, and mature ecosystem (used with SQLAlchemy/Alembic) are a natural fit for that. A NoSQL store would have pushed referential integrity into application code, which is exactly the kind of silent-drift risk this project was designed to avoid.

**Q28. What database-level constraints does your schema rely on, beyond foreign keys?**
Unique constraints (e.g. one attendance record per student per class session per date, preventing duplicate marking), `NOT NULL` constraints on required fields, and `ON DELETE RESTRICT` on foreign keys from reference/catalog tables (department, course, room, semester) so a row still in use anywhere cannot be deleted.

**Q29. Explain the difference between `ON DELETE RESTRICT` and `ON DELETE CASCADE`, and where each is (or isn't) used here.**
`RESTRICT` blocks the delete if any row still references the target; `CASCADE` deletes the dependent rows automatically. This project deliberately uses `RESTRICT` for reference/catalog data (you shouldn't be able to delete a course that still has class sessions), and avoids `CASCADE` entirely for identity data — Users/Students/Teachers are never deleted at all, only deactivated via an `is_active` flag, specifically to prevent an accidental cascade from silently wiping historical results or attendance tied to that person.

**Q30. How does your project handle database migrations, and how many exist currently?**
Every schema change is a reviewed, generated Alembic migration — never hand-edited after generation and never applied as manual DDL against a running database. There are 10 migrations currently, forming a single linear chain to one head revision, and CI includes an automated check that `alembic revision --autogenerate` produces an empty diff, proving the SQLAlchemy models and the migration history never drift apart.

**Q31. Examiner probe: If you needed to add a new NOT NULL column to a table with existing production data, how would you do it safely?**
Not as a single migration that adds the column as `NOT NULL` directly, since that would fail against existing rows. The safe sequence is: add the column as nullable, backfill existing rows with a sensible default in the same or a follow-up migration, then add a second migration that alters the column to `NOT NULL` once every row is guaranteed populated. This project hasn't needed that exact sequence yet, but the same "never hand-edit a generated migration, always add a new one" discipline applies.

---

## 8. SQLAlchemy (Q32–Q36)

**Q32. What is an ORM, and what specific problem does SQLAlchemy solve here?**
An ORM (Object-Relational Mapper) lets you interact with database rows as Python objects instead of writing raw SQL strings. SQLAlchemy specifically solves two problems in this project: it guarantees all queries are parameterized (closing off SQL injection as an attack surface by construction, since there is no raw string-interpolated SQL anywhere in the codebase), and it gives a consistent, typed way to express relationships (e.g. `Exam.questions`) that repositories query against.

**Q33. Where do SQLAlchemy queries live in your architecture, and why is that boundary enforced?**
Exclusively in the repository layer (`app/repositories/`) — services call repository methods, never the ORM session directly, and routers never touch the ORM at all. This boundary exists so business logic (in services) stays testable in isolation with repositories mocked/stubbed, and so a query's shape can change without services needing to know or care.

**Q34. What is the N+1 query problem, and how does this project avoid it?**
It's when fetching a list of N parent records, then accessing a related collection on each one individually, triggers N additional queries instead of one. This project avoids it with SQLAlchemy's eager-loading options — `joinedload`/`selectinload` — applied wherever a relationship is known to be accessed together with its parent, such as an Exam with its Questions, or a Result with its Student and Course.

**Q35. Explain the difference between `joinedload` and `selectinload`, and when you'd choose one over the other.**
`joinedload` fetches the related rows in the same query via a SQL JOIN; `selectinload` issues a second, separate `SELECT ... WHERE id IN (...)` query for the related rows. `joinedload` is generally better for one-to-one or small one-to-many relationships to avoid a second round-trip; `selectinload` avoids result-set duplication (a JOIN against a one-to-many relationship multiplies parent rows) and is often better for larger collections.

**Q36. Examiner probe: Your SQLAlchemy session is created per-request via a dependency. What happens to an in-progress transaction if the request handler raises an unhandled exception partway through?**
The `get_db()` generator dependency's `finally` block still runs and closes the session; because no explicit `commit()` was reached before the exception, any pending changes are never persisted, and the session's implicit transaction is rolled back on close. This is exactly why business logic should only call `commit()` once a service's whole atomic unit of work has succeeded — an exception raised mid-service leaves the database in its prior, consistent state rather than half-written.

---

## 9. Alembic (Q37–Q40)

**Q37. What is Alembic, and how is it different from just running `CREATE TABLE` manually?**
Alembic is SQLAlchemy's migration tool — it generates versioned, reversible Python scripts that describe schema changes, rather than applying raw DDL by hand. This gives a reviewable history of every schema change, a way to apply the same sequence of changes to any environment (dev, CI, production) deterministically, and a rollback path (`downgrade()`) if a migration needs to be undone.

**Q38. How does Alembic detect what has changed between your SQLAlchemy models and the database?**
`alembic revision --autogenerate` compares the current state of the SQLAlchemy `Base.metadata` (the models) against the actual database schema (introspected from the connected database) and generates a draft migration reflecting the difference. This project runs that command in CI specifically to assert the diff is empty — proof the committed migrations already fully describe the current models.

**Q39. Why does your project forbid hand-editing a generated migration?**
Because a hand-edited migration can silently diverge from what `--autogenerate` would actually produce from the models, reintroducing the exact model/schema drift problem migrations exist to prevent. If a generated migration is wrong or incomplete, the correct fix is to adjust the models and regenerate, not to patch the generated file directly.

**Q40. Examiner probe: Two developers each generate a migration independently, both based on the same prior head. What happens, and how would Alembic surface the problem?**
Both migrations would set the same `down_revision`, creating two branches from one head — Alembic would detect multiple heads and refuse to run `upgrade head` unambiguously until they're merged (via `alembic merge` or by manually rebasing one migration's `down_revision` onto the other). This project's single-developer, milestone-based process hasn't hit this in practice, but it's the standard resolution path in a team setting.

---

## 10. JWT (Q41–Q45)

**Q41. What is a JWT, and what three parts does it contain?**
A JSON Web Token is a compact, URL-safe, digitally signed token consisting of a header (algorithm/type), a payload (claims — e.g. user ID, role, expiry), and a signature (computed over the header and payload using a secret key), separated by dots. The signature lets the server verify the token hasn't been tampered with, without needing a database lookup for every request.

**Q42. How does your project use access tokens vs. refresh tokens?**
Access tokens are short-lived and sent with every API request in the `Authorization` header; refresh tokens are longer-lived and used only to obtain a new access token once the old one expires. Refresh tokens are rotated on every use — each refresh both issues a new refresh token and invalidates the previous one, so a leaked, already-used refresh token becomes worthless.

**Q43. Where is the JWT secret stored, and why does that matter?**
In an environment variable, never committed to source control — `backend/.env` locally, and an actual secret manager/environment configuration in a real deployment. If the signing secret were hardcoded or committed, anyone with repository access could forge valid tokens for any user, completely bypassing authentication.

**Q44. What happens if a user's account is deactivated but they still hold a valid, unexpired access token?**
The request is still rejected. RBAC middleware doesn't just trust the token's claims blindly — it checks the current `is_active` status of the user record on every request, so a deactivated account fails authorization immediately even with a technically-valid signature and un-expired token. This was a deliberate design decision, not an accidental side effect of the token's short lifetime.

**Q45. Examiner probe: Why not just make access tokens long-lived and skip refresh tokens entirely?**
A long-lived access token that leaks (e.g. via a compromised device, an XSS bug, or a logged request) stays valid — and exploitable — for its entire lifetime, with no way to shorten that window without a token-revocation mechanism, which JWTs don't natively support cheaply (that requires a server-side blocklist, defeating some of the point of a stateless token). Short-lived access tokens plus rotated refresh tokens bound the damage window of a leaked access token to minutes, while still avoiding a database round-trip on every single request.

---

## 11. RBAC (Q46–Q50)

**Q46. What is RBAC, and how is it enforced in your backend?**
Role-Based Access Control restricts actions based on a user's assigned role. It's enforced via FastAPI dependency injection — a `require_roles("admin")`-style dependency runs before the route handler and raises a 403 if the caller's role isn't in the allowed set, so unauthorized requests never reach business logic at all.

**Q47. Why is role-only checking insufficient for endpoints like `GET /attendance/me` for a Parent?**
Because "is a Parent" doesn't answer "a parent of *which* student." Without an additional check, any Parent account could request any student's data just by knowing or guessing a student ID. This project layers an ownership check on top of the role check: the service verifies a `parent_student_link` row actually exists connecting that specific parent to that specific student before returning any data.

**Q48. Walk through what happens, step by step, when a Parent requests another parent's child's exam list.**
The request passes authentication (valid token) and passes the role check (caller is a Parent, which is an allowed role for `GET /exams`). Then the service layer resolves the caller's parent profile and calls `parent_has_linked_student(parent_id, student_id)` against the requested `student_id` — since no link exists, this returns false, and the service raises a 403 Forbidden before any exam data is queried or returned.

**Q49. How is RBAC tested, specifically the negative cases?**
Every RBAC/ownership boundary has an explicit negative integration test — for example, a Parent without a link to a given student calling the exams endpoint with that student's ID, asserting the response is 403, not just that a correctly-linked Parent's request succeeds. This project treats "prove the wrong case is rejected" as equally mandatory as "prove the right case works."

**Q50. Examiner probe: Client-side code also hides UI elements a user's role can't use — isn't that RBAC too, and is it redundant with the backend checks?**
It's a UX convenience, explicitly not a security boundary, and the two aren't redundant — they serve different purposes. Hiding a button a Student can't use avoids a confusing dead-end click; it does nothing to stop a request crafted directly against the API (via curl, a modified frontend build, or browser dev tools) bypassing the UI entirely. Every actual authorization decision is made server-side; frontend hiding could be deleted entirely without changing what a user is *able* to do, only what's *convenient* to attempt.

---

## 12. API Design (Q51–Q55)

**Q51. How is your API versioned, and why?**
Every endpoint is under `/api/v1`, so a future breaking change (v2) can be introduced without immediately breaking existing clients — the version is part of the URL path rather than a header, which is simpler for this project's scale and easier to test/document.

**Q52. Give an example of how your API supports pagination, and why it's mandatory rather than optional.**
List endpoints like `GET /exams` accept `page` and `page_size` query parameters and return a `PaginatedResponse` shape (`items`, `total`, `page`, `page_size`). It's mandatory because returning an unbounded result set (e.g. every exam a university has ever created) doesn't scale and creates an easy, accidental denial-of-service vector as data grows — this was treated as a necessary implementation default even though the original proposal's API spec didn't explicitly detail query parameters.

**Q53. How are errors shaped consistently across your API?**
Global exception handlers catch errors before they reach the client and format them into one consistent JSON error shape, rather than each router formatting its own ad hoc error response. 4xx errors are logged at lower severity; 5xx errors always log the full stack trace server-side but never leak internal details (like a raw exception message or stack trace) into the client-facing response body.

**Q54. Why does `GET /exams` accept an optional `student_id` query parameter instead of a separate endpoint like `/exams/parent-view`?**
Because it's the same underlying resource — a list of exams — just scoped differently depending on the caller's role; adding a parallel endpoint would duplicate pagination, filtering, and response-shaping logic for no real benefit. This follows the same convention already used for `GET /attendance/me`, `GET /results/me`, `GET /fees/me`, and `GET /schedule/me`, all of which take an optional, ownership-checked `student_id` for the Parent case rather than branching into separate routes.

**Q55. Examiner probe: Your `GET /exams` endpoint added a new optional query parameter after the API had already shipped. How do you know this didn't break existing clients?**
Because it's additive and optional — any client that doesn't send `student_id` behaves exactly as before (a Student or Admin request is unaffected), and the new behavior only activates for the Parent role, which previously had no valid branch at all and would have either been rejected or, worse, silently returned unfiltered data. Backward compatibility here isn't just claimed; it's covered by the pre-existing Student/Admin integration tests continuing to pass unmodified alongside the new Parent-specific tests.

---

## 13. Database Design (Q56–Q60)

**Q56. Describe the high-level shape of your schema — how many tables, and what are the major entity groups?**
26 tables, grouped into three families: core identity/reference data (user, student, teacher, parent, parent_student_link, department, course, room, semester), academic entities (class_session, enrollment, exam, question, exam_submission, question_grade, result), and operational entities (attendance, fee_structure, invoice, payment, notification, schedule_change_request).

**Q57. Why is there a separate `parent_student_link` table instead of a `parent_id` column directly on the `student` table?**
Because the relationship can be many-to-many in principle (a student could have more than one linked parent/guardian, and a parent can have more than one linked child), which a single foreign-key column on `student` can't represent. A join table is the standard relational modeling answer for that many-to-many shape, and it's also the exact table every Parent-ownership check in the codebase queries against.

**Q58. Why does `result` also reference `exam_id`, when `(student_id, course_id, semester_id)` is already the business-uniqueness key?**
This was a deliberate, documented design addition beyond the original schema: `POST /results/{examId}/submit` submits results per-exam, and the Admin result-approval queue groups pending results by exam name for review — without a stored `exam_id`, there'd be no way to know which exam most recently produced or updated a given result row once the request completed. It's nullable and `ON DELETE RESTRICT`, and it doesn't change the actual uniqueness key, which remains `(student_id, course_id, semester_id)`.

**Q59. How does your schema prevent a student from being marked present twice for the same class session on the same day?**
A unique constraint spanning `(student_id, class_session_id, date)` on the attendance table. The service layer also checks before inserting, but the database constraint is the actual guarantee — if a race condition slipped past the service-level check, the database would reject the duplicate insert with an `IntegrityError`, which is caught and translated into a 409 Conflict response.

**Q60. Examiner probe: Why do Users/Students/Teachers get deactivated instead of deleted, while Departments/Courses/Rooms get hard-deleted?**
Identity records have deep historical dependents — a deleted Student would orphan or force-cascade-delete years of attendance, exam submissions, and results that are legally/academically meaningful even after that student leaves. Reference/catalog data doesn't carry that same weight — a Room or Course is metadata describing where/what, not a historical record itself, and `ON DELETE RESTRICT` already prevents deleting one still actively referenced. Different entities warranted different deletion policies rather than one blanket rule.

---

## 14. Normalization (Q61–Q64)

**Q61. What normal form is your schema designed to, and give one concrete example.**
The schema is designed to Third Normal Form (3NF) — every non-key attribute depends on the whole primary key and nothing but the key. For example, `course_name` and `credit_hours` live only on the `course` table, not repeated on every `class_session` or `enrollment` row that references a course; a class session stores a `course_id` foreign key, not a copy of the course's name.

**Q62. Give an example of a value your schema deliberately does *not* store, that a less-normalized design might store as a column.**
Attendance percentage and GPA. A denormalized design might store `attendance_percentage` as a column on `student`, updated whenever an attendance record changes. This schema never does that — those figures are always computed live, at query time, from the underlying `attendance` and `result` rows, specifically so they can never silently drift out of sync with the records that produce them.

**Q63. What's the trade-off of computing attendance percentage and GPA live instead of storing them denormalized?**
The trade-off is query cost versus consistency risk. Storing them would make reads cheaper (no aggregation needed) but introduces a real risk: every code path that changes an attendance or result record would need to remember to recompute and update the stored figure, and any path that forgets produces a silently wrong number a user sees and trusts. This project prioritized correctness over that read-performance optimization, and explicitly documents that if performance ever requires caching, it should be a deliberate, separately-decided tradeoff — not a default.

**Q64. Examiner probe: Isn't storing `exam_id` on the `result` table (Q58 above) itself a denormalization, since it's not part of the business key?**
Yes, technically — it's an attribute that doesn't strictly belong to the `(student, course, semester)` key. It was accepted anyway because it serves a specific, load-bearing purpose (grouping the Admin approval queue by exam, and recording result provenance) that couldn't be satisfied by a pure 3NF design without a more expensive join back through `class_session`/`exam` at query time, and it doesn't reintroduce any consistency risk, since it's set once at submission time and never needs to be kept in sync with anything else afterward. Every deliberate deviation from strict normalization in this schema is documented with its specific justification, rather than done ad hoc.

---

## 15. Testing (Q65–Q70)

**Q65. What is the overall shape of your test suite?**
549 automated tests total: 484 backend (pytest) and 65 frontend (Vitest), all currently passing. The backend splits further into 24 unit-test files (service-layer logic, repositories stubbed, no database required) and 8 integration-test files (full request → database → response cycle against a real, disposable PostgreSQL database).

**Q66. What's the difference between your unit tests and integration tests, concretely?**
Unit tests call a service method directly with mocked repository objects, asserting on business logic in isolation — e.g. "does `list_exams()` raise 403 for a Parent with no linked student" without touching a real database. Integration tests go through FastAPI's test client, hitting the actual router, service, repository, and a real disposable PostgreSQL database, asserting the full HTTP response — e.g. "does a GET request from an unlinked Parent actually return a 403 status code."

**Q67. Why "disposable" database, specifically — why not just use the developer's real database for integration tests?**
To guarantee tests are deterministic and never corrupt or depend on real data — each integration test run creates a fresh database, applies every Alembic migration, runs the suite, and can be torn down afterward. Testing against a developer's actual working database risks tests passing or failing based on incidental leftover state, and risks accidentally deleting or mutating real data during a test run.

**Q68. What is a "negative test," and why does your convention require one for every RBAC/ownership boundary?**
A negative test asserts that an unauthorized action is actually rejected — e.g. a Teacher attempting to approve their own submitted result gets a 403 — rather than only testing that the authorized action succeeds. It's required because a security boundary that's never tested for the failure case can silently regress (a future refactor could accidentally loosen a check) without any test catching it, since the "happy path" tests would keep passing regardless.

**Q69. How is CI structured, and what does it actually verify beyond "the tests pass"?**
Two GitHub Actions workflows, `backend-ci.yml` and `frontend-ci.yml`, run on every push and pull request. Beyond running pytest/Vitest, backend CI also runs an automated schema-drift check (`alembic revision --autogenerate` must produce an empty diff), meaning CI would fail if a developer changed a SQLAlchemy model without generating the corresponding migration — a class of bug that unit/integration tests alone wouldn't necessarily catch.

**Q70. Examiner probe: Your integration tests hit a real database — doesn't that make your test suite slow and fragile compared to an all-mocked approach?**
It's slower than an all-mocked suite, yes, but the trade-off was deliberate: mocked repository tests can't catch real database-constraint violations (like the attendance duplicate-prevention unique constraint) or query-shape bugs (an incorrect join or a missing eager-load), which are exactly the class of bug that matters most for a data-integrity-sensitive system. The unit tests already cover the fast, isolated business-logic cases; integration tests exist specifically to catch what mocking can't, and running them against a disposable (not shared, not persistent) database keeps them reliable rather than fragile.

---

## 16. Git (Q71–Q74)

**Q71. What branching/commit convention did you follow?**
Feature branches map to milestones or a coherent slice of one (e.g. `feat/m6-exam-builder`), not arbitrary daily snapshots. Commit messages are imperative, present-tense, and scoped to one logical change (e.g. "Add exam grading endpoint," not "fixed stuff"), and reference the relevant milestone or requirement ID where useful.

**Q72. Why is mixing a schema migration with unrelated feature code in the same commit forbidden in your workflow?**
Because it makes the history harder to audit and harder to revert safely — if a feature needs rolling back but its commit also carries an unrelated Alembic migration, reverting the commit either takes the migration with it (potentially destructive) or requires manually untangling the two. Keeping migrations in their own commits keeps schema history independently reviewable and revertible.

**Q73. What's checked immediately before every commit in your workflow, and why?**
`git status`, every time, no exceptions — inspecting the actual diff, not just filenames. This specifically guards against accidentally staging a local developer configuration file (`.env`, IDE settings, personal secrets) that isn't an intended part of the current task; the policy is to stop and ask for confirmation rather than commit anything unexpected.

**Q74. Examiner probe: Why never force-push or amend a shared/published commit in this project's convention?**
Amending or force-pushing a commit that's already been pushed and potentially pulled elsewhere rewrites history other people (or other clones) may already be relying on — anyone who already has the old commit can end up with a diverged, hard-to-reconcile history, or silently lose commits built on top of the rewritten one. Creating a new commit to fix a problem is always safe; rewriting a published one is not, which is why this project's convention treats it as a near-never operation.

---

## 17. GitHub (Q75–Q77)

**Q75. How does your repository demonstrate the milestone-based development process, not just claim it?**
Through its tag history: eleven milestone tags (`v0.1-milestone0` through `v1.1-milestone10`), a `v2.0.0` tag marking the final milestone-program release, and four further hardening-pass tags (`v2.1` through `v2.4.1`, the current version) — each representing a reviewed checkpoint, visible directly in `git tag` output, not just described after the fact.

**Q76. What does your CI configuration actually run on GitHub, and on what trigger?**
Two workflows — `backend-ci.yml` and `frontend-ci.yml` — triggered on every push and every pull request. They run linting, type-checking, and the full pytest/Vitest suites respectively, plus the backend's schema-drift check, giving independent, automated proof the codebase is in a working state on every change, not just on the developer's own machine.

**Q77. Examiner probe: What's logged in `docs/Proposal_vs_Engineering_Additions.md`, and why does that document need to exist at all?**
Every endpoint, page, middleware, utility, or UI component added that wasn't explicitly required by the original proposal, classified as Required (the proposal implies it but omitted it from its own endpoint table), Derived (a mechanical prerequisite for something the proposal does require), or Design Enhancement (pure engineering judgment, not proposal-driven), each with an explicit disposition. It exists so the project's actual delivered scope versus its original proposal is always precisely, honestly auditable — an examiner can check any given feature against this document rather than having to trust an undocumented claim that "this was always the plan."

---

## 18. Reporting (Q78–Q81)

**Q78. What report/document formats does your system generate, and with what libraries?**
PDF (via ReportLab) and Excel (via openpyxl), both pure-Python libraries with no external binary dependency to install. Covers attendance reports (PDF/Excel/CSV), transcripts (PDF), and fee invoices/receipts (PDF).

**Q79. Why does PDF/Excel generation run as a background task instead of inline in the request?**
Because generating a multi-page report is comparatively slow relative to a typical API response, and running it inline would make the requesting client wait on that generation time, occupying a request thread the whole while. Dispatching it as a background task lets the response return quickly (e.g. immediately acknowledging the export request or, in this project's pattern, generating and streaming the file via a dedicated background-task-backed endpoint) rather than blocking the request-response cycle.

**Q80. How does the fee invoice PDF become a "receipt" without a separate generator?**
The exact same `invoice_generator.py` module checks the invoice's `status` field at generation time and swaps the document's label from "Fee Invoice" to "Fee Receipt" once `status == "paid"` — same layout, same code path, one conditional label, rather than maintaining a second near-duplicate generator module for what is fundamentally the same document at a different point in its lifecycle.

**Q81. Examiner probe: The transcript PDF includes a custom-drawn institutional seal — why draw it programmatically instead of using a logo image asset?**
Because no real institution logo/seal image asset exists for this academic project, and embedding a placeholder or unlicensed graphic would have been worse than not having one. It's drawn using ReportLab's existing canvas primitives (concentric circles, curved text, a star) already in use elsewhere in the same file, so it added no new dependency and is explicitly documented as a temporary measure, to be replaced if a real institutional asset is ever supplied.

---

## 19. Architecture (Q82–Q86)

**Q82. Describe your overall system architecture in one sentence.**
A decoupled two-tier architecture — a React + TypeScript single-page frontend communicating over a versioned REST API with a FastAPI backend that is itself strictly layered into Router, Service, and Repository tiers, backed by PostgreSQL.

**Q83. What exactly is each backend layer responsible for, and what is it explicitly forbidden from doing?**
Routers shape requests/responses and delegate immediately to services — forbidden from containing business logic or direct ORM queries. Services own business rules and workflow state transitions — forbidden from touching the ORM session directly; they call repositories. Repositories own all SQLAlchemy queries — forbidden from containing business logic or authorization decisions.

**Q84. Why enforce this layering as a strict convention rather than letting each domain organize itself pragmatically?**
Because without an enforced boundary, "pragmatic" tends to mean "a query snuck into a router because it was faster to write that way," which is exactly how business logic ends up scattered and untestable in isolation. With the boundary enforced, a service's business logic can be unit-tested with repositories mocked, entirely independent of whether the database or even a router exists — that testability is the actual payoff of the discipline, not just tidiness.

**Q85. How does the frontend mirror this same layering philosophy?**
Pages correspond to screens, Feature hooks (React Query) are the only thing that talks to the API for a given domain, and Components render UI and call hooks — never fetch/axios directly. It's the same principle as the backend's Router/Service/Repository split, translated to the frontend: each layer has one job, and a layer never reaches past its neighbor to do another layer's job.

**Q86. Examiner probe: If you were told tomorrow to add a GraphQL API alongside the REST one, how much of your architecture would you need to change?**
The Service and Repository layers would need no changes at all — they're already fully decoupled from the transport/HTTP concerns that live in the Router layer. Only a new set of GraphQL resolvers would need writing, calling into the exact same service methods the REST routers already call. That's the direct, demonstrable payoff of the layering: the business logic doesn't know or care what protocol invoked it.

---

## 20. Deployment (Q87–Q90)

**Q87. How is the backend intended to be deployed, and how is that verified?**
As a containerized service — the backend runs via Docker Compose alongside PostgreSQL, and this is verified by actually running the documented setup process end-to-end (not just described), with CI verifying both the backend and frontend halves of the stack independently on every change.

**Q88. How is the frontend deployed differently from the backend, and why?**
As static assets — the production build (`npm run build`) outputs a static bundle that can be served from any static host or CDN, since it's a client-rendered SPA with no server-side rendering requirement. This is architecturally simpler and cheaper to scale than the backend, which needs an actual running process to serve the API.

**Q89. What environment-specific configuration differs between development and production, and how is it managed?**
Database connection strings, JWT secrets, and the `is_production` flag (which gates `/docs`/`/redoc`/`/openapi.json`) are all environment variables, never hardcoded or committed — `.env.example` documents the placeholders, and actual values live in a developer-local `.env` file (dev) or a secret manager (production), never in source control.

**Q90. Examiner probe: What would break first if you tried to horizontally scale the backend to multiple replicas right now, and why?**
The login rate limiter — it's implemented as in-process memory, so each replica would track its own independent request counts, meaning an attacker could get roughly N times the allowed login attempts by spreading requests across N replicas (or just by hitting different replicas via a load balancer). This is a documented, known limitation, not a discovered surprise — the documented fix is a shared, Redis-backed rate limiter, which was scoped as a future improvement rather than built now, since a single-instance deployment doesn't need it.

---

## 21. Security (Q91–Q96)

**Q91. How are passwords stored, and why not just hash with SHA-256?**
Hashed with bcrypt, a strong adaptive hashing algorithm, never stored or logged in plaintext. Bcrypt (unlike SHA-256, which is a fast general-purpose hash) is deliberately slow and configurable via a work factor, making brute-force and rainbow-table attacks computationally expensive even if the password hash database were ever leaked — a fast hash like SHA-256 offers no such resistance.

**Q92. What specifically prevents SQL injection in this codebase?**
All database access goes through the SQLAlchemy ORM with parameterized queries — there is no raw string-interpolated SQL anywhere in the codebase. Parameters are always passed as bound values, never concatenated into a query string, which is what actually closes off SQL injection, not just "using an ORM" in the abstract (an ORM used with raw string interpolation would still be vulnerable).

**Q93. What rate limiting exists, and what threat does it mitigate?**
`POST /auth/login` is rate-limited, mitigating credential-stuffing and brute-force password-guessing attacks — without it, an attacker could attempt unlimited password guesses against any known email address at whatever speed their network allows. This was explicitly flagged as an unspecified gap in the original proposal (`Requirement_Analysis.md` §14) and closed with a reasonable, documented default.

**Q94. How does the API avoid leaking sensitive information in error responses or logs?**
5xx responses always log the full stack trace server-side but never leak internals (stack traces, raw exception messages, internal file paths) into the client-facing response body — the client sees a generic, consistent error shape. Structured logs never include sensitive data like passwords, raw JWTs, or full payment details, per the project's logging conventions.

**Q95. What is the actual attack this project defends against by never returning ORM models directly from a router?**
Accidental over-exposure of internal fields — an ORM model might carry a password hash, an internal `is_active` flag, or a foreign key a client shouldn't see, and if a router returned it directly (e.g. via a naive `return db_user`), any field added to that model in the future would automatically leak into the API response with no explicit review. Requiring every response to pass through a Pydantic schema forces an explicit, reviewed allowlist of exactly what's returned, every time.

**Q96. Examiner probe: JWTs are stored where on the frontend, and what attack does that choice need to defend against?**
In `localStorage` (`frontend/src/auth/tokenStorage.ts` — access token, refresh token, and user info each under their own key). Storing tokens in `localStorage` is convenient and survives a page refresh, but it's readable by any JavaScript running on the page, which means an XSS vulnerability anywhere in the frontend could exfiltrate a user's tokens. The mitigating factors here are React's default JSX escaping (which prevents naive injection of attacker-controlled HTML/script), short-lived access tokens (limiting the exploitation window), and rotated refresh tokens (limiting reuse of a stolen refresh token) — but this is a real, acknowledged trade-off versus an httpOnly cookie, which JavaScript can't read at all but which introduces its own CSRF-protection requirements.

---

## 22. Performance (Q97–Q99)

**Q97. What's the single biggest performance discipline enforced across this codebase?**
Avoiding N+1 query patterns via SQLAlchemy eager-loading, combined with mandatory pagination on every list endpoint — together these prevent the two most common ways a data-heavy CRUD system quietly degrades as data grows: unbounded result sets, and one query silently becoming dozens.

**Q98. Why compute attendance percentage and GPA live instead of caching them, given that's slower per-request?**
This is a deliberate correctness-over-raw-speed trade-off, covered in more depth under Normalization (Q63) — caching risks a stale, silently-wrong number if any code path that changes the underlying records forgets to invalidate the cache, and for figures a student's academic standing might depend on, that risk was judged to outweigh the performance cost, which in practice is a straightforward aggregation query, not an expensive one at this data scale.

**Q99. Examiner probe: At what scale would your "always compute live" policy for attendance/GPA start to become an actual performance problem, and what would you do about it?**
It would start to matter once a single student's attendance/result history spans enough semesters and class sessions that the aggregation query itself becomes measurably slow — likely in the tens of thousands of rows per student range, well beyond this project's realistic scale. At that point, the documented, deliberate escalation path (already stated in project conventions) is to introduce caching as an explicit, reviewed tradeoff — e.g. a materialized view or a cached column invalidated on write — rather than defaulting to it prematurely for a problem that doesn't exist yet at this system's actual scale.

---

## 23. Future Scope (Q100–Q103)

**Q100. What's the single most impactful improvement you'd prioritize next, and why?**
A shared, Redis-backed rate limiter, because it's the most concrete blocker to horizontal scaling identified in this project (see Q90) — every other future-scope item is an additive feature, but this one is a correctness gap that would actively get worse, not just stay static, if the system were deployed at any real scale.

**Q101. What would it take to add an overall cross-semester CGPA figure?**
`GET /results/me` currently returns only per-semester GPA and doesn't retain per-course credit-hours in that response, so an accurate cumulative figure can't be computed client-side without either a new backend aggregate endpoint or extending the existing response to include the credit-hours data needed to weight a cross-semester average correctly — a Student/Parent Results page currently shows an explicit "Not available" placeholder rather than risk an inaccurate client-side approximation.

**Q102. Why was a Parent-Teacher messaging module explicitly scoped out rather than attempted in a minimal form?**
Because it was never part of the original proposal at all — it isn't a gap in an existing feature, it's new domain scope (new tables, new endpoints, new UI, a new notification pattern), and the project's convention is that new scope requires an explicit decision to build, not an assumption smuggled in during an unrelated pass. Building even a minimal version would have meant inventing requirements no design document had actually specified.

**Q103. Examiner probe: If you had one more month, would you build the future-scope items, or spend it hardening what already exists — and how would you decide?**
I'd spend it hardening rather than adding scope, and the deciding factor is that every documented future-scope item is additive — the system functions completely and correctly without any of them — whereas hardening (broader load/performance testing under realistic data volumes, a security-focused penetration-test-style pass, and closing the shared-rate-limiter gap specifically) reduces risk in what's already shipped and already promised to work. Given a fixed amount of time, reducing risk in delivered functionality is a better use of it than adding functionality nobody has yet asked to be prioritized.
