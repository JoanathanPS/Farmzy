"""Database setup and session management."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Base class for models
Base = declarative_base()

# Create database engine (with error handling)
try:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        echo=settings.debug,
    )
    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    print(f"Warning: Database engine creation failed: {e}")
    engine = None
    SessionLocal = None


def get_db():
    """Dependency for getting database session."""
    if SessionLocal is None:
        raise Exception("Database not configured. Please set up PostgreSQL connection.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

