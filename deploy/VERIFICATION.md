# Bootstrap evidence — 2026-11-11

## Delivered

- Local checkouts: `/home/tawn/code/Jobbod/{backend,frontend,ai}`.
- Each service source pushed to its develop branch, then fast-forwarded into its ci-cd branch; no force pushes; main preserved.
- Vite files removed from service branches and replaced by their actual stack; `.ai` renamed to `.agents`, references updated, project profiles populated.
- Next.js 16.4.6 / React 19.3.0 official CLI template with src; Python 3.12.13, FastAPI 0.162.4, uv lockfiles.
- Public gateway: http://160.187.246.154/ and http://160.187.246.154/api/hello.
- PostgreSQL 17 + pgvector 0.8.7; Redis AOF; source-built MinIO, all on private Tailscale IP only.
- File secrets, separate runtime/migration privileges, restricted S3 service account, Redis ACL; forced-command CI SSH key.

## Executed checks

| Check | Result / evidence |
|---|---|
| Backend unit health + fail-closed readiness | 2 tests PASS, `uv run python -m unittest discover -s tests` |
| AI unit hello, live, readiness, unknown route | 1 test PASS, same command in ai checkout |
| Copied agent policy after path rename | 18 tests PASS, `uv run python -m unittest discover -s .agents/scripts -p test_ai_policy.py` |
| Next.js build | PASS locally and in GitHub Docker build; standalone image running |
| Production npm audit | `npm audit --omit=dev --audit-level=high`: 0 vulnerabilities |
| Shell / Python / YAML | `bash -n` for all scripts, Python AST parse, YAML parse; Docker Compose config native check PASS |
| Infrastructure authorization | 3 integration tests PASS, `deploy/tests/integration.py` inside backend; repeated after rotation |
| PostgreSQL | Vector distance query PASS; runtime CREATE TABLE denied; Alembic version 0001 |
| Redis | Authenticated roundtrip PASS; no-auth rejected; foreign key prefix rejected |
| S3 | Object roundtrip PASS; visible bucket list restricted to jobbod; bucket creation denied |
| Public isolation | Public infra 5432/6379/9000/9001 blocked; app reaches private DB/Redis/S3 |
| Persistence | PostgreSQL test row, Redis key and S3 object survived full infra container recreation; probes removed |
| Model cache | Marker survived AI container recreation; marker removed, no weights downloaded |
| Backup restore | Custom-format dump restored into isolated `jobbod_restore_probe`; vector 0.8.7 / migration 0001 confirmed; temporary DB removed |
| Runtime rotation | DB runtime, Redis and S3 secrets rotated during locked maintenance; backend recreated healthy; 3 integration tests PASS; recovery files removed afterward |
| Migration failure | Invalid migration connection deliberately injected; deploy exited nonzero, previous backend container ID and health preserved; config restored |
| Unhealthy release rollback | Deliberately broken AI image rejected; prior image restored healthy; workflow failed as expected; Dockerfile restored and next workflow succeeded |
| Idempotency / serialization | Concurrent backend and AI redeploys of current digest PASS, no-op migration PASS; global mutation lock used |
| CI key scope | Shell command, invalid digest and unknown service all rejected with exit 2 |
| Anonymous packages | Unauthenticated GHCR token + manifest reads PASS for all five packages; no personal token supplied |
| Secret scan | Current/previous known server credential files and CI private key absent from tracked source |
| Diff checks | `git diff --check` across all three checkouts PASS; no remaining `.ai/` reference in copied rules |
| Privilege cleanup | Temporary unrestricted sudo removed from both hosts; `sudo -n true` denied afterward; app retains only validated deploy entrypoint |

## GitHub execution links

- [Frontend](https://github.com/hieu1020pk-web/jobbod-/actions/runs/42963172283)
- [Backend](https://github.com/hieu1020pk-web/jobbod-/actions/runs/42964207555)
- [AI](https://github.com/hieu1020pk-web/jobbod-/actions/runs/42964232983)
- [Infrastructure source builds](https://github.com/hieu1020pk-web/jobbod-/actions/runs/42963170731)
- [Expected failure / successful rollback drill](https://github.com/hieu1020pk-web/jobbod-/actions/runs/42963947781)

Backend and AI were rerun successfully after unrestricted sudo was removed.
Frontend encountered one runner-to-server SSH connection timeout; a bounded retry
was used while public HTTP and operator SSH remained reachable.

Warm-cache jobs before final privilege check: backend 28 seconds, AI 26 seconds.
These are observed bootstrap timings, not guaranteed deployment SLAs. Each app
workflow has one SSH command; server performs pull/migration/health/smoke within it.

## Runtime application digests

- Frontend: `sha256:a5a94ea60e76d424a1e38c1e4b6ce37bff4bb30ac3f08cd3ff5014bf94e797d0`
- Backend: `sha256:58d19cc97278d859792dd478fb51bd8556effd83dc4c82e6eb535f80d41ab414`
- AI: `sha256:055c242acec6e3e7309fde212fe1286ec4c3e4e5a9c4abe021abe78b5aa604c5`

## Limits / not executed

No model inference/load test: no model or AI task has been selected. HTTPS was absent at bootstrap; subsequently enabled as documented in TLS.md. No tailnet-admin ACL edit: tailnet-admin credentials were not
provided; applied host firewall and supplied a mergeable policy fragment instead.
No off-host/encrypted backup or MinIO object backup: no destination/recipient key
provided. No lint/full test suites added to app workflows, per requested lean CI.
The default Next.js install reported 7 moderate development-dependency findings;
production dependency audit returned zero. FastAPI's test client emitted an
httpx deprecation warning; existing tests passed. MinIO is pinned archived source,
not an actively maintained upstream release. Model cache budget is checked at
deployment time and is not a hard filesystem quota. HTTP endpoints are skeletons,
not completed product functionality.
