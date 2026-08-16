import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator
from app.config import settings

# Calculate project base directory (where app/ and data/ live)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///./") or db_url.startswith("sqlite:///data/"):
    clean_path = db_url.replace("sqlite:///./", "").replace("sqlite:///", "")
    abs_db_path = os.path.abspath(os.path.join(BASE_DIR, clean_path))
    db_dir = os.path.dirname(abs_db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    db_url = f"sqlite:///{abs_db_path}"

connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency for obtaining a DB session per request with automatic cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
