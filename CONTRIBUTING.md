# Contributing to University Management System (ICT Education)

Thank you for your interest in this project. It was built as a complete, milestone-by-milestone academic submission (see `PROJECT_PROGRESS.md` and `CHANGELOG.md` for the full history) and is now at its final release, `v2.0.0`. This guide describes how to propose changes going forward.

## Code of Conduct

Be respectful and constructive. Disagreements about code should stay focused on the code.

## Getting Started

1. Read [`README.md`](README.md) for setup instructions and [`Project_Structure.md`](Project_Structure.md) for an architectural overview.
2. Read [`CLAUDE.md`](CLAUDE.md) — it defines the coding standards, layering rules, and naming conventions that govern this codebase. Any contribution is expected to follow it.
3. Review the design documents in [`docs/`](docs/) before implementing anything — they are the source of truth for *what* the system does; `CLAUDE.md` governs *how* it's written.

## Development Setup

Follow the "How to Run this Project" section of the [README](README.md#how-to-run-this-project) to get a working local environment (backend, frontend, database, demo seed data).

## Branching and Commits

- Create a feature branch from `master` for your change (`git checkout -b feature/short-description`).
- Commit messages should be imperative, present tense, and scoped to one logical change (e.g. `Add attendance export endpoint`, not `Fixed stuff`).
- Do not mix schema migrations with unrelated feature code in the same commit.
- Never commit secrets, `.env` files, or credentials. Only `.env.example` files with placeholder values are tracked.

## Architecture Rules (enforced, not optional)

This project follows a strict layered backend architecture:

```
Router  →  Service  →  Repository  →  SQLAlchemy  →  PostgreSQL
```

- No business logic in routers; no direct ORM access in routers.
- No raw SQL outside repositories.
- Every request body and response model is a Pydantic schema.
- RBAC (role checks) via dependency injection; ownership/linkage checks in the service layer, on every request.
- On the frontend: server state lives only in React Query; components call typed hooks in `features/`, never `axios`/`fetch` directly.

Pull requests that violate these rules will be asked to be restructured before review.

## Database Changes

- Every schema change is a new Alembic revision, generated via `alembic revision --autogenerate` and reviewed by hand — never hand-edited after generation, never applied as manual DDL.
- Before submitting a migration, confirm `alembic revision --autogenerate` produces an empty diff against your updated models (i.e. your migration and your models agree).

## Testing Requirements

- Every new business rule or validation rule needs at least one test.
- Backend: unit tests for services (repositories stubbed), integration tests for routers (full request → DB → response, against a disposable database via `TEST_DATABASE_URL` — never your real database).
- Frontend: component tests for any new page/feature with non-trivial interaction logic.
- Run before submitting:
  ```
  cd backend
  pytest
  pip check
  alembic current
  alembic heads
  alembic revision --autogenerate   # confirm the diff is empty, then delete the generated file

  cd ../frontend
  npx tsc --noEmit
  npm run lint
  npx vitest run
  npm run build
  ```

## Submitting a Pull Request

1. Ensure all checks above pass locally.
2. Update relevant documentation in the same change (`docs/API_Contract.md` for endpoint changes, `docs/Database_Design.md` for schema changes, `CHANGELOG.md` for a summary).
3. If you introduce anything not explicitly required by the original proposal (`docs/product_proposal.pdf`) — a new endpoint, page, middleware, or utility — log it in `docs/Proposal_vs_Engineering_Additions.md` in the same change.
4. Open a pull request describing what changed and why, referencing any relevant requirement ID (`FR-xxx`/`NFR-xxx`) or milestone.

## Reporting Issues

Please open a GitHub issue with:
- A clear description of the problem or proposed enhancement
- Steps to reproduce (for bugs), including which role/account was used
- Expected vs. actual behavior

## Questions

Open an issue, or see the [Author & Contact](README.md#author--contact) section of the README.
