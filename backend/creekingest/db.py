"""Database session and base model setup for the CreekLink backend."""

from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from creekingest.config import settings

# SQLAlchemy engine and session factory
engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Yield a database session and ensure it is closed afterwards.

    This function is intended for use as a dependency in request handlers
    (e.g., FastAPI). It provides a scoped SQLAlchemy session and guarantees
    that the session is closed when the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
