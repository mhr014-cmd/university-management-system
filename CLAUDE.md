# CLAUDE.md

Guidance for Claude Code (and any future contributor) working in this repository.

This file governs *how* code is written in this project. For *what* to build, always defer to the design documents in `docs/` — this file does not restate requirements, it enforces conventions on top of them.

**Authoritative design docs (read before implementing anything):**
- [docs/product_proposal.pdf](docs/product_proposal.pdf) — original specification
- [docs/Requirement_Analysis.md](docs/Requirement_Analysis.md) — numbered functional/non-functional requirements (FR-xxx, NFR-xxx)
- [docs/System_Architecture.md](docs/System_Architecture.md) — architecture, auth/authz flows, folder structure
- [docs/Database_Design.md](docs/Database_Design.md) — full schema, relationships, constraints
- [docs/Implementation_Roadmap.md](docs/Implementation_Roadmap.md) — milestone build order

If a requested change conflicts with these documents, flag the conflict rather than silently deviating. If a requirement is ambiguous, check `Requirement_Analysis.md` §14 (Anything Unclear) first — it may already be documented there.

---

## 1. Project Overview

**ICT Education — University Management System** is a web platform that consolidates university operations (attendance, exams, results, fees, scheduling) into a single system, replacing spreadsheets, email-based results, and siloed finance tools.

- **Roles:** Student, Teacher, Admin, Parent — each with distinct, API-enforced permissions.
- **Architecture:** Decoupled SPA frontend + REST API backend + PostgreSQL, per `System_Architecture.md` §1.
- **Deadline-sensitive:** see `Implementation_Roadmap.md` for milestone sequencing and cut-scope priorities. Do not reorder milestones without checking their listed dependencies.

---

## 2. Technology Stack

Fixed by the proposal (`System_Architecture.md` §12) — do not substitute without an explicit user request:

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript |
| Styling | TailwindCSS |
| API data layer (frontend) | React Query |
| Backend | FastAPI (Python 3.12) |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Auth | JWT (access + refresh tokens), role-based access control |
| API style | REST, JSON, versioned under `/api/v1` |

---

## 3. Coding Standards

- Follow the layered architecture defined in `System_Architecture.md` §2–§3: routers/pages never contain business logic; business logic never contains raw SQL; data access never contains authorization decisions.
- Every non-trivial function has a single, clear responsibility. Do not fold unrelated concerns (e.g., validation + business rule + notification dispatch) into one function — split by layer as designed.
- No commented-out code, no dead code paths, no speculative abstractions "for later." Build exactly what the current milestone requires (see `Implementation_Roadmap.md`).
- Default to writing no comments. Add a comment only to explain a non-obvious *why* (a business rule from `Requirement_Analysis.md`, a workaround, a subtle constraint) — never to restate what the code does.
- Type everything. Python: full type hints on all function signatures and Pydantic models. TypeScript: no `any`; prefer explicit interfaces/types over inferred `object`.
- Business rules (BR-xxx) and validation rules (VR-xxx) from `Requirement_Analysis.md` must be implemented at the service layer (backend), never trusted to the frontend alone (see NFR-001).

---

## 4. Naming Conventions

- **Database tables/columns:** `snake_case`, singular table names (`student`, not `students`), matching `Database_Design.md` exactly. Foreign keys named `<referenced_entity>_id` (e.g., `class_session_id`).
- **Python:** `snake_case` for functions/variables/modules, `PascalCase` for classes (models, schemas, services).
- **TypeScript/React:** `camelCase` for variables/functions, `PascalCase` for components and types/interfaces, `useX` prefix for hooks.
- **API routes:** `kebab-case` or plural nouns matching the exact endpoint paths listed in `Requirement_Analysis.md` §8 / `Implementation_Roadmap.md` (e.g., `/users/students/{id}`). Do not invent alternate route shapes for the same resource.
- **Enums (status/role/type fields):** lowercase snake_case values (`submitted`, `approved`, `published`) matching the states defined in `Database_Design.md` §6.
- **Files:** one primary export per file where practical; file name matches the primary export's name (`exam_service.py`, `ExamRoom.tsx`).

---

## 5. Folder Conventions

Follow the structure defined in `System_Architecture.md` §7 exactly — do not introduce parallel or competing folder layouts:

```
backend/app/{core,db,models,schemas,routers,services,repositories,middleware,notifications,pdf}
frontend/src/{app,pages,features,components,auth,styles}
```

