#!/usr/bin/python3
"""One authoritative deploy entry point. CI cannot supply paths or Compose files."""
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone


def atomic_write(path, data):
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w') as stream:
        os.chmod(temporary, 0o600)
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    descriptor = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


class Deployer:
    def __init__(self, app, state, lock, wait=150):
        self.app, self.state, self.lock, self.wait = Path(app), Path(state), Path(lock), wait
        self.releases = self.state / 'releases.env'
        self.journals = self.state / 'deployments'
        self.journals.mkdir(mode=0o700, exist_ok=True)
        self.record = None

    def command(self, args, timeout=180, capture=False):
        return subprocess.run(args, cwd=self.app, check=True, timeout=timeout,
                              text=True, stdout=subprocess.PIPE if capture else None).stdout

    def compose(self, env, *args, capture=False):
        return self.command(['docker', 'compose', '--env-file', str(env), *args],
                            timeout=max(self.wait + 30, 180), capture=capture)

    def images(self):
        if not self.releases.exists():
            return {}
        return dict(line.split('=', 1) for line in self.releases.read_text().splitlines() if '=' in line)

    def write_images(self, path, images):
        atomic_write(path, ''.join(f'{key}={value}\n' for key, value in sorted(images.items())))

    def save(self, status):
        self.record['status'] = status
        self.record['updated_at'] = datetime.now(timezone.utc).isoformat()
        atomic_write(self.journals / (self.record['service'] + '.json'), json.dumps(self.record) + '\n')
        print('JOBBOD_RESULT=' + json.dumps(self.record), flush=True)
        history = self.journals / 'history.jsonl'
        if history.exists() and history.stat().st_size >= 10 * 1024 * 1024:
            for index in (2, 1):
                source = history.with_name(f'history.jsonl.{index}')
                if source.exists():
                    source.replace(history.with_name(f'history.jsonl.{index + 1}'))
            history.replace(history.with_name('history.jsonl.1'))
        with history.open('a') as stream:
            os.chmod(history, 0o600)
            stream.write(json.dumps(self.record) + '\n')
            stream.flush()
            os.fsync(stream.fileno())

    def healthy(self, service, image):
        container = self.compose(self.releases, 'ps', '-q', service, capture=True).strip()
        if not container:
            return False
        details = json.loads(self.command(['docker', 'inspect', container], capture=True))[0]
        return (details['Config']['Image'] == image and
                details['State'].get('Health', {}).get('Status') == 'healthy')

    def smoke(self, service):
        if service == 'ai':
            # Compose already waited on AI's own readiness, not unrelated web services.
            return
        self.compose(self.releases, 'up', '-d', '--no-deps', '--wait', '--wait-timeout', '60', 'nginx')
        host, suffix = ('jobbod.net', '/') if service == 'frontend' else ('api.jobbod.net', '/api/hello')
        self.command(['curl', '--fail', '--silent', '--show-error', '--retry', '3', '--retry-delay', '2',
                      '--max-time', '10', '--resolve', f'{host}:443:127.0.0.1', f'https://{host}{suffix}'], timeout=60)

    def stop_migration(self):
        name = self.record.get('migration_container')
        if not name:
            return
        if not re.fullmatch(r'jobbod-migrate-[1-9][0-9]{0,19}', name):
            raise RuntimeError('Invalid recorded migration container')
        inspected = subprocess.run(['docker', 'container', 'inspect', name],
                                   capture_output=True, text=True, timeout=15)
        if inspected.returncode == 0:
            self.command(['docker', 'rm', '-f', name], timeout=30)
        elif 'No such container' not in inspected.stderr and 'No such object' not in inspected.stderr:
            raise RuntimeError('Cannot inspect migration container during recovery')

    def restore(self):
        self.stop_migration()
        service, previous = self.record['service'], self.record['previous']
        images = self.images()
        key = service.upper() + '_IMAGE'
        if previous:
            images[key] = previous
        else:
            images.pop(key, None)
        self.write_images(self.releases, images)
        if previous:
            if not self.healthy(service, previous):
                self.compose(self.releases, 'up', '-d', '--no-deps', '--wait',
                             '--wait-timeout', str(self.wait), service)
        else:
            self.compose(self.releases, 'rm', '-s', '-f', service)
        # A successful restore is not a successful deployment. Never downgrade DB.

    def recover(self):
        for path in sorted(self.journals.glob('*.json')):
            self.record = json.loads(path.read_text())
            if self.record['status'] in {'pulling', 'migrating', 'applying', 'checking', 'committing', 'recovery_failed'}:
                print('Recovering interrupted deployment:', self.record['service'], flush=True)
                try:
                    self.restore()
                except Exception:
                    self.save('recovery_failed')
                    raise RuntimeError('Recovery failed; operator intervention required') from None
                self.save('interrupted')
        self.record = None
        (self.state / 'candidate.env').unlink(missing_ok=True)

    def cleanup(self, service, keep):
        output = self.command(['docker', 'image', 'ls', '--digests', '--format',
                               '{{.Repository}}@{{.Digest}}', f'ghcr.io/hieu1020pk-web/jobbod-{service}'], capture=True)
        for image in set(output.splitlines()) - set(keep):
            if '<none>' in image:
                continue
            try:
                self.command(['docker', 'image', 'rm', image])
            except subprocess.CalledProcessError:
                print('Image still referenced; retained:', image, flush=True)

    def deploy(self, service, image, run_id, commit, rollback=False):
        # One lock also protects image pulls from cleanup by another release.
        if shutil.disk_usage(self.app).free < 3 * 1024**3:
            raise RuntimeError('Need at least 3 GiB free disk')
        with self.lock.open('w') as lock:
            deadline = time.monotonic() + 900
            while True:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError('Deployment lock timed out')
                    time.sleep(0.2)
            self.recover()
            record_path = self.journals / (service + '.json')
            old = json.loads(record_path.read_text()) if record_path.exists() else {}
            if not rollback and run_id < old.get('run_id', 0):
                raise RuntimeError('Stale release rejected')
            if not rollback and run_id == old.get('run_id') and (commit != old.get('commit') or image != old.get('image')):
                raise RuntimeError('Release identity does not match existing run')
            self.command(['docker', 'pull', image], timeout=600)
            images = self.images()
            previous = images.get(service.upper() + '_IMAGE')
            if service == 'ai':
                # Production uses the mounted cache; tests use no cache downloads.
                cache = Path('/var/lib/jobbod/models')
                if cache.exists():
                    size = int(self.command(['du', '-sk', str(cache)], capture=True).split()[0])
                    if size > 8 * 1024**2:
                        raise RuntimeError('AI cache exceeds 8 GiB budget')
            self.record = {'service': service, 'image': image, 'previous': previous,
                           'run_id': max(run_id, old.get('run_id', 0)), 'commit': commit,
                           'started_at': datetime.now(timezone.utc).isoformat(),
                           'migration_container': f'jobbod-migrate-{run_id}' if service == 'backend' and not rollback else None}
            if previous == image and self.healthy(service, image):
                self.save('unchanged')
                print('Already healthy; no migration or recreation needed', flush=True)
                return
            candidate = self.state / 'candidate.env'
            images[service.upper() + '_IMAGE'] = image
            self.write_images(candidate, images)
            self.save('pulling')
            try:
                if service == 'backend' and not rollback:
                    self.save('migrating')
                    self.compose(candidate, 'run', '--rm', '--no-deps', '--name', self.record['migration_container'], 'migrate')
                self.save('applying')
                self.compose(candidate, 'up', '-d', '--no-deps', '--wait', '--wait-timeout', str(self.wait), service)
                self.save('checking')
                self.smoke(service)
                self.save('committing')
                self.write_images(self.releases, images)
                atomic_write(self.state / (service + '.previous'), (previous or '') + '\n')
                self.save('succeeded')
            except BaseException:
                try:
                    self.restore()
                except Exception:
                    self.save('recovery_failed')
                    print('Rollback failed; operator intervention required', file=sys.stderr, flush=True)
                else:
                    self.save('failed')
                raise
            finally:
                candidate.unlink(missing_ok=True)
            try:
                self.cleanup(service, (image, previous))
            except (subprocess.SubprocessError, TimeoutError):
                print('Image cleanup failed; deployment is healthy, inspect disk usage', file=sys.stderr)
            print('Deployed', service, image, flush=True)


