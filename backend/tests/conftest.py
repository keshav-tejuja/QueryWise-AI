import os
import socket

from cryptography.fernet import Fernet

# Must be set before the app (and its settings) are imported.
os.environ.setdefault("SECRET_KEY", "test-secret-key-test-secret-key-0123456789")
os.environ.setdefault("FERNET_KEYS", Fernet.generate_key().decode())
os.environ.setdefault("DB_HOST_ALLOWLIST", "sampledb")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app import models as _models  # noqa: F401
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.connections.pool_manager import pools


@pytest.fixture(scope="session")
def test_engine():
    """A separate <db>_test database, so tests never touch your real application data."""
    url = make_url(settings.database_url)
    test_db_name = f"{url.database}_test"

    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": test_db_name}
        )
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{test_db_name}"'))
    admin.dispose()

    engine = create_engine(url.set(database=test_db_name))
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def client(test_engine):
    test_session = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        with test_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    pools.close_all()

    with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture(scope="session")
def sample_db_reachable():
    """Skip (rather than fail) when the demo database isn't reachable, e.g. outside Docker."""
    try:
        socket.create_connection(("sampledb", 5432), timeout=2).close()
    except OSError:
        pytest.skip("demo database 'sampledb' is not reachable (run tests inside docker compose)")