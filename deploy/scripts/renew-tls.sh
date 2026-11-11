#!/bin/bash
set -euo pipefail
cd /opt/jobbod/app
docker compose --env-file /etc/jobbod/releases.env exec -T nginx nginx -t
docker compose --env-file /etc/jobbod/releases.env exec -T nginx nginx -s reload
