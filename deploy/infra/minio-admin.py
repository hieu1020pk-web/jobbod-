"""Bootstrap MinIO IAM without putting secret values in process arguments."""
import json
from pathlib import Path
from minio import Minio
from minio.credentials import StaticProvider
from minio.minioadmin import MinioAdmin
from urllib3 import PoolManager, Timeout

secrets = Path('/run/secrets')
read = lambda name: (secrets / name).read_text().strip()
config = json.loads(read('backend_config'))
endpoint = 'minio:9000'
http = PoolManager(timeout=Timeout(connect=5, read=15), retries=False)
client = Minio(endpoint, access_key=read('minio_root_user'), secret_key=read('minio_root_password'), secure=False, http_client=http)
admin = MinioAdmin(endpoint=endpoint, credentials=StaticProvider(read('minio_root_user'), read('minio_root_password')), secure=False, http_client=http)
bucket = config['s3_bucket']
if not client.bucket_exists(bucket):
    client.make_bucket(bucket)
policy = {'Version':'2012-10-17','Statement':[
    {'Effect':'Allow','Action':['s3:ListBucket','s3:GetBucketLocation'],'Resource':['arn:aws:s3:::'+bucket]},
    {'Effect':'Allow','Action':['s3:GetObject','s3:PutObject','s3:DeleteObject','s3:AbortMultipartUpload','s3:ListMultipartUploadParts'],'Resource':['arn:aws:s3:::'+bucket+'/*']}
]}
# Both create and update use an explicit, least-privilege policy.
accounts = json.loads(admin.list_service_account(read('minio_root_user'))).get('accounts') or []
if any(account['accessKey'] == config['s3_access_key'] for account in accounts):
    admin.update_service_account(access_key=config['s3_access_key'], secret_key=config['s3_secret_key'], policy=policy)
else:
    admin.add_service_account(access_key=config['s3_access_key'], secret_key=config['s3_secret_key'], name='jobbod-backend', policy=policy)
print('MinIO bucket and restricted backend service account configured')
