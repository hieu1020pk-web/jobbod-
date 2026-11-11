"""Deployment integration tests use real Docker containers, never production paths.

Run with JOBBOD_DEPLOY_INTEGRATION=1. Requires Docker daemon access and public GHCR.
"""
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
import uuid

SOURCE = Path(__file__).resolve().parents[1] / 'scripts/deploy.py'
spec = importlib.util.spec_from_file_location('jobbod_deploy', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
GOOD = 'ghcr.io/hieu1020pk-web/jobbod-ai@sha256:055c242acec6e3e7309fde212fe1286ec4c3e4e5a9c4abe021abe78b5aa604c5'
BAD = 'ghcr.io/hieu1020pk-web/jobbod-ai@sha256:821dad4d79fd95ab5777cd3aeb4f624ab8066c9eda7b02714ad655c1345a67b5'
BACKEND = 'ghcr.io/hieu1020pk-web/jobbod-backend@sha256:58d19cc97278d859792dd478fb51bd8556effd83dc4c82e6eb535f80d41ab414'


class ValidationTests(unittest.TestCase):
    def test_reject_invalid_command_shape_and_identity(self):
        cases = [[], ['ai', GOOD], ['unknown', GOOD, '1', 'a'*40],
                 ['backend', GOOD, '1', 'a'*40], ['ai', GOOD, '-1', 'a'*40],
                 ['ai', GOOD, '1', 'not-a-sha'], ['ai', GOOD+'; id', '1', 'a'*40]]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(ValueError):
                module.main(args)


@unittest.skipUnless(os.environ.get('JOBBOD_DEPLOY_INTEGRATION') == '1', 'Requires isolated real-Docker integration opt-in')
class DeploymentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for image in (GOOD, BAD, BACKEND):
            subprocess.run(['docker', 'pull', image], check=True, stdout=subprocess.DEVNULL)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='jobbod-deploy-test-')
        self.root = Path(self.tmp.name)
        self.app = self.root / 'app'
        self.state = self.root / 'state'
        self.app.mkdir()
        self.state.mkdir()
        self.lock = self.root / 'lock'
        self.project = 'jobbod-test-' + uuid.uuid4().hex[:10]
        self.env = self.state / 'releases.env'
        self.env.write_text('')
        health = {'test': ['CMD', 'python', '-c', "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=1)"], 'interval':'1s','timeout':'2s','retries':2,'start_period':'1s'}
        self.config = {'name':self.project,'services':{'ai':{'image':'${AI_IMAGE:-'+GOOD+'}','healthcheck':health}}}
        self.write_config()
        self.deployer = module.Deployer(self.app, self.state, self.lock, wait=10)
        self.processes = []
        self.database_network = None

    def write_config(self):
        (self.app / 'compose.yaml').write_text(json.dumps(self.config))

    def tearDown(self):
        for process, log in self.processes:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=10)
            log.close()
        if self.database_network:
            subprocess.run(['docker','network','disconnect',self.database_network,'jobbod-migration-test'],check=True)
        result = subprocess.run(['docker','compose','--env-file',str(self.env),'down','--remove-orphans'],cwd=self.app,capture_output=True,text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.tmp.cleanup()

    def deploy(self, image=GOOD, run=10, commit='a'*40):
        self.deployer.deploy('ai',image,run,commit)

    def record(self, service='ai'):
        return json.loads((self.state/'deployments'/f'{service}.json').read_text())

    def container_id(self, service='ai'):
        return self.deployer.compose(self.env,'ps','-q',service,capture=True).strip()

    def launch(self, image, run, service="ai"):
        log = (self.root / f'process-{run}.log').open('w+')
        code = ("import importlib.util,signal; "
                f"s=importlib.util.spec_from_file_location('deploy',{str(SOURCE)!r}); "
                "m=importlib.util.module_from_spec(s);s.loader.exec_module(m); "
                "[signal.signal(sig,m.interrupted) for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP)]; "
                f"m.Deployer({str(self.app)!r},{str(self.state)!r},{str(self.lock)!r},wait=10).deploy({service!r},{image!r},{run},{'b'*40!r})")
        process = subprocess.Popen([sys.executable,'-c',code],stdout=log,stderr=log,start_new_session=True)
        self.processes.append((process,log))
        return process

    def wait_applying(self):
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            if (self.state/'deployments/ai.json').exists() and self.record()['status']=='applying':
                result=subprocess.run(['docker','ps','-q','--filter','label=com.docker.compose.project='+self.project,'--filter','label=com.docker.compose.service=ai'],capture_output=True,text=True,check=True)
                container=result.stdout.strip()
                if container:
                    inspected=subprocess.run(['docker','inspect',container],capture_output=True,text=True)
                    if inspected.returncode==0 and json.loads(inspected.stdout)[0]['Config']['Image']==BAD:
                        return
            time.sleep(0.05)
        self.fail('Deployment did not reach applying phase')

    def test_ai_independent_health_and_duplicate_no_restart(self):
        self.deploy()
        original=self.container_id()
        self.deploy(run=11)
        self.assertEqual(original,self.container_id())
        self.assertEqual(self.record()['status'],'unchanged')
        self.assertTrue(self.deployer.healthy('ai',GOOD))
        # No frontend/backend/nginx service even exists in this Compose project.

    def test_stale_release_and_same_run_mismatch_rejected(self):
        self.deploy(run=20)
        with self.assertRaisesRegex(RuntimeError,'Stale'):
            self.deploy(run=19)
        with self.assertRaisesRegex(RuntimeError,'identity'):
            self.deploy(run=20,commit='b'*40)
        self.assertEqual(self.record()['run_id'],20)
        self.assertTrue(self.deployer.healthy('ai',GOOD))

    def test_bad_health_restores_previous_and_fails(self):
        self.deploy()
        with self.assertRaises(subprocess.CalledProcessError):
            self.deploy(BAD,11)
        self.assertEqual(self.record()['status'],'failed')
        self.assertTrue(self.deployer.healthy('ai',GOOD))
        self.assertEqual(self.deployer.images()['AI_IMAGE'],GOOD)

    def test_first_bad_release_removed_without_committing_state(self):
        with self.assertRaises(subprocess.CalledProcessError):
            self.deploy(BAD)
        self.assertNotIn('AI_IMAGE',self.deployer.images())
        self.assertFalse(self.container_id())
        self.assertEqual(self.record()['status'],'failed')

    def test_sigterm_rolls_back_before_exit(self):
        self.deploy()
        process=self.launch(BAD,11)
        self.wait_applying()
        process.send_signal(signal.SIGTERM)
        self.assertNotEqual(process.wait(timeout=30),0)
        self.assertEqual(self.record()['status'],'failed')
        self.assertTrue(self.deployer.healthy('ai',GOOD))

    def test_sigkill_recovered_by_next_deployment(self):
        self.deploy()
        process=self.launch(BAD,11)
        self.wait_applying()
        os.killpg(process.pid,signal.SIGKILL)
        process.wait(timeout=10)
        self.assertEqual(self.record()['status'],'applying')
        self.deploy(run=12)
        self.assertTrue(self.deployer.healthy('ai',GOOD))
        history=[json.loads(line) for line in (self.state/'deployments/history.jsonl').read_text().splitlines()]
        self.assertIn('interrupted',[item['status'] for item in history])
        self.assertEqual(self.record()['run_id'],12)
        self.assertFalse((self.state/'candidate.env').exists())

    def test_concurrent_releases_serialize(self):
        self.deploy()
        first=self.launch(BAD,11)
        self.wait_applying()
        second=self.launch(GOOD,12)
        self.assertNotEqual(first.wait(timeout=40),0)
        self.assertEqual(second.wait(timeout=40),0)
        self.assertEqual(self.record()['run_id'],12)
        self.assertTrue(self.deployer.healthy('ai',GOOD))

    def prepare_backend(self):
        self.config['services'].update({
            'backend':{'image':'${BACKEND_IMAGE:-'+BACKEND+'}',
                       'healthcheck':{'test':['CMD','python','-c',"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live')"], 'interval':'1s','timeout':'2s','retries':3}},
            'migrate':{'image':'${BACKEND_IMAGE:-'+BACKEND+'}','profiles':['tools'],
                       'command':['alembic','upgrade','head']}})
        self.write_config()
        self.deployer.write_images(self.env,{'BACKEND_IMAGE':BACKEND})
        self.deployer.compose(self.env,'up','-d','--wait','--wait-timeout','15','backend')
        return self.container_id('backend')

    def test_real_backend_migration_failure_preserves_container(self):
        original=self.prepare_backend()
        # No migration secret is mounted: the real Alembic entry point fails.
        tag=os.environ['JOBBOD_TEST_BACKEND_CANDIDATE']
        with self.assertRaises(subprocess.CalledProcessError):
            self.deployer.deploy('backend',tag,11,'b'*40)
        self.assertEqual(self.container_id('backend'),original)
        self.assertTrue(self.deployer.healthy('backend',BACKEND))
        self.assertEqual(self.deployer.images()['BACKEND_IMAGE'],BACKEND)
        self.assertEqual(self.record('backend')['status'],'failed')
        self.assertNotEqual(subprocess.run(['docker','inspect','jobbod-migrate-11'],capture_output=True).returncode,0)

    def test_killed_migration_container_stopped_and_database_lock_released(self):
        original=self.prepare_backend()
        self.database_network=self.project+'_default'
        subprocess.run(['docker','network','connect',self.database_network,'jobbod-migration-test'],check=True)
        command="import psycopg,time; c=psycopg.connect('postgresql://postgres@jobbod-migration-test/jobbod_migration_test'); c.execute('SELECT pg_advisory_lock(724764650110)'); time.sleep(60)"
        self.config['services']['migrate']['command']=['python','-c',command]
        self.write_config()
        process=self.launch(os.environ['JOBBOD_TEST_BACKEND_CANDIDATE'],11,service='backend')
        import psycopg
        url='postgresql://postgres@127.0.0.1:55439/jobbod_migration_test'
        deadline=time.monotonic()+25
        while time.monotonic()<deadline:
            with psycopg.connect(url,autocommit=True) as conn:
                busy=conn.execute('SELECT NOT pg_try_advisory_lock(724764650110)').fetchone()[0]
            if busy:
                break
            time.sleep(0.1)
        else:
            self.fail('Migration container did not hold the real DB lock')
        os.killpg(process.pid,signal.SIGKILL)
        process.wait(timeout=10)
        self.assertEqual(self.record('backend')['status'],'migrating')
        # A deployment for another service must recover the orphan first.
        self.deploy(run=12)
        self.assertNotEqual(subprocess.run(['docker','inspect','jobbod-migrate-11'],capture_output=True).returncode,0)
        with psycopg.connect(url,autocommit=True) as conn:
            self.assertTrue(conn.execute('SELECT pg_try_advisory_lock(724764650110)').fetchone()[0])
        self.assertEqual(self.container_id('backend'),original)
        self.assertEqual(self.record('backend')['status'],'interrupted')


if __name__=='__main__':
    unittest.main(verbosity=2)
