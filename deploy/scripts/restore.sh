#!/bin/bash
set -euo pipefail
[[ $# == 1 && -f $1 ]] || { echo 'Usage: restore.sh /path/to/backup.dump (stop app first)' >&2; exit 2; }
exec 9>/run/lock/jobbod-infra.lock
flock -w 120 9
cd /opt/jobbod/infra
# Explicitly destructive; run only after stopping application writes.
docker compose exec -T postgres pg_restore -U postgres -d jobbod --clean --if-exists --exit-on-error < "$1"
