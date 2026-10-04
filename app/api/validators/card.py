from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.deck import get_user_deck_by_deck_id

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


