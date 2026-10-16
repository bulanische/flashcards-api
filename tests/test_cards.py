from types import SimpleNamespace
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.auth.router import current_user
from app.main import app
from app.models.card import Card
from app.models.deck import Deck
from app.models.language import Language
from app.models.user import User

@pytest.mark.asyncio
async def test_create_card_rejects_missing_fields(client: AsyncClient):
    """Проверяет отказ при создании карточки без обязательных полей."""
    # Подменяем пользователя, чтобы пройти проверку авторизации.
    app.dependency_overrides[current_user] = lambda: SimpleNamespace(id=-1)

    try:
        # Отправляем неполные данные карточки.
        response = await client.post(
            "/cards/",
            json={"word": "hola"},
        )

        # Проверяем, что запрос отклонён из-за отсутствующих полей.
        assert response.status_code == 422
    finally:
        # Удаляем подмену зависимости после теста.
        app.dependency_overrides.pop(current_user, None)


@pytest.mark.asyncio
async def test_update_nonexistent_card(client: AsyncClient):
    """Проверяет обновление несуществующей карточки."""
    # Подменяем пользователя, чтобы проверить именно поиск карточки.
    app.dependency_overrides[current_user] = lambda: SimpleNamespace(id=-1)

    try:
        # Отправляем запрос с заведомо несуществующим идентификатором.
        response = await client.put(
            "/cards/999999999",
            json={
                "word": "hola",
                "translation": "привет",
                "deck_id": 999999999,
            },
        )

        # API должен сообщить, что карточка не найдена.
        assert response.status_code == 404
    finally:
        # Убираем подмену зависимости даже при ошибке теста.
        app.dependency_overrides.pop(current_user, None)


@pytest.mark.asyncio
async def test_delete_nonexistent_card(client: AsyncClient):
    """Проверяет удаление несуществующей карточки."""
    # Подменяем пользователя для изолированной проверки доступа.
    app.dependency_overrides[current_user] = lambda: SimpleNamespace(id=-1)

    try:
        # Пытаемся удалить карточку, которой нет в базе.
        response = await client.delete("/cards/999999999")

        # API должен вернуть ошибку отсутствующей карточки.
        assert response.status_code == 404
    finally:
        # Восстанавливаем обычную авторизацию.
        app.dependency_overrides.pop(current_user, None)

