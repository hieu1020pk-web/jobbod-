# Jobbod deployment

Application: `devops@160.187.246.154`, private `100.110.186.46`.
Infrastructure: `devops@100.98.24.40`, public address `103.252.137.194`.
The infrastructure SSH host key is stored under the public address; use
`ssh -F /dev/null -o HostKeyAlias=103.252.137.194 devops@100.98.24.40`.

## Ownership and release

Three independent checkouts of the same GitHub repository. Each service owns
its root source on `<service>/develop`; merge that branch into `<service>/ci-cd`
and push to deploy. Never merge branches belonging to different services.
The original Vite source remains in `main` and Git history; it is replaced on
these service branches. Backend owns migrations and this canonical deploy tree.

Backend CI rehearses changed migrations/dependencies on disposable PostgreSQL +
pgvector (manual dispatch always rehearses); app CI never upgrades infra.
Every pending revision declares deployment_policy=expand or maintenance; the latter
requires an explicit operator maintenance window. PostgreSQL advisory locking,
revision checks and PostgreSQL 17 / pgvector 0.8.x compatibility guard apply.
The policy declaration still requires review and application-specific data tests.

Each app workflow does checkout, cached native amd64 build/push, then exactly
one SSH invocation for deployment and checks. No separate CI test/lint jobs.
Packages use `contents: read`, `packages: write`; publish GHCR packages as public
and verify anonymous pull. The server does not log into GHCR. GitHub secrets:
`JOBBOD_DEPLOY_KEY` (dedicated forced-command SSH key), `JOBBOD_KNOWN_HOSTS`
(pinned verified app SSH host keys). Do not replace host verification with scans
inside CI. Package visibility is independent of repository visibility.

The deployment key may only invoke `deploy frontend|backend|ai <image@digest> <run_id> <commit_sha>`.
The root-owned deployment script validates the exact registry/repository and
SHA-256 digest. A global flock serializes app releases; pull has a 10-minute
limit, lock wait 15 minutes, readiness wait 150 seconds. Workflows do not cancel
an active deployment. No arbitrary remote shell, user-supplied Compose or host
mounts are accepted through that key.

The entrypoint is installed from scripts/deploy.py; the former deploy.sh is removed.
Root-only per-service journals and bounded history live under /etc/jobbod/deployments.
Signals roll back; the next deployment reconciles journaled interruptions, stops
recorded orphan migration containers, and fails closed if recovery fails.
Older run IDs and same-run identity mismatches are rejected. Only the affected
service is checked. Healthy identical images are not recreated.

Backend migrations run before replacing the old container. Failure preserves
the old image. Health/smoke failure restores the prior image and fails CI.
Migrations must be backward compatible with that image: expand first, backfill,
contract in a separately reviewed release. Automatic database downgrade is
intentionally forbidden. HTTP deployment has a brief restart interruption.

## Bootstrap / configuration updates

Use an operator key and temporary sudo, never the restricted CI key. Transfer
this deployment tree into root-owned `/opt/jobbod/bootstrap/deploy`, then run
`scripts/bootstrap.sh app` or `scripts/bootstrap.sh infra` as root on the
corresponding host. It installs files under `/opt/jobbod/app`, `/opt/jobbod/infra`
and `/usr/local/sbin`; it does not install Docker (already available).
Run `python3 scripts/sync-secrets.py` from the local operator checkout after infra
secret initialization. This passes values through SSH pipes without printing.
On infra: `cd /opt/jobbod/infra && sudo docker compose up -d --wait`, then
`sudo /usr/local/sbin/jobbod-minio-admin`. Bootstrap preserves existing secrets
and image selections. Start app services using the GitHub workflows.

Image/config/Compose/script updates are separate: application CI changes images
only. An operator must reinstall changed root-owned deployment files; CI never
gets permission to replace its own privileged scripts. Infra images build only
when MinIO build sources/workflow change or by manual dispatch, not per app
commit. Update `.env` image digests explicitly after an infra image release.
`MC_IMAGE` in the infra env example is the pinned optional operations CLI image;
it is not a continuously running service.

After bootstrap remove `/etc/sudoers.d/99-devops-bootstrap` on both hosts.
App retains only `/etc/sudoers.d/50-jobbod-deploy`; infra retains no new passwordless
sudo grant. Operators can still use password-authenticated sudo for maintenance.
Neither account is added to the Docker group (equivalent to unrestricted root).

## Data, network and resource budget

