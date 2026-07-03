"""
Alembic migration environment.

Wires Alembic's runtime to the SQLAlchemy Base/metadata and database URL
from app.core.config.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

# Guarantee `backend/` (this file's grandparent directory) is importable as
# the root of the `app` package, regardless of invocation method or cwd.
# `alembic.ini`'s `prepend_sys_path = .` already covers the normal case, but
# this is a self-contained fallback: unlike relying on cwd, `python -m
# alembic` vs. the bare `alembic` console-script entry point (the latter
# does NOT add cwd to sys.path, causing `ModuleNotFoundError: No module
# named 'app'`), or ini-parsing edge cases, __file__ is always correct.
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.db.base import Base
from app import models  # noqa: F401 - import registers all implemented models on Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
