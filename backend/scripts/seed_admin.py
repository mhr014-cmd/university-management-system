"""
Bootstrap script: creates the first Admin account.

Required because POST /users/students and POST /users/teachers are
Admin-only, so the very first Admin cannot be self-registered (see
docs/Database_Design.md Section 11, item 4).

Usage (from backend/, with the venv active):
    SEED_ADMIN_EMAIL=admin@example.com SEED_ADMIN_PASSWORD=... \
    SEED_ADMIN_FIRST_NAME=First SEED_ADMIN_LAST_NAME=Last \
    python -m scripts.seed_admin

Reads credentials from process-level environment variables only — never
from or into any .env file (per CLAUDE.md Section 8/14 item 13). Idempotent:
if a user with SEED_ADMIN_EMAIL already exists, the script reports that and
exits without creating a duplicate.
"""

import os
import sys

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.admin import Admin
from app.models.user import User
from app.repositories.user_repository import UserRepository

user_repo = UserRepository()


def main() -> int:
    email = os.environ.get("SEED_ADMIN_EMAIL")
    password = os.environ.get("SEED_ADMIN_PASSWORD")
    first_name = os.environ.get("SEED_ADMIN_FIRST_NAME")
    last_name = os.environ.get("SEED_ADMIN_LAST_NAME")

    missing = [
        name
        for name, value in (
            ("SEED_ADMIN_EMAIL", email),
            ("SEED_ADMIN_PASSWORD", password),
            ("SEED_ADMIN_FIRST_NAME", first_name),
            ("SEED_ADMIN_LAST_NAME", last_name),
        )
        if not value
    ]
    if missing:
        print(f"Missing required environment variable(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    session = SessionLocal()
    try:
        existing = user_repo.get_by_email(session, email)
        if existing is not None:
            print(f"A user with email {email!r} already exists (id={existing.id}) — nothing to do.")
            return 0

        user = User(email=email, password_hash=hash_password(password), role="admin")
        session.add(user)
        session.flush()

        admin = Admin(user_id=user.id, first_name=first_name, last_name=last_name)
        session.add(admin)
        session.commit()

        print(f"Created Admin account: email={email!r} user_id={user.id} admin_id={admin.id}")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
