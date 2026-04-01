import pytest
import os
from unittest.mock import patch

HEADERS = {"X-Api-Key": "my_super_secret_api_key_for_bots"}


def create_test_user(client):
    """Helper function to create a user for observation tests."""
    response = client.post(
        "/api/users/register",
        json={"platform_name": "telegram", "platform_user_id": "obs_user_1", "fio": "Obs User"},
        headers=HEADERS,
    )
    return response.json()["user_id"]


# ---------------------------------------------------------
# 1. МОКИРОВАННЫЕ ТЕСТЫ (Всегда проходят, независимы от сети)
# ---------------------------------------------------------

@patch("app.services.yandex_disk.requests.get")
@patch("app.services.yandex_disk.requests.put")
def test_upload_post_mocked(mock_put, mock_get, client, db, monkeypatch):
    # Обходим проверку токена в сервисе для мок-теста
    monkeypatch.setenv("YANDEX_DISK_TOKEN", "valid_mock_token")

    user_id = create_test_user(client)

    # Настраиваем поведение моков requests
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"href": "https://mock-upload-url.yandex.net"}
    mock_put.return_value.status_code = 201

    files = {"file": ("test.jpg", b"fake_image_bytes", "image/jpeg")}
    data = {"user_id": user_id, "description": "Beautiful bird mock"}

    response = client.post("/api/posts", headers=HEADERS, data=data, files=files)

    assert response.status_code == 200
    assert "post_id" in response.json()
    assert response.json()["link"].startswith("disk:/observations/")

    # Проверяем, что запросы к Я.Диску "как бы" отправлялись
    mock_get.assert_called_once()
    mock_put.assert_called_once()


def test_save_geolocation(client, db):
    user_id = create_test_user(client)

    response = client.post(
        "/api/geolocations",
        json={"user_id": user_id, "x": 55.7558, "y": 37.6173},
        headers=HEADERS,
    )

    assert response.status_code == 200
    assert "geo_id" in response.json()


@patch("app.services.yandex_disk.requests.get")
@patch("app.services.yandex_disk.requests.put")
def test_link_photo_geo(mock_put, mock_get, client, db, monkeypatch):
    monkeypatch.setenv("YANDEX_DISK_TOKEN", "valid_mock_token")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"href": "https://mock-upload-url"}
    mock_put.return_value.status_code = 201

    user_id = create_test_user(client)

    # 1. Создаем пост
    post_resp = client.post(
        "/api/posts",
        headers=HEADERS,
        data={"user_id": user_id, "description": "test"},
        files={"file": ("test.jpg", b"fake", "image/jpeg")},
    )
    post_id = post_resp.json()["post_id"]

    # 2. Создаем геометку
    geo_resp = client.post(
        "/api/geolocations",
        json={"user_id": user_id, "x": 10.0, "y": 20.0},
        headers=HEADERS,
    )
    geo_id = geo_resp.json()["geo_id"]

    # 3. Связываем
    link_resp = client.post(
        "/api/link_photo_geo",
        json={"user_id": user_id, "post_id": post_id, "geo_id": geo_id},
        headers=HEADERS,
    )

    assert link_resp.status_code == 200
    assert link_resp.json()["message"] == "Linked successfully"


# ---------------------------------------------------------
# 2. ИНТЕГРАЦИОННЫЕ ТЕСТЫ (Требуют реального токена)
# ---------------------------------------------------------

# Тест пропустится, если токена нет или стоит дефолтный из .env.example
@pytest.mark.skipif(
    os.getenv("YANDEX_DISK_TOKEN") in [None, "", "yandex_token"],
    reason="Valid YANDEX_DISK_TOKEN is required for real integration test"
)
def test_upload_post_real_yandex_disk(client, db):
    """
    Этот тест реально отправляет файл на Я.Диск.
    Убедитесь, что папка observations/ создана на вашем Я.Диске.
    """
    user_id = create_test_user(client)

    files = {"file": ("integration_test.txt", b"Integration test file", "text/plain")}
    data = {"user_id": user_id, "description": "Integration test"}

    response = client.post("/api/posts", headers=HEADERS, data=data, files=files)

    assert response.status_code == 200
    assert "post_id" in response.json()