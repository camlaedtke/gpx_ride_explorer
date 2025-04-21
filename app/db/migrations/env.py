"""
Environment configuration for Alembic migrations.

Configures the migration environment, including target metadata and database URL,
for both online and offline migrations.
"""

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides access to the 
# values within the .ini file
config = context.config

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

# Get the SQLAlchemy metadata from the models
from app.db.models import Base
target_metadata = Base.metadata

# Override sqlalchemy.url from ini file with DATABASE_URL from .env
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/bikecoach")
config.set_main_option("sqlalchemy.url", DATABASE_URL)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
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
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()