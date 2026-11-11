# Jobbod ai

Python 3.12, FastAPI, uv. Install: `uv sync --frozen`.
Run: `uv run uvicorn jobbod_ai.main:app --app-dir src --port 8000`.
Health: `/health/live`, `/health/ready`; hello: `/hello`.

Branches: `ai/develop` → `ai/ci-cd`. Source lives at the root of each branch.
Runtime secrets are files under `/run/secrets`; never commit credentials.

## Docker local

From this directory (ai/develop or ai/ci-cd):

```bash
docker build -t jobbod-ai:local .
docker run --rm -p 127.0.0.1:8001:8000 jobbod-ai:local
```

Liveness: http://localhost:8001/health/live. This is a CPU skeleton without a selected model; no model weights are downloaded during build.

## Local environment example

```bash
cp .env.example .env
uv sync --frozen
uv run --env-file .env uvicorn jobbod_ai.main:app --app-dir src
```

The skeleton does not require any secret or model token. Real `.env` files are ignored by Git and Docker context. Docker runs use the image's explicit host/port command; the example UVICORN variables are for the local uv command above.
