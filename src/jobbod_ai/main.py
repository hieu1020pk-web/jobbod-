from fastapi import FastAPI

app = FastAPI(title="Jobbod ai")


@app.get("/health/live")
def live():
    return {"status": "ok"}


@app.get("/hello")
def hello():
    return {"message": "Hello from Jobbod ai"}


@app.get("/health/ready")
def ready():
    # No model is required by this skeleton. Add readiness when selecting a model.
    return {"status": "ready", "model_loaded": False}
