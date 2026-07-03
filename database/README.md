# database/

This folder holds database-related assets that live **outside** the backend's Alembic migration history:

- `seeds/` — seed data scripts/fixtures for development and demo environments (see `docs/Database_Design.md` §11 for the full seed data requirements list).

**Note:** The authoritative schema definition, migrations, and SQLAlchemy models live under `backend/app/models/` and `backend/alembic/` (see `docs/System_Architecture.md` §7 Folder Structure) — not here. This folder is for supplementary database assets only (seed data, exported ER diagrams, ad hoc query notes), to avoid duplicating the schema in two places.

Full schema design: [`docs/Database_Design.md`](../docs/Database_Design.md).
