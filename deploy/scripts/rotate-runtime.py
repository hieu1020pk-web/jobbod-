#!/usr/bin/env python3
"""Run as root on infra during maintenance; stop backend before running.

Writes no secret values to stdout. Copy backend_config to app and recreate backend
before resuming traffic. Requires the admin tool installed by bootstrap.
"""
import fcntl
import hashlib
import json
import os
import secrets
import subprocess
from datetime import datetime, timezone
from pathlib import Path

if os.geteuid() != 0:
    raise SystemExit('Run as root on infra after stopping backend')
lock = open('/run/lock/jobbod-infra.lock', 'w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
root = Path('/etc/jobbod/secrets')
backup = Path('/etc/jobbod/rotation-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
backup.mkdir(mode=0o700)
for name in ('backend_config', 'db_runtime_password', 'redis_password', 'redis_acl', 's3_secret_key'):
    target = backup / name
    target.write_bytes((root / name).read_bytes())
    target.chmod(0o600)
config = json.loads((root / 'backend_config').read_text())
db, redis = (secrets.token_hex(32) for _ in range(2))
s3 = secrets.token_hex(20)
# Password is passed to psql over stdin, not command-line arguments.
sql = "ALTER ROLE jobbod_runtime PASSWORD '" + db + "';\n"
subprocess.run(['docker', 'compose', 'exec', '-T', 'postgres', 'psql', '-v', 'ON_ERROR_STOP=1', '-U', 'postgres', '-d', 'jobbod'], cwd='/opt/jobbod/infra', input=sql.encode(), check=True)
config['database_url'] = 'postgresql://jobbod_runtime:' + db + '@100.98.24.40:5432/jobbod'
config['redis_url'] = 'redis://jobbod:' + redis + '@100.98.24.40:6379/0'
config['s3_secret_key'] = s3
updates = {'db_runtime_password': (db + '\n',999), 'redis_password': (redis + '\n',999),
    'redis_acl': ('user default off\nuser jobbod on #' + hashlib.sha256(redis.encode()).hexdigest() + ' ~jobbod:* &jobbod:* +@read +@write +@connection +@transaction -@dangerous\n',999),
    's3_secret_key': (s3 + '\n',10001), 'backend_config': (json.dumps(config),10001)}
for name, (value, uid) in updates.items():
    path = root / name
    # Write in place: Compose secrets are bind mounts of these inodes.
    path.write_text(value)
    path.chmod(0o600)
    os.chown(path, uid, uid)
subprocess.run(['/usr/local/sbin/jobbod-minio-admin'], check=True)
subprocess.run(['docker', 'compose', 'restart', 'redis'], cwd='/opt/jobbod/infra', check=True)
print('Runtime credentials rotated. Copy backend_config to app, recreate backend, verify readiness.')
print('Recovery files retained in ' + str(backup) + '; remove after successful verification.')
