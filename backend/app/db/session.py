from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Engine for the APPLICATION database only.
# Analytics connections to user databases will live in a separate module with a different type.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    connect_args={"connect_timeout": 5},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one session per request; uncommitted work is rolled back on close."""
    with SessionLocal() as session:
        yield session


def check_database() -> None:
    """Raise an exception if the application database is unreachable."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))