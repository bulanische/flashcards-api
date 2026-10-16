from types import SimpleNamespace
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.auth.router import current_user
from app.main import app
from app.models.language import Language
from app.models.user import User
from app.models.deck import Deck



@pytest.mark.asyncio
async def test_decks_require_auth(client: AsyncClient):
    """Проверяет, что список колод недоступен без авторизации."""

    # Отправляем запрос без токена авторизации.
    response = await client.get("/decks/")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_decks_for_current_user(client: AsyncClient):
    """Проверяет получение колод только текущего пользователя."""

    # Подменяем авторизацию тестовым пользователем.
    test_user = SimpleNamespace(id=-1)

    async def override_current_user():
        """Возвращает пользователя для теста."""

        return test_user

    app.dependency_overrides[current_user] = override_current_user

    try:
        # Запрашиваем список колод от имени тестового пользователя.
        response = await client.get("/decks/")
    finally:
        # Убираем подмену авторизации после запроса.
        app.dependency_overrides.pop(current_user, None)

    assert response.status_code == 200

    # Проверяем, что API не возвращает чужие колоды.
    decks = response.json()
    assert all(deck["user_id"] == test_user.id for deck in decks)


@pytest.mark.asyncio
async def test_create_deck(client, test_session_factory):
    """Проверяет создание колоды и отклонение дубликата."""

    # Создаём уникальный суффикс для данных теста.
    suffix = uuid4().hex[:8]

    async with test_session_factory() as session:
        # Создаём владельца колоды.
        user = User(
            email=f"deck-test-{suffix}@example.com",
            hashed_password="test-password-hash",
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        session.add(user)
        await session.flush()

        # Создаём два системных языка.
        language_a = Language(
            name="Russian",
            native_name="Русский",
            code=f"ru-{suffix}",
        )
        language_b = Language(
            name="Spanish",
            native_name="Español",
            code=f"es-{suffix}",
        )
        session.add_all([language_a, language_b])
        await session.commit()

        # Сохраняем идентификаторы для запросов.
        user_id = user.id
        language_a_id = language_a.id
        language_b_id = language_b.id

    # Подменяем авторизацию тестовым пользователем.
    async def override_current_user():
        """Возвращает тестового пользователя."""

        return SimpleNamespace(id=user_id)

    app.dependency_overrides[current_user] = override_current_user

    try:
        # Создаём колоду первым запросом.
        response = await client.post(
            "/decks/",
            json={
                "name": "Русский — Испанский",
                "language_a_id": language_a_id,
                "language_b_id": language_b_id,
            },
        )

        # Проверяем успешное создание.
        assert response.status_code == 200
        deck = response.json()
        assert deck["name"] == "Русский — Испанский"
        assert deck["user_id"] == user_id
        assert deck["language_a_id"] == language_a_id
        assert deck["language_b_id"] == language_b_id

        # Повторяем запрос с теми же данными.
        duplicate_response = await client.post(
            "/decks/",
            json={
                "name": "Русский — Испанский",
                "language_a_id": language_a_id,
                "language_b_id": language_b_id,
            },
        )

        # Проверяем, что API отклоняет дубликат.
        assert duplicate_response.status_code == 409

    finally:
        # Убираем подмену авторизации даже при ошибке теста.
        app.dependency_overrides.pop(current_user, None)

@pytest.mark.asyncio
async def test_user_cannot_modify_another_users_deck(
    client,
    test_session_factory,
):
    """Проверяет запрет изменения и удаления чужой колоды."""

    # Создаём уникальный суффикс для тестовых данных.
    suffix = uuid4().hex[:8]

    async with test_session_factory() as session:
        # Создаём владельца колоды и другого пользователя.
        owner = User(
            email=f"owner-{suffix}@example.com",
            hashed_password="test-password-hash",
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        other_user = User(
            email=f"other-{suffix}@example.com",
            hashed_password="test-password-hash",
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        session.add_all([owner, other_user])
        await session.flush()

        # Создаём два системных языка для колоды.
        language_a = Language(
            name="Russian",
            native_name="Русский",
            code=f"ru-{suffix}",
        )
        language_b = Language(
            name="Spanish",
            native_name="Español",
            code=f"es-{suffix}",
        )
        session.add_all([language_a, language_b])
        await session.flush()

        # Создаём колоду, принадлежащую только владельцу.
        deck = Deck(
            name="Чужая колода",
            user_id=owner.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        session.add(deck)
        await session.commit()

        # Сохраняем ID до закрытия сессии.
        deck_id = deck.id
        owner_id = owner.id
        other_user_id = other_user.id

    # Подменяем авторизацию пользователем, который не владеет колодой.
    async def override_current_user():
        """Возвращает пользователя без прав на чужую колоду."""

        return SimpleNamespace(id=other_user_id)

    app.dependency_overrides[current_user] = override_current_user

    try:
        # Пытаемся изменить чужую колоду.
        update_response = await client.put(
            f"/decks/{deck_id}",
            json={"name": "Подменённое название"},
        )

        # Пытаемся удалить чужую колоду.
        delete_response = await client.delete(f"/decks/{deck_id}")
    finally:
        # Восстанавливаем обычную авторизацию после теста.
        app.dependency_overrides.pop(current_user, None)

    # Оба действия должны быть запрещены.
    assert update_response.status_code == 404
    assert delete_response.status_code == 404

    async with test_session_factory() as session:
        # Проверяем, что колода осталась у прежнего владельца.
        saved_deck = await session.scalar(
            select(Deck).where(Deck.id == deck_id)
        )

        assert saved_deck is not None
        assert saved_deck.user_id == owner_id
        assert saved_deck.name == "Чужая колода"


@pytest.mark.asyncio
async def test_user_can_update_and_delete_own_deck(
    client,
    test_session_factory,
):
    """Проверяет изменение и удаление собственной колоды."""

    # Создаём уникальный суффикс для тестовых данных.
    suffix = uuid4().hex[:8]

    async with test_session_factory() as session:
        # Создаём пользователя — владельца колоды.
        user = User(
            email=f"deck-owner-{suffix}@example.com",
            hashed_password="test-password-hash",
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        session.add(user)
        await session.flush()

        # Создаём два системных языка.
        language_a = Language(
            name="Russian",
            native_name="Русский",
            code=f"ru-{suffix}",
        )
        language_b = Language(
            name="Spanish",
            native_name="Español",
            code=f"es-{suffix}",
        )
        session.add_all([language_a, language_b])
        await session.flush()

        # Создаём колоду напрямую в тестовой базе.
        deck = Deck(
            name="Исходное название",
            user_id=user.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        session.add(deck)
        await session.commit()

        # Сохраняем ID для последующих запросов.
        user_id = user.id
        deck_id = deck.id

    # Подменяем авторизацию владельцем колоды.
    async def override_current_user():
        """Возвращает владельца колоды."""

        return SimpleNamespace(id=user_id)

    app.dependency_overrides[current_user] = override_current_user

    try:
        # Изменяем название колоды через API.
        update_response = await client.put(
            f"/decks/{deck_id}",
            json={"name": "Новое название"},
        )

        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Новое название"

        # Повторно сохраняем то же название без конфликта.
        response = await client.put(
            f"/decks/{deck_id}",
            json={"name": "Новое название"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Новое название"

        # Удаляем собственную колоду.
        delete_response = await client.delete(f"/decks/{deck_id}")

        assert delete_response.status_code == 204

    finally:
        # Убираем подмену авторизации после запросов.
        app.dependency_overrides.pop(current_user, None)

    async with test_session_factory() as session:
        # Проверяем, что удалённая колода больше не существует.
        saved_deck = await session.get(Deck, deck_id)

        assert saved_deck is None


@pytest.mark.asyncio
async def test_create_deck_rejects_unavailable_languages(
    client,
    test_session_factory,
):
    """Проверяет отклонение несуществующего и чужого языка."""

    # Создаём уникальный суффикс для тестовых данных.
    suffix = uuid4().hex[:8]

    async with test_session_factory() as session:
        # Создаём текущего пользователя и владельца другого языка.
        user = User(
            email=f"language-user-{suffix}@example.com",
            hashed_password="test-password-hash",
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        other_user = User(
            email=f"language-owner-{suffix}@example.com",
            hashed_password="test-password-hash",
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        session.add_all([user, other_user])
        await session.flush()

        # Создаём системный язык, доступный обоим пользователям.
        system_language = Language(
            name="Spanish",
            native_name="Español",
            code=f"es-{suffix}",
        )

        # Создаём пользовательский язык, принадлежащий другому пользователю.
        foreign_language = Language(
            name="French",
            native_name="Français",
            code=f"fr-{suffix}",
            user_id=other_user.id,
        )
        session.add_all([system_language, foreign_language])
        await session.commit()

        # Сохраняем идентификаторы до закрытия сессии.
        user_id = user.id
        system_language_id = system_language.id
        foreign_language_id = foreign_language.id

    # Подменяем авторизацию текущим пользователем.
    async def override_current_user():
        """Возвращает пользователя, создающего колоду."""

        return SimpleNamespace(id=user_id)

    app.dependency_overrides[current_user] = override_current_user

    try:
        # Пытаемся создать колоду с несуществующим языком.
        missing_language_response = await client.post(
            "/decks/",
            json={
                "name": "Несуществующий язык",
                "language_a_id": 999999999,
                "language_b_id": system_language_id,
            },
        )

        # Пытаемся использовать язык, принадлежащий другому пользователю.
        foreign_language_response = await client.post(
            "/decks/",
            json={
                "name": "Чужой язык",
                "language_a_id": foreign_language_id,
                "language_b_id": system_language_id,
            },
        )
    finally:
        # Убираем подмену авторизации даже при ошибке.
        app.dependency_overrides.pop(current_user, None)

    # Проверяем, что оба недоступных языка отклонены.
    assert missing_language_response.status_code == 404
    assert foreign_language_response.status_code == 404

@pytest.mark.asyncio
async def test_update_deck_rejects_duplicate_name_and_languages(
    client,
    test_session_factory,
):
    """Проверяет запрет одинаковых названий колод с той же парой языков."""

    # Создаём уникальный суффикс для тестовых данных.
    suffix = uuid4().hex[:8]

    async with test_session_factory() as session:
        # Создаём пользователя.
        user = User(
            email=f"deck-duplicate-{suffix}@example.com",
            hashed_password="test-password-hash",
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        session.add(user)
        await session.flush()

        # Создаём два системных языка.
        language_a = Language(
            name="Russian",
            native_name="Русский",
            code=f"ru-{suffix}",
        )
        language_b = Language(
            name="Spanish",
            native_name="Español",
            code=f"es-{suffix}",
        )
        session.add_all([language_a, language_b])
        await session.flush()

        # Создаём две колоды с одинаковыми языками.
        first_deck = Deck(
            name="Первая колода",
            user_id=user.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        second_deck = Deck(
            name="Вторая колода",
            user_id=user.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        session.add_all([first_deck, second_deck])
        await session.commit()

        # Сохраняем идентификаторы перед завершением сессии.
        user_id = user.id
        second_deck_id = second_deck.id

    # Подменяем авторизацию владельцем колод.
    async def override_current_user():
        """Возвращает пользователя — владельца колод."""

        return SimpleNamespace(id=user_id)

    app.dependency_overrides[current_user] = override_current_user

    try:
        # Пытаемся присвоить второй колоде название первой.
        response = await client.put(
            f"/decks/{second_deck_id}",
            json={"name": "Первая колода"},
        )

        assert response.status_code == 409
        assert response.json()["detail"] == (
            "A deck with the same name and languages already exists."
        )
    finally:
        # Убираем подмену авторизации после теста.
        app.dependency_overrides.pop(current_user, None)
