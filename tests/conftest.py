import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import Base, get_db

# A completely separate database file, used ONLY by tests. Never
# touches mems.db -- this is what lets you run the test suite
# without worrying about wiping your real project data.
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    # Same shape as the real get_db() in database.py, just pointed at
    # the test engine instead. This is what actually redirects every
    # endpoint's database calls to test.db during tests.
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# This line is the key mechanism: FastAPI's dependency_overrides lets
# you swap out Depends(get_db) app-wide, for the duration of tests,
# without touching a single line of your actual endpoint code.
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Runs ONCE before any test in the whole session: build a fresh
    # test.db from your real models.py table definitions.
    Base.metadata.create_all(bind=engine)
    yield
    # Runs once after ALL tests finish: tear it back down and delete
    # the file, so every test run starts completely clean.
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest.fixture
def client():
    return TestClient(app)
