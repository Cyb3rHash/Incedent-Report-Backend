from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import get_settings
from app.db.url import normalize_asyncpg_database_url
from app.models.incident import Base  # noqa: F401  (ensures models are registered)

# Alembic Config object
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    """Return the DB URL for Alembic migrations.

    Contract:
      - Reads DATABASE_URL via Settings.
      - Ensures the URL uses the asyncpg driver for async SQLAlchemy migrations.
      - Removes `sslmode` from the URL query string (asyncpg does not accept it),
        while still allowing SSL to be enforced via connect_args in online mode.

    Returns:
      str: SQLAlchemy URL guaranteed to use the asyncpg driver and safe for asyncpg.
    """
    settings = get_settings()
    normalized = normalize_asyncpg_database_url(settings.database_url)
    return normalized.sqlalchemy_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode with async engine.

    Error behavior:
      - Raises ValueError with an actionable message if DATABASE_URL is missing/invalid
        or if the hostname cannot be resolved (common misconfiguration with Neon URLs).
    """
    try:
        settings = get_settings()
        normalized = normalize_asyncpg_database_url(settings.database_url)

        configuration = config.get_section(config.config_ini_section) or {}
        configuration["sqlalchemy.url"] = normalized.sqlalchemy_url

        connectable = async_engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            connect_args=normalized.connect_args,
        )

        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

        await connectable.dispose()
    except ValueError as e:
        # Provide a crisp failure for config/DNS issues rather than a deep stack trace.
        raise RuntimeError(f"Alembic cannot run migrations due to invalid DATABASE_URL: {e}") from e


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
