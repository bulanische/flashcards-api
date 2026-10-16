from uuid import uuid4

import pytest
from httpx import AsyncClient




@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Проверяет регистрацию нового пользователя."""
    # Создаём уникальный email, чтобы повторные запуски не конфликтовали.
    email = f"test-{uuid4().hex}@example.com"
    password = "Test-password-123!"

    # Отправляем данные нового пользователя в API.
    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    # Проверяем успешную регистрацию и данные созданного пользователя.
    assert response.status_code == 201
    assert response.json()["email"] == email


@pytest.mark.asyncio
async def test_login_and_get_current_user(client: AsyncClient):
    """Проверяет вход пользователя и доступ по JWT-токену."""
    # Создаём уникальные учётные данные для этого теста.
    email = f"test-{uuid4().hex}@example.com"
    password = "Test-password-123!"

    # Сначала регистрируем пользователя через настоящий API.
    registration_response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )
    assert registration_response.status_code == 201

    # Входим через OAuth2-форму: email передаётся в поле username.
    login_response = await client.post(
        "/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )

    # Проверяем, что сервер выдал JWT-токен.
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert token_data["token_type"].lower() == "bearer"
    assert token_data["access_token"]

    # Передаём токен в заголовке для запроса текущего пользователя.
    user_response = await client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token_data['access_token']}",
        },
    )

    # Проверяем, что токен позволяет получить данные нужного пользователя.
    assert user_response.status_code == 200
    assert user_response.json()["email"] == email
    
@pytest.mark.asyncio
async def test_get_current_user_without_token(client: AsyncClient):
    """Проверяет отказ в доступе к профилю без токена."""
    # Отправляем запрос без заголовка авторизации.
    response = await client.get("/auth/me")

    # Проверяем, что API требует авторизацию.
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_with_invalid_token(client: AsyncClient):
    """Проверяет отказ в доступе с недействительным токеном."""
    # Передаём заведомо поддельный токен.
    response = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    # Проверяем, что API не принимает поддельный токен.
    assert response.status_code == 401

