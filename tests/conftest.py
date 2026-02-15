"""Pytest fixtures: isolated DB per test, FastAPI TestClient."""
import os

import pytest
from fastapi.testclient import TestClient

# Set test DB before importing app so startup uses it; disable Basic Auth for tests
@pytest.fixture
def client(tmp_path):
    db_path = str(tmp_path / "test.db")
    os.environ["ATTENTION_TRACKER_DB"] = db_path
    os.environ.pop("BASIC_AUTH_USER", None)
    os.environ.pop("BASIC_AUTH_PASSWORD", None)
    os.environ.pop("DATABASE_URL", None)  # use SQLite for tests
    from server import database
    database.init_db()
    from server.main import app
    with TestClient(app) as c:
        yield c
    os.environ.pop("ATTENTION_TRACKER_DB", None)
