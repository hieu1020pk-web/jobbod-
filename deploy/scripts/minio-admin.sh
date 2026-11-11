#!/bin/bash
set -euo pipefail
docker run --rm --network jobbod-infra_default \
    -v /etc/jobbod/secrets:/run/secrets:ro \
    -v /opt/jobbod/infra:/work:ro \
    python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df \
    sh -ec 'pip install --disable-pip-version-check --root-user-action=ignore --require-hashes -q --target /tmp/deps -r /work/admin-requirements.txt; PYTHONPATH=/tmp/deps python /work/minio-admin.py'