def interrupted(signum, frame):
    raise InterruptedError('Deployment interrupted')


def main(arguments):
    rollback = bool(arguments and arguments[0] == 'rollback')
    if rollback:
        arguments = arguments[1:]
    if len(arguments) != 4:
        raise ValueError('Usage: jobbod-deploy [rollback] SERVICE IMAGE RUN_ID COMMIT_SHA')
    service, image, run_id, commit = arguments
    if service not in {'frontend', 'backend', 'ai'}:
        raise ValueError('Invalid service')
    if not re.fullmatch(r'ghcr\.io/hieu1020pk-web/jobbod-' + service + r'@sha256:[a-f0-9]{64}', image):
        raise ValueError('Invalid image repository/digest')
    if not re.fullmatch(r'[1-9][0-9]{0,19}', run_id) or not re.fullmatch(r'[a-f0-9]{40}', commit):
        raise ValueError('Invalid release identity')
    os.umask(0o077)
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, interrupted)
    Deployer('/opt/jobbod/app', '/etc/jobbod', '/run/lock/jobbod-app.lock').deploy(
        service, image, int(run_id), commit, rollback=rollback)


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except ValueError as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
    except BaseException as error:
        print('Deployment failed:', type(error).__name__, str(error), file=sys.stderr)
        sys.exit(1)
