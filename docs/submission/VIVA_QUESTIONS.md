# Viva Questions & Model Answers

100 oral-examination questions with model answers, grounded in the actual implemented University Management System (ICT Education) — FastAPI + PostgreSQL + SQLAlchemy backend, React + TypeScript frontend. Ordered beginner → expert within each of 15 topic areas. Where a question is general computer-science knowledge, the answer ties back to how the concept is actually used in this project.

---

## A. Python (Q1–Q6)

**Q1. What are Python's key features that made it suitable for this project's backend?**
Python offers a large, mature web-framework ecosystem (FastAPI), strong typing support via type hints (used throughout this project's Pydantic schemas and function signatures), readability, and first-class async/await support, which FastAPI relies on for non-blocking request handling.

**Q2. What is a Python decorator, and where is one used in this project?**
A decorator is a function that wraps another function/class to extend its behavior without modifying its source. This project uses decorators extensively via FastAPI's routing syntax, e.g. `@router.get("/me")`, which registers a function as the handler for that route, and `@pytest.fixture` in the test suite to provide reusable setup objects like a database session.

**Q3. Explain Python type hints and how this project uses them.**
Type hints (`def f(x: int) -> str`) annotate expected types without enforcing them at runtime by themselves. This project uses them on every service/repository method signature, and combines them with Pydantic (which *does* enforce validation at runtime) for every request/response schema, so a caller and a reader both know exactly what shape of data flows through each layer.

**Q4. What is the difference between a list and a tuple, and does this project use both?**
A list is mutable and ordered; a tuple is immutable and ordered. The codebase mostly uses lists (e.g. query results from repositories) but tuples appear where a fixed, small, immutable grouping is returned, e.g. `get_student_with_user()` returning `(Student, User)`.

**Q5. What is a Python generator, and where would FastAPI use one?**
A generator produces values lazily via `yield` instead of building a full list in memory. FastAPI's dependency-injection system uses generator functions for resources needing setup/teardown — this project's `get_db()` dependency is a generator that yields a database session and guarantees it is closed afterward, even if the request raises an exception.

**Q6. What is the Global Interpreter Lock (GIL) and why doesn't it block this project's concurrency model?**
The GIL allows only one thread to execute Python bytecode at a time in the reference CPython interpreter. This project's concurrency comes from FastAPI's async event loop (cooperative concurrency for I/O-bound work like database queries and PDF generation dispatched via `run_in_threadpool`), not from CPU-bound multi-threading, so the GIL is not a practical bottleneck for this workload.

---

## B. FastAPI (Q7–Q13)

**Q7. What is FastAPI and why was it chosen for this project?**
FastAPI is a modern, high-performance Python web framework for building APIs, built on Starlette and Pydantic. It was chosen (per the project's fixed technology stack) for its native async support, automatic request validation via Pydantic, and automatic interactive API documentation (Swagger UI) generated directly from the code.

**Q8. How does FastAPI's dependency injection work, and give an example from this project.**
A dependency is a callable declared as a parameter default via `Depends(...)`; FastAPI resolves it before the route function runs. This project uses it for the database session (`db: Session = Depends(get_db)`), the authenticated user (`current_user: User = Depends(get_current_user)`), and role checks (`dependencies=[Depends(require_roles("admin"))]`), keeping cross-cutting concerns out of the route function body.

**Q9. How are request and response bodies validated in this project?**
Every request body is typed as a Pydantic `BaseModel` subclass (a "schema"), and FastAPI automatically validates the incoming JSON against it before the route function executes, returning `422 Unprocessable Entity` with field-level errors on failure. Response models are also declared (`response_model=...`), which both documents and enforces the exact shape returned to the client, and ensures an ORM model is never accidentally leaked directly.

**Q10. How does this project generate its interactive API documentation?**
FastAPI derives OpenAPI schema automatically from route declarations, Pydantic models, and docstrings, serving it at `/docs` (Swagger UI) and `/redoc`. This project explicitly disables all three (`/docs`, `/redoc`, `/openapi.json`) when `ENVIRONMENT=production`, so the full endpoint surface isn't publicly discoverable in a real deployment.

**Q11. How does this project handle errors consistently across 82 endpoints?**
Through FastAPI's global exception handlers, registered once in `app/main.py`, which translate any raised exception (validation errors, `HTTPException`s raised by services, and unhandled exceptions) into one consistent JSON error shape, rather than each router formatting its own error responses.

**Q12. What is `run_in_threadpool` and why does this project use it for PDF/Excel generation?**
It's a FastAPI/Starlette utility that runs a synchronous, CPU-bound function in a background thread instead of blocking the async event loop. ReportLab (PDF) and openpyxl (Excel) generation are both synchronous, CPU-bound operations, so wrapping them in `run_in_threadpool` keeps the event loop free to serve other requests while a document is being built.

**Q13. How would you version this API for a future breaking change, and how is that already supported?**
By introducing a new URL prefix (e.g. `/api/v2`) alongside the existing one, so already-deployed frontend builds keep working against `/api/v1` unchanged. This project already versions every endpoint under `/api/v1` from day one specifically to make that future migration possible without a coordinated frontend/backend redeploy.

---

## C. PostgreSQL (Q14–Q19)

**Q14. Why PostgreSQL over another relational database for this project?**
PostgreSQL was fixed by the project's technology stack; it offers strong standards compliance, robust constraint/foreign-key enforcement (used extensively here), native UUID support (used as this project's primary-key type), and mature tooling that integrates cleanly with SQLAlchemy/Alembic.

**Q15. What is a foreign key, and what delete behavior does this project use by default?**
A foreign key enforces that a column's value must exist as a primary key in another table, preventing orphaned references. This project defaults every foreign key to `ON DELETE RESTRICT` — you cannot delete a `department` while `course` rows still reference it — preserving historical data integrity rather than silently cascading deletions.

**Q16. What is a unique constraint, and give a concrete example from this schema.**
A unique constraint guarantees no two rows share the same value (or combination of values) in the constrained column(s). `attendance_record` has a composite unique constraint on `(student_id, class_session_id, attendance_date)`, which is the actual database-level guarantee that a student can't be marked attendance twice for the same class on the same day — not just an application-level check.

**Q17. What is a database index, and name one used in this project along with its purpose.**
An index is a data structure that speeds up lookups on a column at the cost of extra storage and slightly slower writes. `notification` has a composite index on `(user_id, is_read)`, because the notification panel's unread-count query filters on exactly those two columns for every request.

**Q18. What is a database transaction, and how does this project use one?**
A transaction groups multiple operations so they either all succeed (`COMMIT`) or all fail together (`ROLLBACK`), preserving consistency. Every service method that writes more than one row — e.g. auto-generating an invoice per eligible student when a fee structure is created — performs all of its writes within one SQLAlchemy session and commits once, so a partial failure never leaves half-created invoices behind.

**Q19. How does this project verify its database schema stays in sync with its ORM models over time?**
By running `alembic revision --autogenerate` against a fully-migrated database and checking the output is empty — if SQLAlchemy detects any difference between the current models and the actual database schema, it would generate a non-empty migration, which is treated as a CI failure (a documented, automated schema-drift check).

---

## D. React (Q20–Q26)

**Q20. What is React, and what architectural style does this project's frontend follow?**
React is a component-based JavaScript/TypeScript library for building user interfaces. This project's frontend is a feature-sliced single-page application: one component tree per screen (`pages/`), one typed data-fetching hook module per API domain (`features/`), and shared presentational components (`components/`).

**Q21. What is a React Hook, and name a built-in one used heavily in this project.**
A Hook is a function letting a function component use state, lifecycle, or context features. `useState` is used throughout for local UI state (e.g. a modal's open/closed flag, a form field's current value); `useEffect` is used for side effects like auto-selecting a Parent's first linked child once the children list loads.

**Q22. What is React Query (TanStack Query) and why does this project use it instead of plain `useState` for API data?**
React Query manages server-state: fetching, caching, background refetching, and loading/error states, keyed by a "query key." This project uses it exclusively for anything that comes from the API, because it solves cache invalidation and refetch-after-mutation declaratively (e.g. marking attendance invalidates the `["attendance"]` query key, which automatically refreshes every screen reading attendance data) rather than manually tracking loading flags and re-fetch calls by hand.

**Q23. Explain how this project prevents "prop drilling" for authentication state.**
Authentication state (current user, role, token presence) is held in a small React Context (`AuthContext`) provided once near the app root, so any component — including deeply nested route guards — can read it via `useAuth()` without passing it down through every intermediate component's props.

**Q24. What is a controlled component, and where did this project need to convert an uncontrolled form to a controlled one?**
A controlled component's value is driven by React state (`value` + `onChange`), versus an uncontrolled one that reads its value imperatively (e.g. via `FormData`) only at submit time. The Admin Timetable forms were converted from `FormData`-based reads to per-field `useState` specifically because the new `SearchableSelect` component has no native form-field participation (it isn't a real `<input>`/`<select>`), so `FormData` could never read its selected value.

