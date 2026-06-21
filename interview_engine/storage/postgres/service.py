"""Service for managing PostgreSQL database engine, connection pooling, and session sessions."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .models import Base


class PostgresService:
    """Manages connection pool, sessionmaker, and database lifecycle for PostgreSQL."""

    def __init__(self, database_url: Optional[str] = None) -> None:
        self.database_url = database_url or os.environ.get(
            "DATABASE_URL", "sqlite:///nephele.db"
        )
        
        # Configure connection pooling and dialect-specific parameters
        if self.database_url.startswith("postgresql"):
            self.engine = create_engine(
                self.database_url,
                pool_size=10,
                max_overflow=20,
                pool_recycle=1800,
                pool_pre_ping=True
            )
        else:
            # Fallback (e.g. SQLite for testing/offline support)
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False} if "sqlite" in self.database_url else {}
            )
            
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=True,
            bind=self.engine
        )

    def create_tables(self) -> None:
        """Create tables in the database (useful for local development/testing)."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self) -> None:
        """Drop all tables in the database (useful for test isolation)."""
        Base.metadata.drop_all(bind=self.engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""
        db_session = self.SessionLocal()
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise
        finally:
            db_session.close()
