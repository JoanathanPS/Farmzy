"""Database setup and session management for Supabase."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Base class for models
Base = declarative_base()

engine = None
SessionLocal = None

# Initialize Supabase PostgreSQL connection
if settings.database_url and "localhost" not in settings.database_url:
    try:
        # Support pooler / direct supabase connection
        db_url = settings.database_url
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            echo=settings.debug,
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print("Connected to Supabase PostgreSQL database.")
    except Exception as e:
        print(f"Warning: Supabase database connection failed: {e}")
        engine = None
        SessionLocal = None
else:
    print("Notice: Supabase DATABASE_URL not configured in .env. Database features will be disabled.")


def get_db():
    """Dependency for getting database session."""
    if SessionLocal is None:
        raise Exception("Supabase Database not configured. Please set DATABASE_URL in your .env file.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
