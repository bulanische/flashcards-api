from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card
from app.models.deck import Deck


async def validate_language_not_in_use(
    session: AsyncSession,
    language_id: int,
) -> None:
    """Проверяет, что язык не используется в колодах или карточках."""

    # Ищем колоды, в которых указанный язык является одним из двух языков
    deck_query = select(Deck.id).where(
        or_(
            Deck.language_a_id == language_id,
            Deck.language_b_id == language_id,
        )
    )

    # Выполняем запрос по колодам
    deck_result = await session.execute(deck_query)

    # Получаем первую найденную колоду или None
    existing_deck = deck_result.scalars().first()

    # Если язык используется хотя бы в одной колоде
    if existing_deck is not None:
        raise ValueError(
            "Language is used in one or more decks."
        )

    # Ищем карточки, в которых указанный язык является одним из двух языков
    card_query = select(Card.id).where(
        or_(
            Card.language_a_id == language_id,
            Card.language_b_id == language_id,
        )
    )

    # Выполняем запрос по карточкам
    card_result = await session.execute(card_query)

    # Получаем первую найденную карточку или None
    existing_card = card_result.scalars().first()

    # Если язык используется хотя бы в одной карточке
    if existing_card is not None:
        raise ValueError(
            "Language is used in one or more cards."
        )
