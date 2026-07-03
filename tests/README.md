# tests/ (root)

This top-level folder is reserved for **cross-cutting tests** that exercise the system end-to-end (frontend + backend + database together) — as opposed to unit/integration tests scoped to a single side of the stack, which live in `backend/tests/` and `frontend/tests/` respectively (see `docs/System_Architecture.md` §7 Folder Structure).

- `e2e/` — end-to-end test scenarios (e.g., full login → exam submission → grading → result approval flow), placeholder only.

No tests are implemented yet. Testing conventions are defined in [`CLAUDE.md`](../CLAUDE.md) §10, and per-requirement test obligations are tracked in [`docs/Requirement_Traceability_Matrix.md`](../docs/Requirement_Traceability_Matrix.md) (Testing Status column).
