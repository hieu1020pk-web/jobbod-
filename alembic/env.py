"""Validate migration history and serialize every Alembic entry point in PostgreSQL."""
import json
import os
from pathlib import Path

from alembic import context
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

# Session lock survives transaction boundaries and releases when connection closes.
MIGRATION_LOCK = 724764650110


def validate_history(connection):
    major = int(connection.exec_driver_sql("SHOW server_version_num").scalar()) // 10000
    available = connection.exec_driver_sql("SELECT default_version FROM pg_available_extensions WHERE name = 'vector'").scalar()
    installed = connection.exec_driver_sql("SELECT extversion FROM pg_extension WHERE extname = 'vector'").scalar()
    if major != 17 or not available or any(not version.startswith("0.8.") for version in (available, installed) if version):
        raise RuntimeError("Infra compatibility requires PostgreSQL 17 and pgvector 0.8.x; review infra upgrades separately")
    script = ScriptDirectory.from_config(context.config)
    heads = script.get_heads()
    if len(heads) != 1:
        raise RuntimeError("Migration history must have exactly one head")
    current = MigrationContext.configure(connection).get_current_heads()
    if len(current) > 1:
        raise RuntimeError("Database has multiple migration heads; resolve during maintenance")
    ancestors = {revision.revision for revision in script.walk_revisions()}
    if any(revision not in ancestors for revision in current):
        raise RuntimeError("Database revision is unknown to this release; refusing migration")
    pending = list(script.iterate_revisions(heads[0], current[0] if current else "base"))
    mode = os.environ.get("JOBBOD_MIGRATION_MODE", "expand")
    if mode not in {"expand", "maintenance"}:
        raise RuntimeError("Invalid migration mode")
    for revision in pending:
        policy = getattr(revision.module, "deployment_policy", None)
        if policy not in {"expand", "maintenance"}:
            raise RuntimeError("Every pending migration must declare deployment_policy")
        if policy == "maintenance" and mode != "maintenance":
            raise RuntimeError("Maintenance migration requires an operator maintenance window")
    return heads[0]


config_path = os.environ.get("JOBBOD_MIGRATION_CONFIG_FILE", "/run/secrets/migration_config")
config = json.loads(Path(config_path).read_text())
engine = create_engine(config["migration_url"], poolclass=NullPool, connect_args={"connect_timeout": 5})
try:
    with engine.connect() as connection:
        connection.exec_driver_sql("SET lock_timeout = '10s'")
        connection.exec_driver_sql("SET statement_timeout = '120s'")
        acquired = connection.exec_driver_sql("SELECT pg_try_advisory_lock(%s)", (MIGRATION_LOCK,)).scalar()
        connection.commit()
        if not acquired:
            raise RuntimeError("Another migration holds the database lock; retry after it finishes")
        try:
            target = validate_history(connection)
            connection.commit()
            context.configure(connection=connection, target_metadata=None, transactional_ddl=True)
            with context.begin_transaction():
                context.run_migrations()
            if MigrationContext.configure(connection).get_current_heads() != (target,):
                raise RuntimeError("Migration did not finish at the expected revision")
        finally:
            connection.rollback()
            connection.exec_driver_sql("SELECT pg_advisory_unlock(%s)", (MIGRATION_LOCK,))
            connection.commit()
finally:
    engine.dispose()
