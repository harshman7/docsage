"""
SQLAlchemy database connection and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Use connect_args for SQLite, otherwise use default
connect_args = {}
if settings.USE_SQLITE:
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, echo=False, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

