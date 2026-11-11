"""Run inside the deployed backend container; uses mounted runtime credentials."""
import io
import json
import unittest
from pathlib import Path
import boto3
import psycopg
import redis
from botocore.config import Config
from botocore.exceptions import ClientError

class InfrastructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(Path('/run/secrets/backend_config').read_text())

    def test_vector_and_runtime_database_permissions(self):
        with psycopg.connect(self.config['database_url'], connect_timeout=3) as connection:
            distance = connection.execute("SELECT '[1,2,3]'::vector <-> '[1,2,4]'::vector").fetchone()[0]
            self.assertEqual(distance, 1.0)
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute('CREATE TABLE public.forbidden_runtime_probe (id integer)')

    def test_redis_authentication_and_key_scope(self):
        client = redis.Redis.from_url(self.config['redis_url'], socket_timeout=3)
        try:
            self.assertTrue(client.ping())
            client.set('jobbod:bootstrap-probe', 'ok', ex=60)
            self.assertEqual(client.get('jobbod:bootstrap-probe'), b'ok')
            with self.assertRaises(redis.exceptions.NoPermissionError):
                client.set('foreign:bootstrap-probe', 'forbidden')
        finally:
            client.delete('jobbod:bootstrap-probe')
            client.close()
        unauthenticated = redis.Redis(host='100.98.24.40', port=6379, socket_timeout=3)
        try:
            with self.assertRaises(redis.exceptions.AuthenticationError):
                unauthenticated.ping()
        finally:
            unauthenticated.close()

    def test_s3_bucket_scope_and_roundtrip(self):
        client = boto3.client('s3', endpoint_url=self.config['s3_endpoint'],
            aws_access_key_id=self.config['s3_access_key'], aws_secret_access_key=self.config['s3_secret_key'],
            config=Config(connect_timeout=3, read_timeout=5, retries={'max_attempts': 0}))
        bucket, key = self.config['s3_bucket'], 'bootstrap/integration-probe.txt'
        try:
            client.put_object(Bucket=bucket, Key=key, Body=b'jobbod-smoke')
            response = client.get_object(Bucket=bucket, Key=key)
            try:
                self.assertEqual(response['Body'].read(), b'jobbod-smoke')
            finally:
                response['Body'].close()
            with self.assertRaises(ClientError) as failure:
                client.list_buckets()
            self.assertEqual(failure.exception.response['Error']['Code'], 'AccessDenied')
        finally:
            client.delete_object(Bucket=bucket, Key=key)
            client.close()

if __name__ == '__main__':
    unittest.main(verbosity=2)
