import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock

HEADERS = {"X-Api-Key": "my_super_secret_api_key_for_bots"}


def create_test_user(client):
    """Helper function to create a user for observation tests."""
    response = client.post(
        "/api/users/register",
        json={
            "platform_name": "telegram",
            "platform_user_id": "obs_user_1",
            "fio": "Obs User",
        },
        headers=HEADERS,
    )
    return response.json()["user_id"]


# ---------------------------------------------------------
# 1. МОКИРОВАННЫЕ ТЕСТЫ (Всегда проходят, независимы от сети)
# ---------------------------------------------------------


@patch("app.services.ai_service.httpx.AsyncClient")
@patch("app.services.ai_service.redis_client")
@patch("app.services.ai_service.get_plants_dictionary")
def test_ai_classify_mocked(
    mock_get_plants, mock_redis, mock_async_client_class, client
):
    # Настраиваем мок асинхронного клиента httpx (контекстный менеджер)
    mock_client_instance = mock_async_client_class.return_value.__aenter__.return_value

    # Имитируем успешный ответ от нейросети
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"plant_class": 1, "confidence": 0.95}

    # Привязываем асинхронный мок к методу post
    mock_client_instance.post = AsyncMock(return_value=mock_response)

    # Имитируем словарь растений, чтобы подтянулась эталонная ссылка
    mock_get_plants.return_value = {
        "1": {"reference_image_url": "https://example.com/ref.jpg"}
    }

    files = {"file": ("test.jpg", b"fake_image_bytes", "image/jpeg")}
    response = client.post("/api/ai/classify", headers=HEADERS, files=files)

    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["plant_class"] == 1
    assert json_resp["confidence"] == 0.95
    assert json_resp["reference_image_url"] == "https://example.com/ref.jpg"
    assert "temp_file_id" in json_resp

    # Проверяем, что файл ушел на кэширование в Redis
    mock_redis.setex.assert_called_once()


@patch("app.services.yandex_disk.redis_client")
@patch("app.services.yandex_disk.requests.get")
@patch("app.services.yandex_disk.requests.put")
@patch("app.services.observation_service.get_and_delete_stashed_image")
def test_upload_post_mocked(
    mock_get_stashed, mock_put, mock_get, mock_redis, client, db, monkeypatch
):
    # Указываем, что кэш папок пуст, чтобы код попытался их создать
    mock_redis.get.return_value = None

    # Обходим проверку токена в сервисе для мок-теста
    monkeypatch.setenv("YANDEX_DISK_TOKEN", "valid_mock_token")

    user_id = create_test_user(client)

    # Имитируем успешное извлечение картинки из Redis
    mock_get_stashed.return_value = {
        "filename": "test.jpg",
        "content_type": "image/jpeg",
        "bytes": b"fake_image_bytes",
    }

    # Настраиваем поведение моков requests для Я.Диска
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "href": "https://mock-upload-url.yandex.net"
    }
    mock_put.return_value.status_code = 201

    # Теперь отправляем строгий JSON payload (без файлов)
    data = {
        "user_id": user_id,
        "description": "Beautiful bird mock",
        "ai_plant_id": 1,
        "ai_confidence": 0.95,
        "user_plant_id": 1,
        "temp_file_id": "dummy_temp_file_id",
    }

    response = client.post("/api/posts", headers=HEADERS, json=data)

    assert response.status_code == 200
    assert "post_id" in response.json()
    assert response.json()["link"].startswith("disk:/observations/")

    # Проверяем, что запросы к Я.Диску "как бы" отправлялись
    mock_get.assert_called_once()

    # 2 запроса PUT на создание директорий и 1 PUT на саму загрузку файла = 3
    assert mock_put.call_count == 3


def test_save_geolocation(client, db):
    user_id = create_test_user(client)

    response = client.post(
        "/api/geolocations",
        json={"user_id": user_id, "x": 55.7558, "y": 37.6173},
        headers=HEADERS,
    )

    assert response.status_code == 200
    assert "geo_id" in response.json()


@patch("app.services.yandex_disk.redis_client")
@patch("app.services.yandex_disk.requests.get")
@patch("app.services.yandex_disk.requests.put")
@patch("app.services.observation_service.get_and_delete_stashed_image")
def test_link_photo_geo(
    mock_get_stashed, mock_put, mock_get, mock_redis, client, db, monkeypatch
):
    monkeypatch.setenv("YANDEX_DISK_TOKEN", "valid_mock_token")

    mock_redis.get.return_value = None

    # Подсовываем фейковый файл
    mock_get_stashed.return_value = {
        "filename": "test.jpg",
        "content_type": "image/jpeg",
        "bytes": b"fake",
    }

    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"href": "https://mock-upload-url"}
    mock_put.return_value.status_code = 201

    user_id = create_test_user(client)

    # 1. Создаем пост (через новый JSON формат)
    post_resp = client.post(
        "/api/posts",
        headers=HEADERS,
        json={
            "user_id": user_id,
            "description": "test",
            "ai_plant_id": -1,
            "ai_confidence": 0.0,
            "user_plant_id": 5,
            "temp_file_id": "dummy_id",
        },
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
        "/api/link-photo-geo",
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
    reason="Valid YANDEX_DISK_TOKEN is required for real integration test",
)
@patch("app.services.observation_service.get_and_delete_stashed_image")
def test_upload_post_real_yandex_disk(mock_get_stashed, client, db):
    """
    Этот тест реально отправляет файл на Я.Диск.
    Так как мы используем кеширование в Redis, тест подменит
    содержимое из Redis своим файлом.
    """
    user_id = create_test_user(client)

    # Подмешиваем файл для загрузки
    mock_get_stashed.return_value = {
        "filename": "integration_test.txt",
        "content_type": "text/plain",
        "bytes": b"Integration test file created by automated test.",
    }

    data = {
        "user_id": user_id,
        "description": "Integration test",
        "ai_plant_id": -1,
        "ai_confidence": 0.0,
        "user_plant_id": 1,
        "temp_file_id": "dummy_integration_id",
    }

    response = client.post("/api/posts", headers=HEADERS, json=data)

    assert response.status_code == 200
    assert "post_id" in response.json()
