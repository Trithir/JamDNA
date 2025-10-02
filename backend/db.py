from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# Path to your SQLite DB (will be created if missing)
DATABASE_URL = "sqlite:///../data/db.sqlite"

# SQLAlchemy engine & session factory
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # needed for SQLite + FastAPI
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables if they don’t exist
Base.metadata.create_all(bind=engine)

# Dependency for FastAPI routes
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
