from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.deck import get_user_deck_by_deck_id

from app.models.card import Card
from app.models.deck import Deck
from app.models.user import User

async def validate_card_deck(
    session: AsyncSession,
    deck_id: int,
    user: User,
) -> Deck:
    """Проверяет, доступна ли колода пользователю."""

    # Получаем колоду только среди колод текущего пользователя
    deck = await get_user_deck_by_deck_id(
        session=session,
        deck_id=deck_id,
        user=user,
    )

    # Если колода недоступна, вызывающий код получит ошибку
    if deck is None:
        raise ValueError("Deck not found or unavailable.")

    return deck

def validate_match_card_deck_langs(
    deck: Deck,
    language_a_id: int,
    language_b_id: int,
) -> None:
    """Проверяет соответствие языков карточки языкам колоды."""

    # Получаем языки, которые разрешены в колоде
    deck_languages = {
        deck.language_a_id,
        deck.language_b_id,
    }

    # Получаем языки, указанные в карточке
    card_languages = {
        language_a_id,
        language_b_id,
    }

    # Проверяем, что карточка использует оба языка колоды
    if card_languages != deck_languages:
        raise ValueError(
            "Card languages do not match the deck languages."
        )


async def validate_unique_card(
    session: AsyncSession,
    user: User,
    deck_id: int,
    word: str,
    translation: str,
    language_a_id: int,
    language_b_id: int,
    card_id: int | None = None,
) -> None:
    """Проверяет, что в колоде нет дублирующейся карточки."""

    # Ищем карточки только в колодах текущего пользователя
    query = select(Card).where(
        Card.deck_id == deck_id,
        Card.word == word,
        Card.translation == translation,
        Card.deck.has(
            Deck.user_id == user.id,
        ),
    )

    # Проверяем совпадение языков независимо от их порядка
    query = query.where(
        (
            (Card.language_a_id == language_a_id)
            & (Card.language_b_id == language_b_id)
        )
        |
        (
            (Card.language_a_id == language_b_id)
            & (Card.language_b_id == language_a_id)
        )
    )

    # При обновлении исключаем саму редактируемую карточку
    if card_id is not None:
        query = query.where(
            Card.id != card_id,
        )

    # Выполняем запрос
    result = await session.execute(query)

    # Получаем первую найденную карточку или None
    existing_card = result.scalars().first()

    # Если такая карточка уже существует, сообщаем о дубликате
    if existing_card is not None:
        raise ValueError(
            "A card with the same content already exists in this deck."
        )