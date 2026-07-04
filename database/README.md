# database/

This folder holds database-related assets that live **outside** the backend's Alembic migration history:

- `seeds/` — reserved for static seed fixtures/exports, if a future need arises. The actual runnable seed script is `backend/scripts/seed_demo_data.py` (implemented Milestone 11, per `docs/Database_Design.md` §11's full requirements list) — kept alongside `backend/scripts/seed_admin.py` rather than here, since both are executable Python that needs the backend's own app context (`app.db.session`, models, `hash_password`), not standalone data files.

**Note:** The authoritative schema definition, migrations, and SQLAlchemy models live under `backend/app/models/` and `backend/alembic/` (see `docs/System_Architecture.md` §7 Folder Structure) — not here. This folder is for supplementary database assets only (seed data, exported ER diagrams, ad hoc query notes), to avoid duplicating the schema in two places.

Full schema design: [`docs/Database_Design.md`](../docs/Database_Design.md).
