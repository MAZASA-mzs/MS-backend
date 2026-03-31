import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.main import app
from fastapi.testclient import TestClient

# Set test API key
os.environ["API_KEY"] = "my_super_secret_api_key_for_bots"

# Test database
TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/test_observations"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def mock_redis(mocker):
    mock_redis = mocker.patch("app.redis_client.redis_client")
    return mock_redis


def test_register_user(client, db):
    response = client.post(
        "/api/users/register",
        json={
            "platform_name": "telegram",
            "platform_user_id": "123",
            "fio": "Test User",
            "email": "test@example.com",
            "consent": True,
        },
        headers={"X-Api-Key": "my_super_secret_api_key_for_bots"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["fio"] == "Test User"


def test_get_user_by_platform(client, db):
    # First register
    client.post(
        "/api/users/register",
        json={
            "platform_name": "telegram",
            "platform_user_id": "123",
            "fio": "Test User",
        },
        headers={"X-Api-Key": "my_super_secret_api_key_for_bots"},
    )

    response = client.get(
        "/api/users/by-platform/telegram/123",
        headers={"X-Api-Key": "my_super_secret_api_key_for_bots"},
    )
    assert response.status_code == 200
    assert response.json()["fio"] == "Test User"


def test_generate_link_code(client, db, mock_redis):
    # Mock redis setex
    mock_redis.setex.return_value = None

    response = client.post(
        "/api/users/me/generate-link-code?user_id=test-user-id",
        headers={"X-Api-Key": "my_super_secret_api_key_for_bots"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "code" in data
    mock_redis.setex.assert_called_once()


def test_link_account(client, db, mock_redis):
    # Mock redis get
    mock_redis.get.return_value = "test-user-id"
    mock_redis.delete.return_value = None

    response = client.post(
        "/api/users/link-account",
        json={
            "platform_name": "maks",
            "platform_user_id": "456",
            "code": "ABC123",
        },
        headers={"X-Api-Key": "my_super_secret_api_key_for_bots"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Account linked"
    mock_redis.get.assert_called_once_with("link_code:ABC123")
    mock_redis.delete.assert_called_once_with("link_code:ABC123")