**Q25. How does this project keep four different user roles from requiring four separate frontend applications?**
Shared screens (Dashboard, Timetable, Attendance, Results, Fee Centre) render one component tree that branches internally on `useAuth().user.role`, composing role-specific widgets/views conditionally, rather than maintaining a fully separate page tree per role — RBAC enforcement itself still happens server-side; this branching is purely a UX/composition choice.

**Q26. What testing library does the frontend use, and what kind of behavior does it verify?**
Vitest (a Vite-native test runner) combined with React Testing Library, which renders components into a simulated DOM (jsdom) and queries them the way a user would (by visible text/role), rather than by internal implementation details. Tests cover things like the exam timer computing its countdown from a server-recorded start time (not the client clock), and that approving a schedule change request actually calls the resolve mutation with the correct arguments.

---

## E. Authentication (Q27–Q32)

**Q27. Describe this project's login flow end to end.**
The client submits email/password to `POST /auth/login`; the server verifies the password against its bcrypt hash, and on success issues a short-lived JWT access token and a longer-lived refresh token. The access token is attached as `Authorization: Bearer <token>` on every subsequent request; when it expires, the client calls `POST /auth/refresh` to obtain a new pair without forcing a full re-login.

**Q28. Why are passwords hashed with bcrypt instead of stored in plaintext or hashed with a fast general-purpose hash like SHA-256?**
Bcrypt is a deliberately slow, adaptive hashing algorithm with a built-in salt, designed specifically to resist brute-force and rainbow-table attacks even if the password hash database is stolen. A fast hash like SHA-256 is designed for speed, which is exactly the wrong property for password storage — it makes brute-forcing millions of guesses per second feasible.

