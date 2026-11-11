# Jobbod ai

Python 3.12, FastAPI, uv. Install: `uv sync --frozen`.
Run: `uv run uvicorn jobbod_ai.main:app --app-dir src --port 8000`.
Health: `/health/live`, `/health/ready`; hello: `/hello`.

Branches: `ai/develop` → `ai/ci-cd`. Source lives at the root of each branch.
Runtime secrets are files under `/run/secrets`; never commit credentials.
