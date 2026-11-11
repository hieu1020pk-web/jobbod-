#!/bin/bash
set -euo pipefail
# CI may deploy the checked-out release, never invoke operator rollback or a shell.
read -r verb service image run_id commit extra <<< "${SSH_ORIGINAL_COMMAND:-}"
[[ $verb == deploy && -n $run_id && -n $commit && -z ${extra:-} ]] || exit 2
exec sudo -n /usr/local/sbin/jobbod-deploy "$service" "$image" "$run_id" "$commit"
