HEADERS = {"X-Api-Key": "my_super_secret_api_key_for_bots"}


# ---------------------------------------------------------
# 1. ТЕСТЫ КОМАНД (ADMIN & PUBLIC API)
# ---------------------------------------------------------


def test_create_command(client, db):
    response = client.post(
        "/api/admin/commands",
        json={
            "command_name": "/start",
            "command_description": "Запустить бота",
            "platform_enabled": "ALL",
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["command_name"] == "/start"
    assert "command_id" in data


def test_get_commands_platform_filtering(client, db):
    # Создаем команду только для Telegram
    client.post(
        "/api/admin/commands",
        json={"command_name": "/tg_only", "platform_enabled": "TG"},
        headers=HEADERS,
    )
    # Создаем команду только для MAX
    client.post(
        "/api/admin/commands",
        json={"command_name": "/max_only", "platform_enabled": "MAX"},
        headers=HEADERS,
    )
    # Создаем универсальную команду
    client.post(
        "/api/admin/commands",
        json={"command_name": "/universal", "platform_enabled": "ALL"},
        headers=HEADERS,
    )

    # Проверяем выдачу для Telegram
    resp_tg = client.get("/api/settings/commands?platform=TG", headers=HEADERS)
    assert resp_tg.status_code == 200
    names_tg = [cmd["command_name"] for cmd in resp_tg.json()]
    assert "/tg_only" in names_tg
    assert "/universal" in names_tg
    assert "/max_only" not in names_tg

    # Проверяем выдачу для MAX
    resp_max = client.get("/api/settings/commands?platform=MAX", headers=HEADERS)
    assert resp_max.status_code == 200
    names_max = [cmd["command_name"] for cmd in resp_max.json()]
    assert "/max_only" in names_max
    assert "/universal" in names_max
    assert "/tg_only" not in names_max


def test_update_command(client, db):
    create_resp = client.post(
        "/api/admin/commands",
        json={"command_name": "/old_cmd", "platform_enabled": "ALL"},
        headers=HEADERS,
    )
    cmd_id = create_resp.json()["command_id"]

    update_resp = client.patch(
        f"/api/admin/commands/{cmd_id}",
        json={"command_name": "/new_cmd", "command_description": "Updated"},
        headers=HEADERS,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["command_name"] == "/new_cmd"
    assert update_resp.json()["command_description"] == "Updated"


def test_delete_command(client, db):
    create_resp = client.post(
        "/api/admin/commands",
        json={"command_name": "/delete_me", "platform_enabled": "ALL"},
        headers=HEADERS,
    )
    cmd_id = create_resp.json()["command_id"]

    delete_resp = client.delete(f"/api/admin/commands/{cmd_id}", headers=HEADERS)
    assert delete_resp.status_code == 200

    # Проверяем, что команда удалена (patch должен вернуть 404)
    update_resp = client.patch(
        f"/api/admin/commands/{cmd_id}",
        json={"command_name": "/try_update"},
        headers=HEADERS,
    )
    assert update_resp.status_code == 404


def test_command_not_found(client, db):
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.patch(
        f"/api/admin/commands/{fake_uuid}",
        json={"command_name": "/fail"},
        headers=HEADERS,
    )
    assert response.status_code == 404


# ---------------------------------------------------------
# 2. ТЕСТЫ FAQ (ADMIN & PUBLIC API)
# ---------------------------------------------------------


def test_create_faq(client, db):
    response = client.post(
        "/api/admin/faq/sections",
        json={
            "title": "Как отправить фото?",
            "description": "Нажмите скрепку",
            "sort_order": 1,
            "is_enabled": True,
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Как отправить фото?"
    assert "section_id" in data


def test_faq_visibility_rules(client, db):
    # Создаем активный FAQ
    client.post(
        "/api/admin/faq/sections",
        json={
            "title": "Активный раздел",
            "description": "Видно всем",
            "is_enabled": True,
        },
        headers=HEADERS,
    )
    # Создаем скрытый FAQ
    client.post(
        "/api/admin/faq/sections",
        json={
            "title": "Скрытый раздел",
            "description": "Черновик",
            "is_enabled": False,
        },
        headers=HEADERS,
    )

    # Admin API - должен видеть все разделы (в т.ч. скрытые)
    admin_resp = client.get("/api/admin/faq/sections", headers=HEADERS)
    assert admin_resp.status_code == 200
    admin_titles = [f["title"] for f in admin_resp.json()]
    assert "Активный раздел" in admin_titles
    assert "Скрытый раздел" in admin_titles

    # Public API - должен видеть только активные
    public_resp = client.get("/api/faq/sections", headers=HEADERS)
    assert public_resp.status_code == 200
    public_titles = [f["title"] for f in public_resp.json()]
    assert "Активный раздел" in public_titles
    assert "Скрытый раздел" not in public_titles


def test_update_faq(client, db):
    create_resp = client.post(
        "/api/admin/faq/sections",
        json={"title": "Old Title", "description": "Old Desc"},
        headers=HEADERS,
    )
    faq_id = create_resp.json()["section_id"]

    update_resp = client.patch(
        f"/api/admin/faq/sections/{faq_id}",
        json={"title": "New Title", "is_enabled": False},
        headers=HEADERS,
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["title"] == "New Title"
    assert data["is_enabled"] is False


def test_delete_faq(client, db):
    create_resp = client.post(
        "/api/admin/faq/sections",
        json={"title": "To be deleted", "description": "Desc"},
        headers=HEADERS,
    )
    faq_id = create_resp.json()["section_id"]

    delete_resp = client.delete(f"/api/admin/faq/sections/{faq_id}", headers=HEADERS)
    assert delete_resp.status_code == 200

    admin_resp = client.get("/api/admin/faq/sections", headers=HEADERS)
    titles = [f["title"] for f in admin_resp.json()]
    assert "To be deleted" not in titles


# ---------------------------------------------------------
# 3. ТЕСТ ПОЛИТИКИ КОНФИДЕНЦИАЛЬНОСТИ
# ---------------------------------------------------------


def test_privacy_policy(client, db):
    # Тестируем публичный эндпоинт, который не ходит в БД
    response = client.get("/api/privacy-policy", headers=HEADERS)
    assert response.status_code == 200

    data = response.json()
    assert "text" in data
    assert len(data["text"]) > 0

    assert "pdf_link" in data
    assert str(data["pdf_link"]).endswith(".pdf")
