# Jobbod backend

Python 3.12, FastAPI, uv. Install: `uv sync --frozen`.
Run: `uv run uvicorn jobbod_backend.main:app --app-dir src --port 8000`.
Health: `/health/live`, `/health/ready`; hello: `/api/hello`.

Branches: `backend/develop` → `backend/ci-cd`. Source lives at the root of each branch.
Runtime secrets are files under `/run/secrets`; never commit credentials.

## Docker local

From this directory (backend/develop or backend/ci-cd):

```bash
docker build -t jobbod-backend:local .
docker run --rm -p 127.0.0.1:8000:8000 jobbod-backend:local
```

Liveness: http://localhost:8000/health/live. Without runtime secret configuration, readiness returns 503; hello/liveness work for local smoke testing. For real DB/Redis/S3 access, mount a private config file at /run/secrets/backend_config and set JOBBOD_REQUIRE_CONFIG=1. Never put credentials in image/build args or Git.

## Local configuration and secrets

```bash
cp .env.example .env
mkdir -p .secrets
chmod 700 .secrets
cp config/backend_config.example.json .secrets/backend_config.json
cp config/migration_config.example.json .secrets/migration_config.json
chmod 600 .env .secrets/*.json
```

Replace every CHANGE_ME value with credentials of your **local** PostgreSQL/Redis/MinIO. These templates do not create those services or provision users/buckets. Use PostgreSQL 17 with pgvector 0.8.x and bucket jobbod; keep runtime and migration accounts separate. Do not copy production secrets to a developer machine.

```bash
uv sync --frozen
uv run --env-file .env uvicorn jobbod_backend.main:app --app-dir src
# In a separate shell, only against the intended local DB:
uv run --env-file .env alembic upgrade head
```

The JSON templates, .env.example and Dockerfile are committed; `.env`, `.secrets/` and all actual credentials are ignored. Docker context also excludes config templates and real env/secrets. Never remove the .secrets directory ignore rule.

For a configured Docker run, edit the ignored backend JSON to use `host.docker.internal` instead of 127.0.0.1 for services running on the host. On Linux add the host-gateway mapping. Run under your local UID so the container can read your mode-0600 file without making it world-readable:

```bash
docker run --rm --user "$(id -u):$(id -g)" \
  -p 127.0.0.1:8000:8000 --add-host host.docker.internal:host-gateway \
  -e JOBBOD_REQUIRE_CONFIG=1 \
  -v "$PWD/.secrets/backend_config.json:/run/secrets/backend_config:ro" \
  jobbod-backend:local
```

On SELinux hosts, use the appropriate bind-mount label for the local private file (for example `:ro,Z`); do not disable SELinux. The local DB/Redis/MinIO must be reachable via the host gateway. The migration secret is not mounted into a running backend container.
