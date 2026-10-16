from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.models.deck import Deck
from app.models.language import Language
from app.models.user import User
from app.models.card import Card


async def create_test_user(session, prefix: str = "user") -> User:
    """Создаёт пользователя с уникальным email для теста."""

    user = User(
        email=f"{prefix}-{uuid4().hex[:8]}@example.com",
        hashed_password="test-password-hash",
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )
    session.add(user)
    await session.flush()
    return user


async def create_test_language(
    session,
    user_id: int | None,
    name: str = "Test language",
    native_name: str = "Test",
) -> Language:
    """Создаёт язык с уникальным кодом для теста."""

    language = Language(
        name=name,
        native_name=native_name,
        code=f"test-{uuid4().hex[:8]}",
        user_id=user_id,
    )
    session.add(language)
    await session.flush()
    return language


@pytest.mark.asyncio
async def test_delete_language_rejects_language_used_in_deck(
    client: AsyncClient,
    test_session_factory,
    override_current_user,
):
    """Проверяет запрет удаления языка, используемого в колоде."""

    async with test_session_factory() as session:
        user = await create_test_user(session)
        language_a = await create_test_language(
            session, user.id, "Russian", "Русский"
        )
        language_b = await create_test_language(
            session, user.id, "Spanish", "Español"
        )
        deck = Deck(
            name="Русский — Испанский",
            user_id=user.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        session.add(deck)
        await session.commit()
        user_id = user.id
        language_id = language_a.id

    override_current_user(user_id)
    response = await client.delete(f"/languages/{language_id}")

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Language is used in one or more decks."
    )


@pytest.mark.asyncio
async def test_delete_system_language_returns_forbidden(
    client: AsyncClient,
    test_session_factory,
    override_current_user,
):
    """Проверяет запрет удаления системного языка."""

    async with test_session_factory() as session:
        language = await create_test_language(session, user_id=None)
        await session.commit()
        language_id = language.id

    override_current_user(12345)
    response = await client.delete(f"/languages/{language_id}")

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "System languages cannot be deleted."
    )


@pytest.mark.asyncio
async def test_user_cannot_delete_another_users_language(
    client: AsyncClient,
    test_session_factory,
    override_current_user,
):
    """Проверяет запрет удаления чужого языка."""

    async with test_session_factory() as session:
        current_user_record = await create_test_user(
            session, "current"
        )
        owner = await create_test_user(session, "owner")
        language = await create_test_language(
            session, owner.id, "Foreign language", "Foreign"
        )
        await session.commit()
        current_user_id = current_user_record.id
        language_id = language.id

    override_current_user(current_user_id)
    response = await client.delete(f"/languages/{language_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Language not found."


@pytest.mark.asyncio
async def test_user_can_delete_own_unused_language(
    client: AsyncClient,
    test_session_factory,
    override_current_user,
):
    """Проверяет успешное удаление собственного языка."""

    async with test_session_factory() as session:
        user = await create_test_user(session)
        language = await create_test_language(session, user.id)
        await session.commit()
        user_id = user.id
        language_id = language.id

    override_current_user(user_id)
    response = await client.delete(f"/languages/{language_id}")

    assert response.status_code == 204

    async with test_session_factory() as session:
        deleted_language = await session.get(Language, language_id)
        assert deleted_language is None


@pytest.mark.asyncio
async def test_delete_nonexistent_language_returns_not_found(
    client: AsyncClient,
    override_current_user,
):
    """Проверяет ответ при удалении несуществующего языка."""

    override_current_user(12345)
    response = await client.delete("/languages/999999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Language not found."


@pytest.mark.asyncio
async def test_create_language_success(
    client: AsyncClient,
    test_session_factory,
    override_current_user,
):
    """Проверяет успешное создание пользовательского языка."""

    async with test_session_factory() as session:
        user = await create_test_user(session)
        await session.commit()
        user_id = user.id

    override_current_user(user_id)
    payload = {
        "name": "Spanish",
        "native_name": "Español",
        "code": f"es-{uuid4().hex[:8]}",
    }
    response = await client.post("/languages/", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["native_name"] == payload["native_name"]
    assert data["code"] == payload["code"]
    assert data["id"] is not None

    async with test_session_factory() as session:
        language = await session.get(Language, data["id"])
        assert language is not None
        assert language.user_id == user_id


@pytest.mark.asyncio
async def test_get_languages_returns_system_and_own_languages(
    client: AsyncClient,
    test_session_factory,
    override_current_user,
):
    """Проверяет доступность системных и собственных языков."""

    async with test_session_factory() as session:
        user = await create_test_user(session)
        another_user = await create_test_user(session, "another")

        system_language = await create_test_language(
            session, None, "English", "English"
        )
        own_language = await create_test_language(
            session, user.id, "Spanish", "Español"
        )
        foreign_language = await create_test_language(
            session, another_user.id, "French", "Français"
        )
        await session.commit()

        user_id = user.id
        expected_codes = {
            system_language.code,
            own_language.code,
        }
        foreign_code = foreign_language.code

    override_current_user(user_id)
    response = await client.get("/languages/")

    assert response.status_code == 200
    returned_codes = {
        language["code"] for language in response.json()
    }
    assert expected_codes <= returned_codes
    assert foreign_code not in returned_codes

@pytest.mark.asyncio
async def test_delete_language_rejects_language_used_in_card(
    client: AsyncClient,
    test_session_factory,
    override_current_user,
):
    """Проверяет запрет удаления языка, используемого в карточке."""

    async with test_session_factory() as session:
        user = await create_test_user(session)
        language_a = await create_test_language(
            session, user.id, "Russian", "Русский"
        )
        language_b = await create_test_language(
            session, user.id, "Spanish", "Español"
        )

        # Создаём колоду с другими языками, чтобы проверить именно карточку.
        other_language_a = await create_test_language(
            session, user.id, "English", "English"
        )
        other_language_b = await create_test_language(
            session, user.id, "French", "Français"
        )
        deck = Deck(
            name="English — French",
            user_id=user.id,
            language_a_id=other_language_a.id,
            language_b_id=other_language_b.id,
        )
        session.add(deck)
        await session.flush()

        # Связываем карточку с проверяемым языком, не используя его в колоде.
        card = Card(
            word="hola",
            translation="привет",
            deck_id=deck.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        session.add(card)
        await session.commit()

        user_id = user.id
        language_id = language_a.id

    override_current_user(user_id)
    response = await client.delete(f"/languages/{language_id}")

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Language is used in one or more cards."
    )