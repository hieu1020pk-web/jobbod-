#!/bin/sh
set -eu
runtime=$(cat /run/secrets/db_runtime_password)
migration=$(cat /run/secrets/db_migration_password)
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -v runtime="$runtime" -v migration="$migration" <<'SQL'
CREATE ROLE jobbod_runtime LOGIN PASSWORD :'runtime';
CREATE ROLE jobbod_migration LOGIN PASSWORD :'migration';
ALTER DATABASE jobbod OWNER TO jobbod_migration;
ALTER SCHEMA public OWNER TO jobbod_migration;
REVOKE ALL ON DATABASE jobbod FROM PUBLIC;
GRANT CONNECT ON DATABASE jobbod TO jobbod_runtime;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO jobbod_runtime;
CREATE EXTENSION IF NOT EXISTS vector;
ALTER DEFAULT PRIVILEGES FOR ROLE jobbod_migration IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO jobbod_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE jobbod_migration IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO jobbod_runtime;
SQL
