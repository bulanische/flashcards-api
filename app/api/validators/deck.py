from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deck import Deck
from app.models.user import User


async def validate_unique_deck(
    session: AsyncSession,
    user: User,
    name: str,
    language_a_id: int,
    language_b_id: int,
    deck_id: int | None = None,
) -> None:
    """Проверяет, что у пользователя нет дублирующейся колоды."""

    # Формируем базовый запрос на поиск колоды текущего пользователя
    query = select(Deck).where(
        Deck.user_id == user.id,
        Deck.name == name,
    )

    # Проверяем совпадение языков независимо от их порядка
    query = query.where(
        (
            (Deck.language_a_id == language_a_id)
            & (Deck.language_b_id == language_b_id)
        )
        |
        (
            (Deck.language_a_id == language_b_id)
            & (Deck.language_b_id == language_a_id)
        )
    )

    # При обновлении исключаем из поиска саму редактируемую колоду
    if deck_id is not None:
        query = query.where(
            Deck.id != deck_id,
        )

    # Выполняем запрос
    result = await session.execute(query)

    # Получаем первую найденную колоду или None
    existing_deck = result.scalars().first()

    # Если такая колода уже существует, сообщаем о дубликате
    if existing_deck is not None:
        raise ValueError(
            "A deck with the same name and languages already exists."
        )
