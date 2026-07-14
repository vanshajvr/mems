from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()  # reads .env into the environment -- must run before os.getenv() below

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mems.db")
# os.getenv(key, default) -- reads DATABASE_URL from .env if present,
# falls back to the hardcoded default if .env is missing entirely
# (e.g. on a fresh clone before anyone's created one).

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()