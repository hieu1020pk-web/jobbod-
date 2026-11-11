import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from fastapi.testclient import TestClient
from jobbod_backend.main import app

class HealthTests(unittest.TestCase):
    def test_live_and_hello(self):
        with TestClient(app) as client:
            self.assertEqual(client.get('/health/live').status_code, 200)
            self.assertEqual(client.get('/api/hello').json()['message'], 'Hello from Jobbod backend')
            self.assertEqual(client.get('/does-not-exist').status_code, 404)

    def test_readiness_fails_closed_without_secrets(self):
        with TestClient(app) as client:
            response = client.get('/health/ready')
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json(), {'status': 'unavailable'})
