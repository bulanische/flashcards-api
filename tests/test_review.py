from uuid import uuid4
from sqlalchemy import select
import pytest

from app.models.card import Card
from app.models.deck import Deck
from app.models.language import Language
from app.models.user import User
from app.models.user_card_progress import UserCardProgress


async def create_review_deck(test_session_factory, card_count=0):
    """Создаёт тестовую колоду с заданным количеством карточек."""

    suffix = uuid4().hex[:8]

    async with test_session_factory() as session:
        # Создаём пользователя-владельца.
        user = User(
            email=f"review-{suffix}@example.com",
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

        # Создаём колоду владельца.
        deck = Deck(
            name="Колода для повторения",
            user_id=user.id,
            language_a_id=language_a.id,
            language_b_id=language_b.id,
        )
        session.add(deck)
        await session.flush()

        # Добавляем карточки, если они нужны тесту.
        cards = [
            Card(
                word=f"слово-{index}-{suffix}",
                translation=f"palabra-{index}-{suffix}",
                deck_id=deck.id,
                language_a_id=language_a.id,
                language_b_id=language_b.id,
            )
            for index in range(card_count)
        ]
        session.add_all(cards)
        await session.commit()

        return user.id, deck.id, [
            {
                "id": card.id,
                "word": card.word,
                "translation": card.translation,
                "language_a_id": card.language_a_id,
                "language_b_id": card.language_b_id,
            }
            for card in cards
        ]


@pytest.mark.asyncio
async def test_get_deck_review_returns_all_cards(
    client,
    test_session_factory,
    override_current_user,
):
    """Проверяет выдачу всех карточек с допустимым направлением перевода."""

    user_id, deck_id, cards = await create_review_deck(
        test_session_factory,
        card_count=3,
    )
    override_current_user(user_id)

    response = await client.get(f"/review/{deck_id}")
    print(response.status_code, response.json())
    assert response.status_code == 200

    review_cards = response.json()

    # Проверяем, что все карточки возвращены ровно по одному разу.
    assert {card["card_id"] for card in review_cards} == {
        card["id"] for card in cards
    }
    assert len(review_cards) == len(cards)

    # Проверяем оба допустимых направления перевода для каждой карточки.
    cards_by_id = {card["id"]: card for card in cards}

    for review_card in review_cards:
        original = cards_by_id[review_card["card_id"]]

        forward = (
            review_card["question"] == original["word"]
            and review_card["answer"] == original["translation"]
            and review_card["question_language_id"]
            == original["language_a_id"]
            and review_card["answer_language_id"]
            == original["language_b_id"]
        )
        reverse = (
            review_card["question"] == original["translation"]
            and review_card["answer"] == original["word"]
            and review_card["question_language_id"]
            == original["language_b_id"]
            and review_card["answer_language_id"]
            == original["language_a_id"]
        )
        assert forward or reverse


@pytest.mark.asyncio
async def test_user_cannot_review_another_users_deck(
    client,
    test_session_factory,
    override_current_user,
):
    """Проверяет запрет повторения чужой колоды."""

    _, deck_id, _ = await create_review_deck(test_session_factory)

    # Используем ID, не принадлежащий владельцу колоды.
    override_current_user(-1)

    response = await client.get(f"/review/{deck_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_review_for_empty_deck(
    client,
    test_session_factory,
    override_current_user,
):
    """Проверяет, что пустая колода возвращает пустой список."""

    user_id, deck_id, _ = await create_review_deck(test_session_factory)
    override_current_user(user_id)

    response = await client.get(f"/review/{deck_id}")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_submit_review_answer_creates_progress(
    client,
    test_session_factory,
    override_current_user,
):
    """Проверяет создание прогресса при первой оценке карточки."""

    user_id, _, cards = await create_review_deck(
        test_session_factory,
        card_count=1,
    )
    override_current_user(user_id)
    card_id = cards[0]["id"]

    response = await client.post(
        f"/review/{card_id}/answer",
        json={"remembered": True},
    )

    assert response.status_code == 200

    # Проверяем, что оценка сохранена в базе данных.
    async with test_session_factory() as session:
        result = await session.execute(
            select(UserCardProgress).where(
                UserCardProgress.user_id == user_id,
                UserCardProgress.card_id == card_id,
            )
        )
        progress = result.scalar_one()

        assert progress.review_count == 1
        assert progress.last_answer_correct is True
        assert progress.last_review_at is not None
