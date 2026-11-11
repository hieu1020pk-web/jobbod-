# Jobbod frontend profile

- Repository: https://github.com/hieu1020pk-web/jobbod-.git
- Branches: frontend/develop → frontend/ci-cd; main is preserved.
- Stack: Next.js generated defaults, npm, src/app.
- Owner/release owner: repository owner hieu1020pk-web.
- Deployment authorized by the user in the bootstrap conversation on 2026-11-11.
- CI: Docker build/push + one SSH deployment + readiness/smoke check; no extra CI test/lint gates requested.
- Secrets: server-local file mounts; GitHub stores deployment SSH key and pinned host key only.
- Verification: npm run build; infrastructure integration and rollback checks during bootstrap.
- Runtime budget: app 4 GB RAM / 40 GB disk; infra 6 GB RAM / 99 GB disk.
- AI: no selected model, no model download; persistent cache reserved for later use.
- Parallel agents: 1. Token/cost telemetry unavailable.
