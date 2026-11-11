from fastapi import FastAPI

app = FastAPI(title="Jobbod backend")


@app.get("/health/live")
def live():
    return {"status": "ok"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from Jobbod backend"}


@app.get("/health/ready")
def ready():
    import boto3
    import psycopg
    import redis
    from botocore.config import Config
    from fastapi.responses import JSONResponse
    from jobbod_backend.config import settings

    try:
        config = settings()
        with psycopg.connect(config["database_url"], connect_timeout=3) as connection:
            connection.execute("SELECT 1")
        client = redis.Redis.from_url(config["redis_url"], socket_connect_timeout=3, socket_timeout=3)
        try:
            client.ping()
        finally:
            client.close()
        s3 = boto3.client("s3", endpoint_url=config["s3_endpoint"],
            aws_access_key_id=config["s3_access_key"], aws_secret_access_key=config["s3_secret_key"],
            config=Config(connect_timeout=3, read_timeout=3, retries={"max_attempts": 0}))
        try:
            s3.head_bucket(Bucket=config["s3_bucket"])
        finally:
            s3.close()
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ready"}
