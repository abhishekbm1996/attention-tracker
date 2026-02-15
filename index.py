"""Vercel entrypoint: export FastAPI app for serverless deployment."""
import traceback

try:
    from server.main import app
except Exception:
    # Surface the actual error so we can diagnose preview deployment failures
    from fastapi import FastAPI
    from fastapi.responses import PlainTextResponse

    app = FastAPI()
    _startup_error = traceback.format_exc()

    @app.get("/{path:path}")
    def catch_all(path: str):
        return PlainTextResponse(f"STARTUP ERROR:\n\n{_startup_error}", status_code=500)
