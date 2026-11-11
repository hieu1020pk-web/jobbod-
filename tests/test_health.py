import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from fastapi.testclient import TestClient
from jobbod_ai.main import app

class HealthTests(unittest.TestCase):
    def test_skeleton(self):
        with TestClient(app) as client:
            self.assertEqual(client.get('/health/live').status_code, 200)
            self.assertEqual(client.get('/health/ready').json(), {'status': 'ready', 'model_loaded': False})
            self.assertEqual(client.get('/hello').json()['message'], 'Hello from Jobbod ai')
            self.assertEqual(client.get('/does-not-exist').status_code, 404)
