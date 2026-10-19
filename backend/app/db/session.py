# SQLAlchemy engine and session factory for the application database. Handles
# SQLite-specific connect args and auto-creates the parent directory for file DBs.
from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker


class Database:
    def __init__(self, url: str) -> None:
        # SQLite requires check_same_thread=False for multi-threaded FastAPI use.
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        if url.startswith("sqlite:///"):
            # Ensure the directory for a file-based SQLite database exists.
            Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
        self.engine: Engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)

    def session(self) -> Generator[Session, None, None]:
        # Context-managed database session that is always closed after use.
        database_session = self.session_factory()
        try:
            yield database_session
        finally:
            database_session.close()

    def is_available(self) -> bool:
        # Lightweight connectivity check used by readiness and dependency injection.
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