PostgreSQL 17 + pgvector, Redis 7.4 AOF, MinIO have persistent directories under
`/var/lib/jobbod`. App publishes Nginx ports 80/443; frontend is https://jobbod.net and API is https://api.jobbod.net/api/hello. See TLS.md for renewal and Cloudflare settings.
AI and app container ports are internal. Infra binds published ports only to
`100.98.24.40`. App can reach 5432, 6379, 9000; operator `100.74.53.37` can also
reach console 9001. A Docker `DOCKER-USER` policy enforces this independently of
UFW. A systemd unit reinstalls that policy when Docker restarts. The configured
operator IP must be changed if the operator Tailscale address changes.

Tailnet ACL management requires tailnet-admin access, which is not provided by
server SSH. Host firewall restrictions are applied; use the adjacent policy
fragment when integrating with the existing tailnet ACL. Do not replace the
whole tailnet policy or interrupt unrelated machines.

App has 4 GB RAM / 40 GB disk. One worker per Python service; CPU/RAM and JSON-log
limits are in Compose. AI model cache is `/var/lib/jobbod/models`, mounted at
`/models`; HF and sentence-transformer cache paths point there. No model selected,
no weights downloaded, no inference dependency installed. Select a CPU model
that actually fits this machine before adding inference. Model files never enter
Git, Docker context, image or release directories. Deploy requires 3 GiB free
and rejects a cache exceeding 8 GiB; this is a deployment budget check, not a
filesystem quota. The eventual downloader must enforce its own model budget.

Docker layer caching means unchanged dependencies/base layers are reused. Keep
the current and preceding image per service; cleanup targets only that service's
older GHCR image references. No volume pruning, global system prune or automatic
model-cache deletion. Next.js runtime cache has its own persistent directory.

## Secrets and rotation

`/etc/jobbod` and its secrets directory are 0700. Files are 0600 and owned by the
container UID that must read them (10001 for app/MinIO, 999 for PostgreSQL/Redis).
Compose uses read-only secret file mounts. These are ordinary host files, not an
encrypted secret vault; root and the Docker daemon are trusted.

Runtime backend config has only PostgreSQL runtime, Redis and bucket-scoped S3
credentials. The Alembic container alone receives `migration_config`. PostgreSQL
runtime cannot create schema objects; migrations own the schema but are not
superuser. PostgreSQL administrator credentials and MinIO root credentials stay
on infra. Readiness checks DB, authenticated Redis and authorized bucket access
with bounded timeouts; responses never expose connection strings.

For runtime rotation, arrange a maintenance window and keep the app deployment
lock held in a root operator session (`flock /run/lock/jobbod-app.lock bash`).
Inside that session stop backend using Compose with
`--env-file /etc/jobbod/releases.env`. On infra run
`sudo /usr/local/sbin/jobbod-rotate-runtime`; locally run `scripts/sync-secrets.py`;
inside the locked app session recreate backend with `up -d --no-deps --force-recreate
--wait backend`. Verify readiness before releasing the lock. This rotates DB
runtime password, Redis password and S3 service-account secret; old service-account
secret is replaced. It retains root-only recovery files on infra until an operator
removes them after verification. If any step fails, leave backend stopped and
recover coherently from those files; do not resume with mismatched credentials.
Temporary operator sudo is required for this cross-host administration; revoke it
afterward. CI deployment needs no access to plaintext secrets.

Administrator and migration credentials require a separate planned maintenance:
change the PostgreSQL role password using local socket + stdin, update the
matching secret/config, sync migration config, and verify a no-op migration.
For MinIO root rotation update its files and recreate MinIO, then verify IAM;
never use startup password environment changes to pretend a persisted PostgreSQL
password has rotated. Keep an encrypted backup of secrets separately from data;
use your own recipient key and store it off-host. No off-host destination or key
has been supplied, so off-host/encrypted backup is not configured.

## Backups and recovery

`jobbod-backup.timer` runs daily at 03:15 server time (UTC). It takes a custom-format
PostgreSQL dump and keeps seven daily copies under `/var/backups/jobbod`, atomically
renaming successful dumps. Check with `systemctl list-timers jobbod-backup.timer`.
This protects against logical mistakes, not loss of the infra host. MinIO object
backup and off-host database backup require an additional storage destination.

Restore only during maintenance with application writes stopped:
`sudo /usr/local/sbin/jobbod-restore /var/backups/jobbod/postgres-<timestamp>.dump`.
The schema dump does not recreate cluster roles: restore into a cluster provisioned
with the same roles/secrets first. Verify pgvector, Alembic version and app
readiness before resuming traffic. Never run restore automatically from CI.

MinIO community is archived. Its server and optional CLI are built from fixed
source commits, and runtime images are pinned by digest. There is no claim of
ongoing upstream security maintenance. Domain and HTTPS configuration are documented in TLS.md.