**Q29. What happens in this system if a user's account is deactivated while they still hold a valid, unexpired token?**
The authentication dependency re-checks the user's `is_active` flag from the database on every single request, not just at login — so a deactivated account is rejected (`403`) immediately on its very next request, even though the JWT itself is still cryptographically valid and unexpired.

**Q30. How does logout work given that JWTs are normally stateless?**
`POST /auth/logout` invalidates the current session's refresh token server-side, so it can no longer be exchanged for a new access token — this is what makes the "logout" meaningful despite the access token itself being a self-contained, unrevocable-by-default artifact until it naturally expires (which is why the access token's lifetime is kept short).

**Q31. How is password change handled, and what validation applies?**
`PUT /auth/password` requires the caller to already be authenticated and to supply their current password (re-verified against the stored hash) alongside the new one; the new password must differ from the current one and meet a minimum length/complexity policy, enforced by the service layer, not just the frontend form.

**Q32. Why does this project rate-limit `POST /auth/login` specifically, and not every endpoint?**
Login is the one endpoint an unauthenticated attacker can call repeatedly to brute-force a password, since every other endpoint already requires a valid token to reach. It's rate-limited to 5 attempts per 60-second window per client IP, closing off that specific brute-force vector without penalizing normal authenticated usage elsewhere.

---

## F. JWT (Q33–Q38)

