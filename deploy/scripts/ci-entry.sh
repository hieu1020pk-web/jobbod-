#!/bin/bash
set -euo pipefail
# Only this forced command is reachable with the CI SSH key.
read -r verb service image extra <<< "${SSH_ORIGINAL_COMMAND:-}"
[[ $verb == deploy && -z ${extra:-} ]] || exit 2
exec sudo -n /usr/local/sbin/jobbod-deploy "$service" "$image"
