import json
import os
from pathlib import Path
from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

config = json.loads(Path(os.environ.get("JOBBOD_MIGRATION_CONFIG_FILE", "/run/secrets/migration_config")).read_text())
engine = create_engine(config["migration_url"], poolclass=NullPool, connect_args={"connect_timeout": 5})
with engine.connect() as connection:
    connection.exec_driver_sql("SET lock_timeout = '10s'")
    connection.exec_driver_sql("SET statement_timeout = '120s'")
    connection.commit()
    context.configure(connection=connection, target_metadata=None)
    with context.begin_transaction():
        context.run_migrations()
engine.dispose()