**Q33. What is a JWT, structurally?**
A JSON Web Token is three base64url-encoded segments separated by dots: a header (algorithm/type), a payload (claims — in this project, the user's ID and a token-type marker), and a signature computed over the first two segments using a secret key, which lets the server verify the token hasn't been tampered with.

**Q34. Why does this project use two tokens (access + refresh) instead of one long-lived token?**
A single long-lived token would mean a stolen token stays valid for a long time with no easy way to limit the damage. Splitting into a short-lived access token (limiting the exposure window if stolen) and a separate, rotatable refresh token (used only to mint new access tokens, and invalidated on logout) balances security against not forcing the user to re-enter credentials constantly.

**Q35. What does "refresh token rotation" mean, and does this project implement it?**
Rotation means each time a refresh token is used to obtain a new access token, the refresh token itself is also replaced with a new one, invalidating the old one — so a leaked, unused-yet refresh token has a limited window of usefulness. This project rotates the refresh token on every use.

**Q36. How does the backend verify a JWT's authenticity, and what happens on a malformed or expired token?**
It decodes the token using the shared `JWT_SECRET_KEY` and configured algorithm; the underlying JWT library itself checks the signature and the `exp` (expiry) claim. Any failure — bad signature, malformed structure, or expired token — raises a `JWTError`, which the authentication dependency catches and re-raises as `401 Unauthorized`.

**Q37. Where should a JWT be stored on the client, and what are the tradeoffs?**
Options are memory/in-JS-variable (safest against XSS but lost on page refresh), `localStorage` (persists across refresh but readable by any script on the page, i.e. vulnerable if an XSS bug exists), or an httpOnly cookie (invisible to JavaScript, but requires CSRF protection instead). This project's frontend stores tokens client-side to survive a page reload, which is the standard pragmatic tradeoff for an SPA that doesn't otherwise implement CSRF tokens.

**Q38. Can a JWT be revoked before it expires?**
Not the access token itself directly, by design — it's a self-contained, stateless credential. This project mitigates that by keeping access tokens short-lived (so an un-revocable window is small) and revoking the *refresh* token on logout, which prevents a *new* access token from being minted, even though any already-issued access token keeps working until its own expiry.

---

## G. RBAC (Q39–Q44)

**Q39. What is Role-Based Access Control, and what roles exist in this system?**
RBAC restricts actions based on a user's assigned role rather than per-user permission lists. This system has four roles: Student, Teacher, Parent, and Admin, each with a distinct, non-overlapping set of intended capabilities.

**Q40. How is a role check actually enforced in this codebase — show the mechanism.**
Via a `require_roles(...)` FastAPI dependency attached to a router, e.g. `dependencies=[Depends(require_roles("admin"))]` — it inspects the resolved current user's role and raises `403 Forbidden` if it isn't in the allowed set, before the route function body ever executes.

**Q41. Why is role-only access control insufficient for some endpoints in this system — give a concrete example.**
Because "the caller is a Parent" doesn't tell you *which* student's data they may see. `GET /attendance/me` requires the role check *and* a service-layer check that the requested `student_id` actually appears in a `parent_student_link` row belonging to that specific parent — omitting the second check would let any Parent view any student's data just by guessing an ID.

**Q42. Where in the layered architecture do ownership checks live, and why not in the router?**
In the service layer, alongside the rest of the business logic — routers only shape HTTP request/response and delegate. Putting an ownership check in the router would scatter business rules across two layers and make it easy to accidentally add a new endpoint that forgets the check; centralizing it in services keeps the rule enforced everywhere that calls that service method.

**Q43. What HTTP status code does this system return when a resource exists but the caller isn't allowed to see it, and why might `404` sometimes be preferred over `403`?**
Typically `403 Forbidden` for an authenticated-but-wrong-role/owner request. Some endpoints intentionally return `404 Not Found` instead when even confirming a resource *exists* would leak information to an unauthorized caller (e.g. one student probing whether another student's ID is valid) — this system uses that pattern for a Student attempting to access another student's exam.

**Q44. How does this project's test suite specifically verify RBAC, beyond just testing the "happy path"?**
Every RBAC/ownership boundary has an explicit **negative** test — e.g. a test that logs in as a Teacher and asserts that calling an Admin-only endpoint returns `403`, and a test that logs in as an unlinked Parent and asserts that requesting another child's attendance also returns `403` — proving the rejection actually happens, not just assuming it from the code.

---

## H. APIs (Q45–Q51)

**Q45. What architectural style does this project's API follow, and what does that mean in practice?**
REST (Representational State Transfer) over HTTP/JSON — resources (students, exams, invoices) are addressed by URL, and operations on them map to HTTP methods (`GET` read, `POST` create, `PUT` update, `DELETE` remove), with statelessness meaning every request carries all the context (via the JWT) needed to process it, with no server-side session state required.

**Q46. How many endpoints does this system expose, and how are they organized?**
82 REST endpoints across 11 domains — authentication, users, reference data, scheduling, attendance, exams, results, fees, notifications, reports, and health — each domain living in its own router file and versioned under `/api/v1`.

**Q47. What HTTP status codes does this API use, and what does each signal?**
`200`/`201` success (200 for reads/updates, 201 for creates); `204` success with no response body (e.g. a delete); `401` missing/invalid/expired token; `403` valid token but insufficient role/ownership; `404` not found (or hidden); `409` a business-rule conflict (e.g. duplicate attendance, an already-resolved change request); `422` request validation failure; `500` an unexpected server error.

**Q48. How does this API handle pagination, and where is it used?**
List endpoints (e.g. `GET /users/students`, `GET /exams`) accept `page` and `page_size` query parameters and return a consistent `PaginatedResponse` shape (`items`, `total`, `page`, `page_size`), so no list endpoint ever returns an unbounded result set regardless of how large the underlying table grows.

**Q49. Give an example of an endpoint in this system that wasn't in the original project proposal but was added during implementation, and explain why.**
`GET /schedule/change-requests` (the Admin approval queue listing) — the original scope included creating and resolving a change request, but implementation revealed there was no way for an Admin to actually *see* pending requests to act on them, so the endpoint was added and documented as a "Derived" addition with its justification.

**Q50. How are file downloads (PDFs, Excel, CSV) exposed through this REST API?**
As `GET` endpoints that return a binary `Response` with the appropriate `media_type` (`application/pdf`, the Excel MIME type, or `text/csv`) and a `Content-Disposition: attachment; filename="..."` header, generated on demand from live data at request time — nothing is pre-generated or stored on disk.

**Q51. Why does this project prefer explicit response schemas over returning ORM models directly from an endpoint?**
Returning an ORM model directly risks leaking internal columns never meant for the client (e.g. a password hash), couples the API's public contract to the database schema (so a column rename would silently break every consumer), and bypasses FastAPI's own response validation — an explicit Pydantic response schema controls exactly what's serialized.

---

## I. SQLAlchemy (Q52–Q58)

**Q52. What is SQLAlchemy, and what role does it play in this project?**
SQLAlchemy is a Python SQL toolkit and Object-Relational Mapper. This project uses its ORM layer to define every database table as a Python class (a "model"), and its Core query-building API (`select(...)`) inside repository methods to write every query the application executes.

**Q53. What is the "Repository Pattern," and how does this project apply it with SQLAlchemy?**
The Repository Pattern isolates all data-access logic behind a dedicated class per domain, so the rest of the application never constructs a SQLAlchemy query directly. This project enforces that literally: `app/repositories/` is the *only* place any `select(...)`/`session.add(...)` call is written; services call repository methods and never touch the session directly.

**Q54. What is the N+1 query problem, and how would you recognize/avoid it in this codebase?**
It's the pattern of running one query to fetch a list, then one additional query per item to fetch each item's related data — e.g. fetching every attendance record's student name one query at a time instead of in one batch. This project explicitly avoids it via batch-lookup repository methods (e.g. `list_students_by_ids()`, used once per report rather than once per row) and via SQLAlchemy's `joinedload`/`selectinload` where relationships are accessed together.

**Q55. What is the difference between `session.flush()` and `session.commit()`, and which does this project's repository layer use?**
`flush()` sends pending SQL to the database (so autogenerated values like a UUID default become available) without ending the transaction; `commit()` ends the transaction, persisting the changes permanently. This project's convention is that repositories only ever `flush()`; only the service layer calls `commit()`, because the service owns the transaction boundary — a repository method might be one of several calls inside a single atomic business operation.

**Q56. How does this project translate a database-level constraint violation into a meaningful API error?**
By catching SQLAlchemy's `IntegrityError` in the service layer immediately around the `commit()` call, rolling back the session, and raising an appropriate `HTTPException` (typically `409 Conflict`) with a human-readable message — e.g. attempting to mark duplicate attendance raises the database's unique-constraint violation, which is caught and reported as "Attendance already recorded for this date."

**Q57. What is Alembic, and how does it relate to SQLAlchemy in this project?**
Alembic is SQLAlchemy's migration tool — it generates and applies versioned, incremental schema changes. Every schema change in this project ships as a reviewed Alembic revision (10 exist, in a single linear chain), never as manual DDL run directly against a database, so the schema's history is fully reproducible from an empty database.

**Q58. Explain a case in this project where a Pydantic-level validation rule was insufficient and had to be enforced in the service layer using SQLAlchemy data instead.**
A `Semester`'s partial update (`SemesterUpdate`) allows supplying only one of `start_date`/`end_date`. Pydantic alone can't validate "start before end" on a partial payload, since it might only see one of the two fields — the service layer fetches the semester's *existing* row via SQLAlchemy, computes the effective new start/end (falling back to the existing value for whichever field wasn't supplied), and only then validates the order.

---

## J. Database Design (Q59–Q65)

**Q59. How many tables does this schema have, and what normalization level does it target?**
26 tables, normalized to Third Normal Form (3NF) — every non-key attribute depends on the whole primary key and nothing else, eliminating redundant, update-anomaly-prone data duplication.

**Q60. Walk through the relationship between User and the four role profile tables.**
`user` is the base identity table (email, password hash, role, active flag); `student`, `teacher`, `parent`, and `admin` are each a separate table in a 1:1 relationship with `user` via a `user_id` foreign key, holding only the profile fields relevant to that specific role, rather than one wide table with many always-partially-null columns.

**Q61. Why is `parent_student_link` a separate join table instead of a direct foreign key on `student` pointing to a `parent`?**
Because the relationship is many-to-many, not one-to-many — a parent may be linked to multiple children, and (structurally) a student could have more than one linked parent. A direct FK on `student` could only express "one parent per student," which doesn't match that requirement.

**Q62. Why does `result` store `exam_id` as a nullable foreign key when `(student_id, course_id, semester_id)` is already the table's real business key?**
`exam_id` exists purely for traceability and the Admin approval queue's grouping/display — it records which exam most recently produced or updated the result row. It's nullable and secondary specifically so that the uniqueness/business-key logic (one authoritative result per student/course/semester) never depends on it.

**Q63. Explain the difference in delete policy between reference/catalog data and identity data in this schema, and why they differ.**
Department/Course/Room/Semester use hard `DELETE` with `ON DELETE RESTRICT` — they're catalog data, safe to remove once nothing references them, and adding soft-delete would need a schema change with no real benefit. User/Student/Teacher/Parent are never hard-deleted, only deactivated (`is_active = false`) — because they're identity/audit records with historical Attendance/Result/Payment rows depending on them, which must remain queryable and attributable even after the person leaves the institution.

**Q64. How does this schema prevent two overlapping schedule entries in the same room?**
Two layers: a database unique index on `(room_id, day_of_week, start_time)` catches exact-start-time duplicates, and a service-layer overlap check (`existing.start_time < new.end_time AND new.start_time < existing.end_time`) catches entries that overlap on offset, non-identical start times — which the unique index alone cannot detect.

**Q65. Why are attendance percentage and GPA not stored as columns anywhere in this schema?**
Because a stored, cached value can silently drift out of sync with the records it's derived from the moment any underlying row changes (a corrected attendance record, a newly published result) without also updating the cache. Both are computed live, at query time, directly from the underlying `attendance_record`/`result` rows every time they're requested.

---

## K. Testing (Q66–Q72)

**Q66. What is the difference between a unit test and an integration test, and how many of each does this project have?**
A unit test exercises one unit of logic in isolation (here: a service method, with its repositories replaced by stubs, no real database) — 24 files exist for this. An integration test exercises the full stack together (a real HTTP request through FastAPI to a real, disposable PostgreSQL database and back) — 8 files exist for this. Together they total 477 backend tests.

**Q67. Why does this project stub repositories in unit tests instead of mocking the database connection directly?**
Stubbing at the repository boundary keeps the unit test focused on the service's actual business logic (the thing being tested) while completely avoiding any real I/O, and it matches the project's own layering — since services are defined to only ever call repositories, stubbing exactly that boundary is the natural seam.

**Q68. Why does this project use a disposable database for integration tests instead of mocking the ORM?**
Because the value of an integration test is proving the full path really works — including real SQL constraint enforcement (unique constraints, foreign keys) that a mock could never accidentally violate. Using a real, throwaway PostgreSQL database (created, migrated, tested, and dropped) gets that assurance without ever risking a developer's actual data.

**Q69. Give an example of a negative test in this suite and explain what it proves that a positive test alone would not.**
A test that logs in as a Teacher and asserts `POST /users/students` (Admin-only) returns `403`. A positive test (Admin succeeds) only proves the feature works for the intended user — it says nothing about whether an *unintended* user is actually blocked, which is the property RBAC exists to guarantee.

**Q70. How does this project test a workflow state machine, such as the exam lifecycle?**
By testing both valid and invalid transitions explicitly — e.g. asserting a draft exam can be edited/deleted and a published one cannot, and asserting that submitting results for an exam that isn't fully graded yet is rejected with `409` — rather than only testing the "happy path" sequence of transitions.

**Q71. What does it mean for this project's CI to check for "schema drift," and why is that itself a kind of test?**
It runs `alembic revision --autogenerate` against a fully-migrated database and fails the build if it detects any difference between the live schema and the current ORM models. It's effectively an automated test that the migration history and the code describing it have never silently diverged — a class of bug that wouldn't be caught by ordinary business-logic tests at all.

**Q72. How would you test a bug fix like "a Teacher wasn't notified when their schedule change request was resolved" to prove it's actually fixed?**
Write (or extend) a unit test that stubs the notification dispatcher and asserts it was called with the expected arguments (teacher's user ID, course name, decision) after calling `resolve_change_request` for both the approve and reject paths, plus an integration test that resolves a real request through the API and then asserts the resolving teacher's `GET /notifications` feed actually contains the new message — proving it end-to-end, not just at the unit boundary.

---

## L. Software Engineering (Q73–Q79)

**Q73. What development methodology did this project follow?**
A sequential, milestone-based process — requirements analysis and architecture design were written and reviewed before implementation began, and implementation proceeded through discrete milestones (foundations, users, scheduling, exams, attendance, grading, results, fees, notifications, dashboards, hardening), each reviewed and approved before the next started.

**Q74. What is the Single Responsibility Principle, and how is it reflected in this project's layering?**
A unit of code should have one reason to change. This project's Router/Service/Repository split is a direct application: a router changes only if the HTTP contract changes, a service only if a business rule changes, a repository only if a query's shape changes — mixing them (e.g. business logic in a router) would give one file multiple, unrelated reasons to change.

**Q75. What is technical debt, and how did this project manage the debt of scope changes discovered mid-implementation?**
Technical debt is the implied cost of choosing an easy-but-incomplete solution now versus a more correct one later. This project's convention was to never silently accumulate it: any capability implementation revealed as missing (e.g. no endpoint let an Admin see pending schedule-change requests) was either built immediately and documented as a deliberate scope addition, or explicitly logged as an accepted, named limitation — never left as an undocumented gap.

**Q76. What is the purpose of a "Proposal vs. Engineering Additions" document, and why maintain one?**
It's a running ledger of every capability built beyond the original written proposal, classified (e.g. a mechanical prerequisite vs. a design enhancement) and justified in the same change that introduced it. It exists so that, at any point, the actual delivered scope can be checked against the original proposal precisely, rather than the two silently drifting apart with no record of why.

**Q77. What is a code review checklist, and does this project use one?**
A checklist of properties to verify before considering a change complete (tests passing, no regressions, RBAC preserved, docs updated). This project uses a documented milestone-verification checklist, run and cross-checked against the governing design documents before any milestone is marked complete — a self-review step, not a substitute for actual sign-off.

**Q78. What is the difference between verification and validation, and give an example of each from this project.**
Verification asks "did we build the thing right?" (e.g. does `POST /attendance` actually enforce the documented duplicate-prevention rule — checked by tests). Validation asks "did we build the right thing?" (e.g. does the Parent portal actually give parents the visibility into "results & schedule" that the original proposal promised — checked by the production-readiness gap-closure audit against the proposal's stated intent).

**Q79. Why does this project separate "what to build" (design documents) from "how it's coded" (a coding-conventions document), and what's the benefit?**
Design documents (requirements, architecture, database design) describe the target system's shape; a separate conventions document governs the process and style of writing code to get there (layering rules, naming conventions, testing discipline). Separating them means a future contributor can look up *why* a feature exists in one place and *how* to add to it consistently in another, without either document trying to do both jobs at once.

---

## M. Project Architecture (Q80–Q86)

**Q80. Describe this project's overall architecture in one sentence.**
A decoupled client-server architecture: a React single-page application communicating exclusively over a versioned JSON REST API with a layered FastAPI backend (Router → Service → Repository), backed by PostgreSQL.

**Q81. Why was a layered monolith chosen over a microservices architecture for this project?**
Given the project's scope (a single institution, a single deployable team, a single deadline), a monolith avoids distributed-systems complexity (network calls between services, eventual consistency, service-discovery) while the internal layering still keeps concerns cleanly separated and independently testable — microservices would add operational overhead without a matching benefit at this scale.

**Q82. Trace the full request lifecycle for `POST /attendance` from HTTP request to database write.**
The request hits the FastAPI router; the JWT dependency resolves the current user; a `require_roles("teacher")` dependency checks the role; the Pydantic `AttendanceMarkRequest` schema validates the body; the router calls `attendance_service.mark_attendance()`; the service checks the teacher actually owns the class session, validates every student is enrolled and active, checks for duplicates, then calls `attendance_repo.create_record()` for each row; the repository issues the SQLAlchemy insert and flushes; the service commits the transaction and (after commit) dispatches any resulting notification.

**Q83. Why does this project's frontend keep server state exclusively in React Query rather than duplicating it into component state?**
Duplicating server data into local/component state creates two sources of truth that can drift apart (e.g. a stale cached count after another action changes it). React Query owns caching, refetching, and invalidation in one place, keyed consistently, so every component reading the same data always reflects the same, current value without manual synchronization code.

**Q84. What does "independently deployable tiers" mean for this project, and why does it matter?**
The frontend builds to a static asset bundle deployable from any CDN/static host; the backend is a stateless, containerized service deployable and scalable on its own. This matters because either tier can be redeployed, rolled back, or scaled without requiring the other to change in lockstep, as long as the versioned API contract between them is respected.

**Q85. What is a cross-cutting concern, and name three implemented as middleware/dependencies in this project rather than duplicated per-router.**
A cross-cutting concern is a piece of behavior needed by many otherwise-unrelated parts of the system. This project implements JWT authentication, role-based authorization, and global error handling as shared FastAPI dependencies/middleware applied uniformly, rather than each of the 11 routers reimplementing its own version of each.

**Q86. If this system needed to scale to handle significantly more concurrent users, what is the one documented architectural limitation you'd need to address first, and why?**
The login rate limiter is currently in-process memory, so multiple backend replicas behind a load balancer wouldn't share rate-limit state — an attacker could get 5 attempts per replica rather than 5 total. It's the one component in an otherwise horizontally-scalable, stateless backend that assumes a single process, and would need to move to a shared store (e.g. Redis) first.

---

## N. Security (Q87–Q93)

**Q87. List the main security measures implemented in this project.**
Bcrypt password hashing; short-lived, rotating JWTs; server-side RBAC and ownership re-verification on every request; rate-limited login; Pydantic validation on every request body; exclusive use of the SQLAlchemy ORM (no raw SQL) to prevent injection; production-only disabling of API documentation endpoints; structured logging that never records passwords, raw tokens, or full payment details.

**Q88. How does this project protect against SQL injection?**
By never constructing SQL from string-interpolated user input anywhere in the codebase — every single database query goes through the SQLAlchemy ORM/Core query-building API, which parameterizes values automatically, making injection via a crafted input string structurally impossible rather than merely discouraged by convention.

**Q89. How does this project protect against a compromised/leaked API schema being used to probe for weaknesses in production?**
By disabling `/docs`, `/redoc`, and `/openapi.json` automatically whenever `ENVIRONMENT=production`, via the existing `Settings.is_production` configuration property — the full endpoint surface and request/response schema are only discoverable in non-production environments (development, CI, grading/demo).

**Q90. What data does this project explicitly avoid ever writing to logs, and why?**
Passwords, raw JWTs, and full payment/financial details. Logging any of these would turn the log storage itself into a high-value target — anyone with log access (which is often broader than database access) could otherwise harvest credentials or session tokens directly.

**Q91. What is the difference between authentication and authorization, and where does each fail in this system with a different HTTP status code?**
Authentication answers "who are you" — failing (missing/invalid/expired token) returns `401 Unauthorized`. Authorization answers "are you allowed to do this" — failing (valid identity, wrong role/ownership) returns `403 Forbidden`. Conflating the two into one status code would make it harder for a legitimate client to distinguish "log in again" from "you don't have permission," so this system keeps them distinct.

**Q92. What secrets does this project require, and how are they managed?**
`JWT_SECRET_KEY` (signs tokens) and `DATABASE_URL` (contains DB credentials) are the two sensitive values; both are supplied via environment variables (`backend/.env`, which is git-ignored) and never committed to source control — only a non-secret `.env.example` placeholder file is tracked, documenting which variables exist without exposing real values.

**Q93. Describe a genuine security-relevant bug this project's own QA process found and fixed, and why it mattered.**
An audit found `CourseCreate.credit_hours` and `RoomCreate.capacity` had no lower-bound validation, so a negative or zero value could be submitted and accepted. While not an authentication/authorization bypass, it's a data-integrity/input-validation gap that could corrupt downstream calculations (GPA is credit-hour-weighted) — fixed with a Pydantic `Field(ge=1)` constraint and covered by a new regression test, illustrating that security review in this project extends to validation correctness, not only access control.

---

## O. Deployment (Q94–Q100)

**Q94. What containerization strategy does this project use?**
Docker, with two purposes: a `docker-compose.yml` for local development (Postgres + a live-reloading backend + the Vite dev server, all bind-mounted for fast iteration), and separate, standalone `Dockerfile.backend`/`Dockerfile.frontend` for building production-style images independent of that dev-only compose setup.

**Q95. Describe the production-style backend image, and how it differs from the local dev setup.**
`Dockerfile.backend` is a `python:3.12-slim` image that installs pinned dependencies, copies the application source, and runs `uvicorn app.main:app` **without** `--reload` — a static, immutable image suitable for deployment. The local dev compose setup instead bind-mounts the source and runs `--reload`, trading image immutability for fast iteration speed.

**Q96. How is the frontend intended to be deployed in production, and what does the production Dockerfile actually produce?**
Per the architecture, as a static asset bundle served from a CDN/static host — no server-side rendering. `Dockerfile.frontend` is a multi-stage build: it runs `npm run build` in a Node stage, then copies only the compiled `dist/` output into an `nginx:alpine` image, which is one concrete way to serve that static bundle, not the only one.

**Q97. What does this project's CI verify on every push, and why run it in CI rather than relying on developers to run it locally?**
Backend CI applies all Alembic migrations to a disposable Postgres service container, checks for schema drift, and runs the full pytest suite; frontend CI type-checks, lints, runs the Vitest suite, and confirms the production build succeeds. Running it in CI guarantees every change is checked under identical, reproducible conditions before merge, regardless of whether an individual contributor remembered (or was able) to run the full suite locally.

**Q98. Why does this project's CI run migrations against a disposable database rather than reusing one persistent CI database across runs?**
A persistent database could accumulate state across runs (leftover rows, a stale schema state) that masks a real bug or produces a flaky pass/fail. A fresh, disposable database per run guarantees every CI execution starts from the exact same known-empty state, matching how a real first-time deployment would also apply migrations to a brand-new database.

**Q99. What environment-specific configuration changes between development and production, and how is that controlled?**
The single `ENVIRONMENT` variable — set to `production`, it disables the interactive API docs endpoints. Alongside it, `DATABASE_URL`, `JWT_SECRET_KEY`, and `FRONTEND_ORIGIN` (CORS) must all be set to real production values rather than the development placeholders, and `alembic upgrade head` is expected to run as an explicit deployment step before the new backend version starts accepting traffic.

**Q100. If asked to deploy this system for real institutional use tomorrow, what is the single most important documented gap you would close first, and why?**
The in-memory login rate limiter, if deploying behind multiple backend replicas — it's the one place the system's otherwise-stateless, horizontally-scalable design has a single-process assumption baked in, and it's specifically a security control (brute-force protection), so under-provisioning it silently weakens actual account security rather than just being a performance nitpick.
