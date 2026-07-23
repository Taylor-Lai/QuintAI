"""Database engine and request-scoped session lifecycle."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from docnexus.core.settings import get_settings

DATABASE_URL = get_settings().database_url
engine_options = (
    {"connect_args": {"check_same_thread": False}}
    if DATABASE_URL.startswith("sqlite")
    else {"pool_pre_ping": True, "pool_recycle": 1800}
)
engine = create_engine(DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Yield a database session for one request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
