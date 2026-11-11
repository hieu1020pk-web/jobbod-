# Project rules

Use the user-approved bootstrap plan. Backend owns PostgreSQL schema/migrations and canonical deployment files in deploy/. AI is internal and has no direct database ownership. Never commit secrets or model weights. CI remains build/push/deploy/check only. Keep source on develop and merge develop into ci-cd; do not cherry-pick deployments back into develop. Do not weaken existing repository protections.
