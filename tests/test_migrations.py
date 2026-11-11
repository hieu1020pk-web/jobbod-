"""Real PostgreSQL integration tests; opt in with JOBBOD_TEST_DATABASE_URL.

The configured database is disposable: the public schema is reset per test.
Never use production credentials or the production database here.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import psycopg

URL = os.environ.get('JOBBOD_TEST_DATABASE_URL')
ROOT = Path(__file__).resolve().parents[1]
LOCK = 724764650110


@unittest.skipUnless(URL, 'Requires disposable PostgreSQL/pgvector JOBBOD_TEST_DATABASE_URL')
class MigrationTests(unittest.TestCase):
    def setUp(self):
        # An explicit disposable database name is mandatory before destructive reset.
        from psycopg.conninfo import conninfo_to_dict
        parsed = conninfo_to_dict(URL.replace('postgresql+psycopg://', 'postgresql://'))
        self.assertEqual(parsed.get('dbname'), 'jobbod_migration_test')
        self.url = URL.replace('postgresql+psycopg://', 'postgresql://')
        with psycopg.connect(self.url, autocommit=True) as conn:
            conn.execute('DROP SCHEMA public CASCADE')
            conn.execute('CREATE SCHEMA public')
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        shutil.copytree(ROOT / 'alembic', self.directory / 'alembic')
        if self._testMethodName not in {'test_fresh_database_and_repeat_upgrade', 'test_previous_release_to_current_head'}:
            for revision in (self.directory / 'alembic/versions').glob('*.py'):
                if revision.name != '0001_vector.py':
                    revision.unlink()
        shutil.copy2(ROOT / 'alembic.ini', self.directory / 'alembic.ini')
        config = self.directory / 'config.json'
        config.write_text(json.dumps({'migration_url': self.url.replace('postgresql://', 'postgresql+psycopg://')}))
        self.env = {**os.environ, 'JOBBOD_MIGRATION_CONFIG_FILE': str(config)}
        self.env.pop('JOBBOD_MIGRATION_MODE', None)
        if self._testMethodName in {'test_fresh_database_and_repeat_upgrade', 'test_previous_release_to_current_head'}:
            # Full history may contain previously operator-approved maintenance revisions.
            # Only the disposable test DB gets this mode; deployment retains expand-only.
            self.env['JOBBOD_MIGRATION_MODE'] = 'maintenance'

    def tearDown(self):
        self.temporary.cleanup()

    def upgrade(self, expected=0):
        result = subprocess.run(['alembic', 'upgrade', 'head'], cwd=self.directory,
                                env=self.env, capture_output=True, text=True, timeout=30)
        if expected == 0:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def revision(self, name, source, parent='0001', policy='expand'):
        file = self.directory / 'alembic' / 'versions' / (name + '.py')
        declaration = '' if policy is None else 'deployment_policy = ' + repr(policy) + '\n'
        file.write_text('from alembic import op\n' + declaration +
                        'revision = ' + repr(name) + '\ndown_revision = ' + repr(parent) +
                        '\nbranch_labels = None\ndepends_on = None\n\ndef upgrade():\n' + source + '\n')
        return file

    def test_fresh_database_and_repeat_upgrade(self):
        self.upgrade()
        self.upgrade()
        with psycopg.connect(self.url) as conn:
            from alembic.config import Config
            from alembic.script import ScriptDirectory
            cfg = Config(str(self.directory / 'alembic.ini'))
            cfg.set_main_option('script_location', str(self.directory / 'alembic'))
            expected = ScriptDirectory.from_config(cfg).get_current_head()
            self.assertEqual(conn.execute('SELECT version_num FROM alembic_version').fetchone()[0], expected)
            self.assertEqual(conn.execute("SELECT '[1,2]'::vector <-> '[1,3]'::vector").fetchone()[0], 1.0)

    def test_previous_release_to_current_head(self):
        baseline = os.environ.get('JOBBOD_BASELINE_DIRECTORY')
        self.assertTrue(baseline, 'Provide an archived previous commit via JOBBOD_BASELINE_DIRECTORY')
        result = subprocess.run(['alembic', 'upgrade', 'head'], cwd=baseline,
                                env=self.env, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        with psycopg.connect(self.url) as conn:
            conn.execute('CREATE TABLE migration_ci_sentinel (id integer primary key, payload text)')
            conn.execute("INSERT INTO migration_ci_sentinel VALUES (1, 'prior-release-data')")
        self.upgrade()
        with psycopg.connect(self.url) as conn:
            self.assertEqual(conn.execute('SELECT payload FROM migration_ci_sentinel WHERE id = 1').fetchone()[0], 'prior-release-data')

    def test_existing_data_preserved_by_expand(self):
        self.upgrade()
        with psycopg.connect(self.url) as conn:
            conn.execute('CREATE TABLE migration_probe (id integer primary key, name text)')
            conn.execute("INSERT INTO migration_probe VALUES (1, 'existing-user')")
        self.revision('0002', "    op.execute('ALTER TABLE migration_probe ADD COLUMN optional_note text')")
        self.upgrade()
        with psycopg.connect(self.url) as conn:
            self.assertEqual(conn.execute('SELECT id, name, optional_note FROM migration_probe').fetchone(), (1, 'existing-user', None))

    def test_concurrent_migration_rejected_and_lock_released(self):
        with psycopg.connect(self.url, autocommit=True) as conn:
            conn.execute('SELECT pg_advisory_lock(%s)', (LOCK,))
            self.assertIn('Another migration holds', self.upgrade(1).stderr)
        self.upgrade()

    def test_unknown_database_revision_fails_without_mutation(self):
        self.upgrade()
        with psycopg.connect(self.url) as conn:
            conn.execute("UPDATE alembic_version SET version_num = 'unknown_release'")
        self.assertIn('unknown', self.upgrade(1).stderr)
        with psycopg.connect(self.url) as conn:
            self.assertEqual(conn.execute('SELECT version_num FROM alembic_version').fetchone()[0], 'unknown_release')

    def test_multiple_database_heads_rejected(self):
        self.upgrade()
        with psycopg.connect(self.url) as conn:
            conn.execute("INSERT INTO alembic_version VALUES ('second_head')")
        self.assertIn('multiple migration heads', self.upgrade(1).stderr)

    def test_multiple_code_heads_rejected(self):
        self.revision('0002a', '    pass')
        self.revision('0002b', '    pass')
        self.assertIn('exactly one head', self.upgrade(1).stderr)

    def test_missing_policy_and_maintenance_fail_closed(self):
        self.upgrade()
        file = self.revision('0002', "    op.execute('CREATE TABLE should_not_exist(id integer)')", policy=None)
        self.assertIn('deployment_policy', self.upgrade(1).stderr)
        file.unlink()
        self.revision('0002_maintenance', "    op.execute('CREATE TABLE maintenance_probe(id integer)')", policy='maintenance')
        self.assertIn('maintenance window', self.upgrade(1).stderr)
        with psycopg.connect(self.url) as conn:
            self.assertIsNone(conn.execute("SELECT to_regclass('maintenance_probe')").fetchone()[0])
        self.env['JOBBOD_MIGRATION_MODE'] = 'maintenance'
        self.upgrade()

    def test_failed_migration_rolls_back_transactional_ddl(self):
        self.upgrade()
        self.revision('0002', "    op.execute('CREATE TABLE rolled_back_probe(id integer)')\n    raise RuntimeError('intentional-test-failure')")
        self.upgrade(1)
        with psycopg.connect(self.url) as conn:
            self.assertIsNone(conn.execute("SELECT to_regclass('rolled_back_probe')").fetchone()[0])
            self.assertEqual(conn.execute('SELECT version_num FROM alembic_version').fetchone()[0], '0001')
            self.assertTrue(conn.execute('SELECT pg_try_advisory_lock(%s)', (LOCK,)).fetchone()[0])

    def test_actual_overlapping_processes(self):
        self.upgrade()
        self.revision('0002', "    op.execute('SELECT pg_sleep(3)')")
        process = subprocess.Popen(['alembic', 'upgrade', 'head'], cwd=self.directory,
                                   env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            import time
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                with psycopg.connect(self.url, autocommit=True) as conn:
                    busy = conn.execute('SELECT NOT pg_try_advisory_lock(%s)', (LOCK,)).fetchone()[0]
                if busy:
                    break
                time.sleep(0.05)
            else:
                self.fail('First migration did not acquire advisory lock')
            self.assertIn('Another migration holds', self.upgrade(1).stderr)
            stdout, stderr = process.communicate(timeout=15)
            self.assertEqual(process.returncode, 0, stderr)
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()
