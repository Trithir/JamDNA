from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base

BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent
DATA_DIR = REPO_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_PATH = DATA_DIR / "db.sqlite"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

engine = create_engine(
	DATABASE_URL,
	connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

# Lightweight schema upgrade for older DBs.
with engine.begin() as conn:
	columns = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(tracks)").fetchall()}
	if "embedding" not in columns:
		conn.execute(text("ALTER TABLE tracks ADD COLUMN embedding TEXT"))


def get_session():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()