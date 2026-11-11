import json
import os
from functools import lru_cache
from pathlib import Path


@lru_cache
def settings():
    path = Path(os.environ.get("JOBBOD_CONFIG_FILE", "/run/secrets/backend_config"))
    config = json.loads(path.read_text())
    required = ("database_url", "redis_url", "s3_endpoint", "s3_access_key", "s3_secret_key", "s3_bucket")
    if any(not config.get(key) for key in required):
        raise ValueError("Missing required backend configuration")
    return config
