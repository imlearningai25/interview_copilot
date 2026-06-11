"""
Test configuration — in-memory SQLite, no PostgreSQL required.

Import order matters here:
  1. Patch DATABASE_URL *before* app.database is imported, so get_settings()
     returns "sqlite://" and _make_engine() creates a SQLite engine.
  2. Replace the module-level engine with a StaticPool engine so all
     operations in a test share one in-memory database (SQLite in-memory
     databases vanish when a connection closes — StaticPool prevents that).
  3. Import app.main only after patching so its `from .database import engine`
     binding picks up the StaticPool engine.
"""
import os
import sys
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite://"
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.database as _db_module

_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_db_module.engine = _test_engine

from app.main import create_app       # noqa: E402 — must come after engine patch
from app.database import Base, get_db  # noqa: E402
from app import models                 # noqa: E402
from app.config import get_settings    # noqa: E402

get_settings.cache_clear()

# The PostgreSQL partial unique index (WHERE is_active = TRUE) becomes a full
# unique index in SQLite, which only allows one inactive job — breaks multi-job
# tests.  Strip it; application code already enforces the one-active-at-a-time
# invariant.
models.Job.__table__.indexes = {
    i for i in models.Job.__table__.indexes if i.name != "uq_one_active_job"
}

_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture
def client():
    def _override():
        db = _TestingSession()
        try:
            yield db
        finally:
            db.close()

    application = create_app()
    application.dependency_overrides[get_db] = _override
    return TestClient(application, raise_server_exceptions=True)
