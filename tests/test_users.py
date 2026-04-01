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
    # First register a user
    response = client.post(
        "/api/users/register",
        json={
            "platform_name": "telegram",
            "platform_user_id": "123",
            "fio": "Test User",
        },
        headers={"X-Api-Key": "my_super_secret_api_key_for_bots"},
    )
    user_id = response.json()["user_id"]

    # Mock redis get
    mock_redis.get.return_value = user_id
    mock_redis.delete.return_value = None

    response = client.post(
        "/api/users/link-account",
        params={
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


def test_update_contacts(client, db):
    # First register
    response = client.post(
        "/api/users/register",
        json={
            "platform_name": "telegram",
            "platform_user_id": "123",
            "fio": "Test User",
        },
        headers={"X-Api-Key": "my_super_secret_api_key_for_bots"},
    )
    user_id = response.json()["user_id"]

    response = client.patch(
        f"/api/users/{user_id}/contacts",
        json={"email": "new@example.com", "phone_number": "123456789"},
        headers={"X-Api-Key": "my_super_secret_api_key_for_bots"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "new@example.com"


def test_set_consent(client, db):
    # First register
    response = client.post(
        "/api/users/register",
        json={
            "platform_name": "telegram",
            "platform_user_id": "123",
            "fio": "Test User",
        },
        headers={"X-Api-Key": "my_super_secret_api_key_for_bots"},
    )
    user_id = response.json()["user_id"]

    response = client.post(
        f"/api/users/{user_id}/consent",
        params={"consent": True},
        headers={"X-Api-Key": "my_super_secret_api_key_for_bots"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Consent updated"


def test_set_dobro_id(client, db):
    # First register
    response = client.post(
        "/api/users/register",
        json={
            "platform_name": "telegram",
            "platform_user_id": "123",
            "fio": "Test User",
        },
        headers={"X-Api-Key": "my_super_secret_api_key_for_bots"},
    )
    user_id = response.json()["user_id"]

    response = client.post(
        f"/api/users/{user_id}/dobroid",
        params={"dobro_id": "dobro123"},
        headers={"X-Api-Key": "my_super_secret_api_key_for_bots"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Dobro ID updated"


def test_delete_dobro_id(client, db):
    # First register
    response = client.post(
        "/api/users/register",
        json={
            "platform_name": "telegram",
            "platform_user_id": "123",
            "fio": "Test User",
            "dobro_id": "dobro123",
        },
        headers={"X-Api-Key": "my_super_secret_api_key_for_bots"},
    )
    user_id = response.json()["user_id"]

    response = client.delete(
        f"/api/users/{user_id}/dobroid",
        headers={"X-Api-Key": "my_super_secret_api_key_for_bots"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Dobro ID removed"


def test_get_user_not_found(client, db):
    response = client.get(
        "/api/users/by-platform/telegram/999",
        headers={"X-Api-Key": "my_super_secret_api_key_for_bots"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_update_contacts_not_found(client, db):
    response = client.patch(
        "/api/users/00000000-0000-0000-0000-000000000000/contacts",
        json={"email": "test@example.com"},
        headers={"X-Api-Key": "my_super_secret_api_key_for_bots"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
