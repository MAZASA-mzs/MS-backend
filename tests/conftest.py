import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# 1. Force environment variables BEFORE importing the app
os.environ["POSTGRES_DB"] = "test_observations"
os.environ["API_KEY"] = "my_super_secret_api_key_for_bots"

from app.main import app  # noqa: E402
from app.database import Base, get_db  # noqa: E402

# Test database configuration
TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/test_observations"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create tables once per test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db():
    """
    Creates a fresh database session for a test.
    Uses a transaction that is rolled back so tests don't leak data.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function", autouse=True)
def override_get_db(db):
    """
    Forces FastAPI to use the test database session.
    """

    def _get_test_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def client():
    """Provides a TestClient for the FastAPI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def mock_redis(mocker):
    """Mocks the redis client used in user services."""
    return mocker.patch("app.services.user_service.redis_client")
