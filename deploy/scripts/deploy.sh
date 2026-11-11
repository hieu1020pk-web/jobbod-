#!/bin/bash
set -euo pipefail
umask 077
[[ $# == 2 ]] || exit 2
service=$1
image=$2
case "$service" in frontend|backend|ai) ;; *) exit 2;; esac
[[ $image =~ ^ghcr\.io/hieu1020pk-web/jobbod-${service}@sha256:[a-f0-9]{64}$ ]] || exit 2
cd /opt/jobbod/app
available=$(df -Pk /var/lib/docker | awk 'NR==2 {print $4}')
((available >= 3145728)) || { echo 'Need at least 3 GiB free disk' >&2; exit 1; }
# No registry token on server: packages must be public.
timeout 600 docker pull "$image"
exec 9>/run/lock/jobbod-app.lock
flock -w 900 9
cache_kb=$(du -sk /var/lib/jobbod/models | awk '{print $1}')
((cache_kb <= 8388608)) || { echo 'Model cache exceeds 8 GiB budget; review model revisions before deploying' >&2; exit 1; }
key=${service^^}_IMAGE
state=/etc/jobbod/releases.env
touch "$state"
previous=$(sed -n "s/^${key}=//p" "$state")
retained_previous=$previous
if [[ $image == "$previous" && -f /etc/jobbod/${service}.previous ]]; then
    retained_previous=$(cat "/etc/jobbod/${service}.previous")
fi
set_image() {
    KEY="$key" IMAGE="$1" STATE="$state" python3 - <<'PY'
import os
from pathlib import Path
p=Path(os.environ['STATE'])
lines=[s for s in p.read_text().splitlines() if not s.startswith(os.environ['KEY']+'=')]
lines.append(os.environ['KEY']+'='+os.environ['IMAGE'])
tmp=p.with_suffix('.tmp'); tmp.write_text('\n'.join(lines)+'\n'); tmp.chmod(0o600); tmp.replace(p)
PY
}
compose() { docker compose --env-file "$state" "$@"; }
set_image "$image"
rollback() {
    echo 'Deployment failed; restoring previous image (database is not downgraded)' >&2
    if [[ -n $previous ]]; then
        set_image "$previous"
        compose up -d --no-deps --wait --wait-timeout 120 "$service"
    else
        compose rm -sf "$service"
        sed -i "/^${key}=/d" "$state"
    fi
}
# A failed migration leaves the old application running.
if [[ $service == backend ]]; then
    if ! compose run --rm --no-deps migrate; then
        if [[ -n $previous ]]; then set_image "$previous"; else sed -i "/^${key}=/d" "$state"; fi
        exit 1
    fi
fi
if ! compose up -d --no-deps --wait --wait-timeout 150 "$service"; then rollback; exit 1; fi
if grep -q '^FRONTEND_IMAGE=' "$state" && grep -q '^BACKEND_IMAGE=' "$state"; then
    if ! compose up -d --no-deps --wait --wait-timeout 60 nginx ||
       ! curl --fail --silent --show-error --retry 5 --retry-delay 2 --max-time 10 --resolve jobbod.net:443:127.0.0.1 https://jobbod.net/ >/dev/null ||
       ! curl --fail --silent --show-error --retry 5 --retry-delay 2 --max-time 10 --resolve api.jobbod.net:443:127.0.0.1 https://api.jobbod.net/api/hello; then
        rollback; exit 1
    fi
fi
printf '%s\n' "$retained_previous" > "/etc/jobbod/${service}.previous"
# Delete only old repository images. Preserve running + immediate rollback images.
while read -r old; do
    [[ -z $old || $old == "$image" || $old == "$retained_previous" ]] && continue
    if ! docker image rm "$old"; then echo "Image retained (still referenced): $old" >&2; fi
done < <(docker image ls --digests --format '{{.Repository}}@{{.Digest}}' "ghcr.io/hieu1020pk-web/jobbod-$service" | grep -v '<none>' | sort -u)
echo "Deployed $service $image"