@pytest.mark.asyncio
async def test_create_card(client: AsyncClient, test_session_factory):
    """Проверяет создание карточки в собственной колоде пользователя."""

    # Создаём уникальные данные для теста.
    suffix = uuid4().hex[:8]

    async with test_session_factory() as session:
        # Создаём пользователя — владельца будущей колоды.
        user = User(
            email=f"card-user-{suffix}@example.com",
            hashed_password="test-password-hash",
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        session.add(user)
        await session.flush()

        # Создаём два языка, которые будут использоваться в колоде.
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

        # Создаём колоду с этими языками.
        deck = Deck(
            name="Русский — Испанский",
            user_id=user.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        session.add(deck)
        await session.commit()

        # Сохраняем идентификаторы для запроса после закрытия сессии.
        user_id = user.id
        deck_id = deck.id
        language_a_id = language_a.id
        language_b_id = language_b.id

    # Подменяем авторизацию владельцем созданной колоды.
    app.dependency_overrides[current_user] = (
        lambda: SimpleNamespace(id=user_id)
    )

    try:
        # Отправляем запрос на создание карточки через API.
        response = await client.post(
            "/cards/",
            json={
                "word": "hola",
                "translation": "привет",
                "deck_id": deck_id,
                "language_a_id": language_a_id,
                "language_b_id": language_b_id,
            },
        )

        # Проверяем успешное создание и содержимое ответа.
        assert response.status_code == 200

        created_card = response.json()
        assert created_card["id"] is not None
        assert created_card["word"] == "hola"
        assert created_card["translation"] == "привет"
        assert created_card["deck_id"] == deck_id
        assert created_card["language_a_id"] == language_a_id
        assert created_card["language_b_id"] == language_b_id

    finally:
        # Убираем подмену авторизации после запроса.
        app.dependency_overrides.pop(current_user, None)

    async with test_session_factory() as session:
        # Проверяем, что карточка действительно сохранена в базе.
        result = await session.execute(
            select(Card).where(
                Card.deck_id == deck_id,
                Card.word == "hola",
            )
        )
        saved_card = result.scalars().one()

        assert saved_card.translation == "привет"


@pytest.mark.asyncio
async def test_create_card_rejects_mismatched_languages(
    client: AsyncClient,
    test_session_factory,
):
    """Проверяет отказ при несовпадении языков карточки и колоды."""

    # Создаём уникальные данные для теста.
    suffix = uuid4().hex[:8]

    async with test_session_factory() as session:
        # Создаём пользователя — владельца колоды.
        user = User(
            email=f"card-lang-{suffix}@example.com",
            hashed_password="test-password-hash",
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        session.add(user)
        await session.flush()

        # Создаём три языка: два для колоды и один лишний.
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
        language_c = Language(
            name="English",
            native_name="English",
            code=f"en-{suffix}",
        )
        session.add_all([language_a, language_b, language_c])
        await session.flush()

        # Создаём колоду только для русского и испанского языков.
        deck = Deck(
            name="Русский — Испанский",
            user_id=user.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        session.add(deck)
        await session.commit()

        # Сохраняем идентификаторы для HTTP-запроса.
        user_id = user.id
        deck_id = deck.id
        language_a_id = language_a.id
        language_c_id = language_c.id

    # Подменяем авторизацию пользователем — владельцем колоды.
    app.dependency_overrides[current_user] = (
        lambda: SimpleNamespace(id=user_id)
    )

    try:
        # Передаём английский вместо испанского.
        response = await client.post(
            "/cards/",
            json={
                "word": "hello",
                "translation": "привет",
                "deck_id": deck_id,
                "language_a_id": language_a_id,
                "language_b_id": language_c_id,
            },
        )

        # API должен отклонить карточку с неподходящим языком.
        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Card languages do not match the deck languages."
        )

    finally:
        # Убираем подмену авторизации после запроса.
        app.dependency_overrides.pop(current_user, None)


@pytest.mark.asyncio
async def test_create_card_rejects_nonexistent_deck(
    client: AsyncClient,
):
    """Проверяет отказ при создании карточки в несуществующей колоде."""

    # Подменяем авторизацию, чтобы запрос дошёл до проверки колоды.
    app.dependency_overrides[current_user] = (
        lambda: SimpleNamespace(id=-1)
    )

    try:
        # Отправляем карточку с идентификатором отсутствующей колоды.
        response = await client.post(
            "/cards/",
            json={
                "word": "hola",
                "translation": "привет",
                "deck_id": 999999999,
                "language_a_id": 1,
                "language_b_id": 2,
            },
        )

        # API должен сообщить, что колода недоступна.
        assert response.status_code == 404
        assert response.json()["detail"] == (
            "Deck not found or unavailable."
        )

    finally:
        # Удаляем подмену авторизации после теста.
        app.dependency_overrides.pop(current_user, None)


@pytest.mark.asyncio
async def test_create_card_rejects_duplicate(
    client: AsyncClient,
    test_session_factory,
):
    """Проверяет отказ при создании дублирующейся карточки."""

    # Создаём уникальные данные для теста.
    suffix = uuid4().hex[:8]

    async with test_session_factory() as session:
        # Создаём пользователя — владельца колоды.
        user = User(
            email=f"card-duplicate-{suffix}@example.com",
            hashed_password="test-password-hash",
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        session.add(user)
        await session.flush()

        # Создаём два языка для колоды.
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

        # Создаём колоду пользователя.
        deck = Deck(
            name="Русский — Испанский",
            user_id=user.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        session.add(deck)
        await session.commit()

        # Сохраняем идентификаторы для запросов.
        user_id = user.id
        deck_id = deck.id
        language_a_id = language_a.id
        language_b_id = language_b.id

    # Подменяем авторизацию владельцем колоды.
    app.dependency_overrides[current_user] = (
        lambda: SimpleNamespace(id=user_id)
    )

    payload = {
        "word": "hola",
        "translation": "привет",
        "deck_id": deck_id,
        "language_a_id": language_a_id,
        "language_b_id": language_b_id,
    }

    try:
        # Сначала создаём карточку, чтобы появилась запись для проверки.
        first_response = await client.post("/cards/", json=payload)
        assert first_response.status_code == 200

        # Повторяем запрос с теми же данными.
        duplicate_response = await client.post("/cards/", json=payload)

        # API должен отклонить дубликат с конфликтом.
        assert duplicate_response.status_code == 409
        assert duplicate_response.json()["detail"] == (
            "A card with the same content already exists in this deck."
        )

    finally:
        # Удаляем подмену авторизации после теста.
        app.dependency_overrides.pop(current_user, None)


@pytest.mark.asyncio
async def test_update_card(client: AsyncClient, test_session_factory):
    """Проверяет успешное обновление собственной карточки."""

    # Создаём уникальные данные для теста.
    suffix = uuid4().hex[:8]

    async with test_session_factory() as session:
        # Создаём пользователя — владельца карточки.
        user = User(
            email=f"card-update-{suffix}@example.com",
            hashed_password="test-password-hash",
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        session.add(user)
        await session.flush()

        # Создаём два языка для колоды.
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

        # Создаём колоду пользователя.
        deck = Deck(
            name="Русский — Испанский",
            user_id=user.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        session.add(deck)
        await session.flush()

        # Создаём исходную карточку.
        card = Card(
            word="hola",
            translation="привет",
            deck_id=deck.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        session.add(card)
        await session.commit()

        # Сохраняем идентификаторы для дальнейших запросов.
        user_id = user.id
        deck_id = deck.id
        card_id = card.id

    # Подменяем авторизацию владельцем карточки.
    app.dependency_overrides[current_user] = (
        lambda: SimpleNamespace(id=user_id)
    )

    try:
        # Меняем слово и перевод карточки через API.
        response = await client.put(
            f"/cards/{card_id}",
            json={
                "word": "buenos días",
                "translation": "доброе утро",
                "deck_id": deck_id,
            },
        )

        # Проверяем успешный ответ и новые значения.
        assert response.status_code == 200
        updated_card = response.json()
        assert updated_card["id"] == card_id
        assert updated_card["word"] == "buenos días"
        assert updated_card["translation"] == "доброе утро"

    finally:
        # Убираем подмену авторизации после запроса.
        app.dependency_overrides.pop(current_user, None)

    async with test_session_factory() as session:
        # Проверяем, что изменения действительно сохранены.
        updated_card = await session.get(Card, card_id)

        assert updated_card is not None
        assert updated_card.word == "buenos días"
        assert updated_card.translation == "доброе утро"


@pytest.mark.asyncio
async def test_update_card_rejects_duplicate(
    client: AsyncClient,
    test_session_factory,
):
    """Проверяет отказ при обновлении карточки до дубликата."""

    # Создаём уникальные данные для теста.
    suffix = uuid4().hex[:8]

    async with test_session_factory() as session:
        # Создаём пользователя — владельца колоды.
        user = User(
            email=f"card-update-duplicate-{suffix}@example.com",
            hashed_password="test-password-hash",
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        session.add(user)
        await session.flush()

        # Создаём два языка для колоды.
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

        # Создаём колоду.
        deck = Deck(
            name="Русский — Испанский",
            user_id=user.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        session.add(deck)
        await session.flush()

        # Создаём две карточки с разным содержимым.
        first_card = Card(
            word="hola",
            translation="привет",
            deck_id=deck.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        second_card = Card(
            word="adiós",
            translation="пока",
            deck_id=deck.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        session.add_all([first_card, second_card])
        await session.commit()

        # Сохраняем идентификаторы для HTTP-запроса.
        user_id = user.id
        deck_id = deck.id
        second_card_id = second_card.id

    # Подменяем авторизацию владельцем колоды.
    app.dependency_overrides[current_user] = (
        lambda: SimpleNamespace(id=user_id)
    )

    try:
        # Пытаемся изменить вторую карточку, повторив первую.
        response = await client.put(
            f"/cards/{second_card_id}",
            json={
                "word": "hola",
                "translation": "привет",
                "deck_id": deck_id,
            },
        )

        # API должен отклонить дубликат.
        assert response.status_code == 409
        assert response.json()["detail"] == (
            "A card with the same content already exists in this deck."
        )

    finally:
        # Убираем подмену авторизации после запроса.
        app.dependency_overrides.pop(current_user, None)

    async with test_session_factory() as session:
        # Проверяем, что исходная карточка не изменилась.
        unchanged_card = await session.get(Card, second_card_id)

        assert unchanged_card is not None
        assert unchanged_card.word == "adiós"
        assert unchanged_card.translation == "пока"


@pytest.mark.asyncio
async def test_user_cannot_modify_another_users_card(
    client: AsyncClient,
    test_session_factory,
):
    """Проверяет запрет изменения и удаления чужой карточки."""

    # Создаём уникальные данные для теста.
    suffix = uuid4().hex[:8]

    async with test_session_factory() as session:
        # Создаём владельца карточки и другого пользователя.
        owner = User(
            email=f"card-owner-{suffix}@example.com",
            hashed_password="test-password-hash",
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        other_user = User(
            email=f"card-other-{suffix}@example.com",
            hashed_password="test-password-hash",
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        session.add_all([owner, other_user])
        await session.flush()

        # Создаём языки для колоды владельца.
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

        # Создаём колоду и карточку первого пользователя.
        deck = Deck(
            name="Русский — Испанский",
            user_id=owner.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        session.add(deck)
        await session.flush()

        card = Card(
            word="hola",
            translation="привет",
            deck_id=deck.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        session.add(card)
        await session.commit()

        # Сохраняем идентификаторы для запросов.
        other_user_id = other_user.id
        deck_id = deck.id
        card_id = card.id

    # Авторизуем запросы от имени пользователя, который не владеет карточкой.
    app.dependency_overrides[current_user] = (
        lambda: SimpleNamespace(id=other_user_id)
    )

    try:
        # Пытаемся изменить чужую карточку.
        update_response = await client.put(
            f"/cards/{card_id}",
            json={
                "word": "buenos días",
                "translation": "доброе утро",
                "deck_id": deck_id,
            },
        )

        # Пытаемся удалить чужую карточку.
        delete_response = await client.delete(f"/cards/{card_id}")

        # Оба запроса должны выглядеть как обращение к отсутствующей карточке.
        assert update_response.status_code == 404
        assert delete_response.status_code == 404

    finally:
        # Убираем подмену авторизации после запросов.
        app.dependency_overrides.pop(current_user, None)

    async with test_session_factory() as session:
        # Проверяем, что карточка владельца осталась нетронутой.
        unchanged_card = await session.get(Card, card_id)

        assert unchanged_card is not None
        assert unchanged_card.word == "hola"
        assert unchanged_card.translation == "привет"


@pytest.mark.asyncio
async def test_get_cards_filtered_by_deck(
    client: AsyncClient,
    test_session_factory,
):
    """Проверяет фильтрацию карточек по идентификатору колоды."""

    # Создаём уникальные данные для теста.
    suffix = uuid4().hex[:8]

    async with test_session_factory() as session:
        # Создаём пользователя и два языка.
        user = User(
            email=f"card-filter-{suffix}@example.com",
            hashed_password="test-password-hash",
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        session.add(user)
        await session.flush()

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

        # Создаём две колоды одного пользователя.
        deck_a = Deck(
            name="Колода A",
            user_id=user.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        deck_b = Deck(
            name="Колода B",
            user_id=user.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        session.add_all([deck_a, deck_b])
        await session.flush()

        # Добавляем по одной карточке в каждую колоду.
        card_a = Card(
            word="hola",
            translation="привет",
            deck_id=deck_a.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        card_b = Card(
            word="adiós",
            translation="пока",
            deck_id=deck_b.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        session.add_all([card_a, card_b])
        await session.commit()

        # Сохраняем идентификаторы для запроса.
        user_id = user.id
        deck_a_id = deck_a.id

    # Подменяем авторизацию владельцем обеих колод.
    app.dependency_overrides[current_user] = (
        lambda: SimpleNamespace(id=user_id)
    )

    try:
        # Запрашиваем карточки только первой колоды.
        response = await client.get(
            "/cards/",
            params={"deck_ids": deck_a_id},
        )

        # Проверяем, что вернулась только карточка выбранной колоды.
        assert response.status_code == 200
        cards = response.json()
        assert len(cards) == 1
        assert cards[0]["word"] == "hola"
        assert cards[0]["deck_id"] == deck_a_id

    finally:
        # Убираем подмену авторизации после запроса.
        app.dependency_overrides.pop(current_user, None)


@pytest.mark.asyncio
async def test_user_sees_only_own_cards(
    client: AsyncClient,
    test_session_factory,
):
    """Проверяет, что пользователь получает только свои карточки."""

    # Создаём уникальные данные для теста.
    suffix = uuid4().hex[:8]

    async with test_session_factory() as session:
        # Создаём двух пользователей.
        user_a = User(
            email=f"card-visible-a-{suffix}@example.com",
            hashed_password="test-password-hash",
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        user_b = User(
            email=f"card-visible-b-{suffix}@example.com",
            hashed_password="test-password-hash",
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        session.add_all([user_a, user_b])
        await session.flush()

        # Создаём два языка.
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

        # Создаём отдельную колоду для каждого пользователя.
        deck_a = Deck(
            name="Колода пользователя A",
            user_id=user_a.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        deck_b = Deck(
            name="Колода пользователя B",
            user_id=user_b.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        session.add_all([deck_a, deck_b])
        await session.flush()

        # Создаём по одной карточке в каждой колоде.
        card_a = Card(
            word="hola",
            translation="привет",
            deck_id=deck_a.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        card_b = Card(
            word="adiós",
            translation="пока",
            deck_id=deck_b.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        session.add_all([card_a, card_b])
        await session.commit()

        # Сохраняем ID пользователя A для авторизации.
        user_a_id = user_a.id

    # Авторизуем запросы от имени пользователя A.
    app.dependency_overrides[current_user] = (
        lambda: SimpleNamespace(id=user_a_id)
    )

    try:
        # Получаем все карточки текущего пользователя.
        response = await client.get("/cards/")

        # Проверяем, что чужая карточка не попала в результат.
        assert response.status_code == 200
        cards = response.json()
        assert len(cards) == 1
        assert cards[0]["word"] == "hola"
        assert cards[0]["translation"] == "привет"

    finally:
        # Убираем подмену авторизации после запроса.
        app.dependency_overrides.pop(current_user, None)

