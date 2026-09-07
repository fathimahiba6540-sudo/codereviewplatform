import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.core.config import settings

# Determine database URL with SQLite fallback
db_url = settings.DATABASE_URL or "sqlite:///./codereview.db"

try:
    if "sqlite" in db_url:
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(db_url, pool_pre_ping=True, echo=settings.DEBUG)
        # Test connection
        with engine.connect() as conn:
            pass
except Exception as e:
    print(f"Database connection error with {db_url}: {e}. Falling back to SQLite.")
    db_url = "sqlite:///./codereview.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})

# Create SessionLocal class for DB dependency
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()


def get_db():
    """Dependency for obtaining a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

