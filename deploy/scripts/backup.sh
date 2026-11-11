#!/bin/bash
set -euo pipefail
umask 077
exec 9>/run/lock/jobbod-infra.lock
flock -w 120 9
mkdir -p /var/backups/jobbod
file=/var/backups/jobbod/postgres-$(date -u +%Y%m%dT%H%M%SZ).dump
cd /opt/jobbod/infra
docker compose exec -T postgres pg_dump -U postgres -d jobbod -Fc > "$file.tmp"
mv "$file.tmp" "$file"
find /var/backups/jobbod -name 'postgres-*.dump' -type f -mtime +6 -delete