- One module per domain (auth, users, exams, attendance, results, fees, schedule, notifications, reports) — mirrored consistently across `models/`, `schemas/`, `routers/`, `services/`, and `frontend/src/features/`. Note: `reports` has no dedicated model (it's aggregation-only over existing tables), so it has a `routers/reports.py` + `services/report_service.py` pair but no `models/report.py` or `repositories/report_repository.py` — this is intentional, not an oversight.
- New domains are not introduced outside what `Database_Design.md` / `Requirement_Analysis.md` define, without confirming scope first.
- Tests live alongside their domain (`backend/tests/`, `frontend/tests/`), mirroring the source structure, not colocated ad hoc.

---

## 6. Backend Conventions

- **Routers** (`app/routers/`): handle request/response shaping and delegate immediately to services. No business logic, no direct ORM queries in routers.
- **Services** (`app/services/`): own business rules and workflow state transitions (e.g., result submit → approve → publish per BR-002; exam delete-if-unpublished per BR-003). Services call repositories, never the ORM session directly.
- **Repositories** (`app/repositories/`): all SQLAlchemy queries live here. No business logic in repositories.
- **Schemas** (`app/schemas/`): every request body and response model is a Pydantic schema. Never return ORM models directly from a router.
- **Migrations:** every schema change is a new Alembic revision, generated and reviewed — never hand-edited after generation, never applied as manual DDL against a running database.
- **RBAC and ownership checks** (`System_Architecture.md` §6): applied via dependency injection on every protected route. Role-only checks are insufficient for `/me`-scoped and parent-linked endpoints — verify ownership/linkage in the service layer on every request, not just at login.
- **Async I/O:** PDF generation (transcripts, invoices) and notification dispatch run as background tasks, not inline in the request path (`System_Architecture.md` §2.4).

---

## 7. Frontend Conventions

- **Server state** lives only in React Query — never duplicated into component state or a global store.
- **Client-only UI state** (modals, form drafts, active tab) uses local component state or a lightweight context — not React Query.
- **Pages** (`src/pages/`) correspond 1:1 to the screens listed in `Requirement_Analysis.md` §7. Do not add or remove screens without updating that document.
- **Features** (`src/features/`) wrap each API domain in typed React Query hooks (`useExams`, `useAttendance`, etc.) — components call these hooks, never `fetch`/`axios` directly.
- **Auth** (`src/auth/`): token attachment, silent refresh, and route guarding are centralized here — not reimplemented per page.
- **Role-based UI composition:** shared shells (Dashboard, Profile, Notifications) render role-specific widgets conditionally; do not fork into four separate app trees per role.
- Client-side RBAC hiding of UI elements is a UX convenience only — it is never a substitute for server-side enforcement.

---

## 8. Git Conventions

- Commit messages are imperative, present tense, scoped to one logical change (`Add exam grading endpoint`, not `Fixed stuff`).
- Never amend or force-push shared/published commits.
- Never commit secrets, `.env` files, or credentials — use `.env.example` for documented placeholders only.
- Reference the relevant milestone or requirement ID in commit messages where useful (e.g., `Implement result approval workflow (BR-002, M7)`).
- Feature branches map to milestones or a coherent slice of one (`feat/m6-exam-builder`), not to arbitrary daily snapshots.
- Do not mix schema migrations with unrelated feature code in the same commit.
- A commit that introduces anything not explicitly required by the proposal (endpoint, page, middleware, utility, UI component) is not complete until `docs/Proposal_vs_Engineering_Additions.md` is updated in that same commit — see Section 9.

---

## 9. Documentation Conventions

- Design documents in `docs/` are the source of truth; code should not silently diverge from them. If implementation reveals a design doc is wrong or incomplete, update the doc in the same change, don't just patch around it in code.
- No new standalone `.md` files unless explicitly requested — extend the existing docs (`Requirement_Analysis.md`, `System_Architecture.md`, `Database_Design.md`, `Implementation_Roadmap.md`) instead of creating parallel ones.
- Code comments follow the "why, not what" rule from Section 3 — they are not a substitute for keeping `docs/` accurate.
- Any newly resolved ambiguity from `Requirement_Analysis.md` §14 should be reflected back into that section (mark resolved, note the decision) rather than left stale.
- **Engineering additions are documented immediately, in the same commit, never deferred to a later audit.** Any endpoint, page, middleware, utility, or UI component added that is not explicitly required by `docs/product_proposal.pdf` gets an entry in `docs/Proposal_vs_Engineering_Additions.md` — classified (Required / Derived / Design Enhancement per that document's definitions) and, for anything not permanent, given an explicit disposition (keep vs. remove-when) — before the commit that introduces it, not discovered retroactively during a traceability review (see the Milestone 0 review that found the theme toggle and Dashboard health widget undocumented for a concrete example of what this rule prevents).

---

## 10. Testing Conventions

- Every service-layer business rule (BR-xxx) and validation rule (VR-xxx) gets at least one corresponding test.
- Backend: unit tests for services (business logic in isolation, repositories mocked/stubbed), integration tests for routers (full request → DB → response cycle against a test database).
- Frontend: component tests for pages/features with critical interaction logic (exam timer, grading form, approval workflow); avoid testing implementation details of React Query itself.
- RBAC and ownership checks (Section 6) require explicit negative tests — verify that a wrong-role or wrong-owner request is rejected, not just that the correct-role request succeeds.
- Workflow state machines (exam draft→published, result submitted→approved→published) require tests covering both valid transitions and rejected invalid transitions.
- Do not merge a milestone as "complete" per `Implementation_Roadmap.md` without tests covering its stated APIs and business rules.

---

## 11. Performance Guidelines

- Attendance percentage and GPA are computed at query time from underlying records, never cached as a stored denormalized column (per `Database_Design.md` §3 normalization rationale) — if performance requires caching later, that is a deliberate, documented tradeoff, not a default.
- Use the indexes defined in `Database_Design.md` §9 — do not add ad hoc indexes without checking that list first, and do not skip adding an index the doc already specifies.
- List endpoints (`GET /users/students`, `GET /exams`, etc.) must support pagination/filtering rather than returning unbounded result sets, even though the proposal's API spec doesn't detail query parameters — this is a necessary implementation default.
- PDF generation and notification dispatch are background/async operations (Section 6) specifically to keep request latency low on the endpoints that trigger them.
- Avoid N+1 query patterns in repositories — use SQLAlchemy eager-loading (`joinedload`/`selectinload`) for relationships accessed together (e.g., Exam + Questions, Result + Student + Course).

---

## 12. Security Guidelines

Per `System_Architecture.md` §11:

- Passwords hashed with a strong adaptive algorithm (bcrypt/argon2) — never stored or logged in plaintext.
- Access tokens short-lived; refresh tokens rotated on use and invalidated on logout.
- All database access via parameterized queries through the SQLAlchemy ORM — no raw string-interpolated SQL, ever.
- Every request body validated against a Pydantic schema before reaching business logic.
- RBAC and ownership are enforced server-side on every request; a deactivated user (`is_active = false`) must fail authorization immediately even with a still-valid token.
- No secrets committed to source control — configuration via environment variables / secret managers only.
- No sensitive data (passwords, raw JWTs, full payment details) in logs (Section 13 below).
- Consider rate limiting on `/auth/login` and other public endpoints — flagged as an unspecified gap in the proposal (`Requirement_Analysis.md` §14, item 13); apply a reasonable default and note the assumption.

## 13. Logging & Error Handling

- All backend errors surface through the global exception handlers into a single consistent JSON error shape (`System_Architecture.md` §9) — do not format ad hoc error responses per router.
- Use structured (JSON) logs; log audit events (result approval, payment recording, account creation/deactivation, schedule changes) as discrete entries per `System_Architecture.md` §10.
- `4xx` responses log at lower severity than `5xx`; `5xx` responses always log the full stack trace server-side and never leak internals to the client response body.

---

## 14. Rules for Future Code Generation

When asked to generate code in this repository:

1. **Check the milestone first.** Consult `Implementation_Roadmap.md` to confirm what belongs in the current milestone and what its stated dependencies are — do not build ahead of unmet dependencies (e.g., do not implement Exams before Scheduling exists).
2. **Match the schema exactly.** Table names, column names, types, and constraints must match `Database_Design.md` — do not invent columns or relax constraints for convenience.
3. **Match the API contract exactly.** Endpoint paths, methods, and access-role restrictions must match `Requirement_Analysis.md` §8 / `Implementation_Roadmap.md` — do not add, rename, or restructure endpoints without flagging the deviation.
4. **Respect the layer boundaries** in Sections 6–7 — no business logic in routers/components, no raw queries outside repositories, no server state outside React Query.
5. **Implement every referenced business/validation rule** (BR-xxx, VR-xxx) at the service layer when touching a related feature, not just the happy path.
6. **Never weaken RBAC or ownership checks** to make a feature "work" faster — if an endpoint feels awkward under RBAC, raise it as a design question rather than bypassing the check.
7. **Do not invent scope.** If a request implies a feature not covered by `docs/`, say so and ask, rather than silently expanding the system (per the proposal's own unresolved items in `Requirement_Analysis.md` §14).
8. **Do not add dependencies or swap technologies** outside the stack in Section 2 without an explicit request.
9. **Keep docs and code in sync** — if implementation forces a decision on an ambiguity, update the relevant doc in the same change (Section 9).
10. **No premature optimization or abstraction** — build what the current milestone/requirement needs, following Section 3's coding standards, not a hypothetical future version of the system.
11. **Log every non-proposal-required addition immediately.** Before committing a new endpoint, page, middleware, utility, or UI component, check whether `docs/product_proposal.pdf` actually asked for it. If not, add its entry to `docs/Proposal_vs_Engineering_Additions.md` in the same commit — do not wait for the next traceability audit to catch it (per Section 9).
12. **Self-review before marking any milestone Complete.** Run `docs/MILESTONE_VERIFICATION_CHECKLIST.md` in full, then cross-check the result against all nine governing documents: `Requirement_Analysis.md`, `System_Architecture.md`, `Database_Design.md`, `API_Contract.md`, `UI_Wireframes.md`, `Requirement_Traceability_Matrix.md`, `Proposal_vs_Engineering_Additions.md`, `PROJECT_PROGRESS.md`, and `MILESTONE_VERIFICATION_CHECKLIST.md` itself. Do not set a milestone's Status to "Completed" in `PROJECT_PROGRESS.md` if this review finds an inconsistency, an undocumented deviation, or a skipped proposal requirement — fix or document it first, in the same pass, then record the self-review's evidence in the milestone's row/detail entry. This is a self-review, not a substitute for the human Review Status sign-off in `PROJECT_PROGRESS.md`, which stays a separate field.
