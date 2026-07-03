# scripts/

Repository-level operational scripts (setup, local environment bootstrapping, CI helpers) that span both `backend/` and `frontend/` — as opposed to backend-only scripts, which live in `backend/scripts/` (e.g., `seed_admin.py`, `seed_demo_data.py`).

Placeholder — no scripts implemented yet. Candidates for this folder, per `docs/Implementation_Roadmap.md`:

- A local dev bootstrap script (installs backend + frontend dependencies, copies `.env.example` files)
- A combined lint/test runner used by `.github/workflows/`
