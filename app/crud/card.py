from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import BaseCRUD
from app.models.card import Card
from app.models.user import User
from app.models.deck import Deck

card_crud = BaseCRUD(Card)


async def create_card(
    session: AsyncSession,
    word: str,
    translation: str,
    deck_id: int,
    language_a_id: int,
    language_b_id: int,
) -> Card:
    """Создаёт новую карточку."""

    # Передаём данные карточки в универсальный CRUD
    return await card_crud.create(
        session=session,
        data={
            "word": word,
            "translation": translation,
            "deck_id": deck_id,
            "language_a_id": language_a_id,
            "language_b_id": language_b_id,
        },
    )

async def get_all_user_cards(
    session: AsyncSession,
    user: User,
) -> list[Card]:
    """Возвращает все карточки из колод текущего пользователя."""

    # Получаем карточки только из колод текущего пользователя
    result = await session.execute(
        select(Card).where(
            Card.deck.has(
                Deck.user_id == user.id
            )
        )
    )

    # Возвращаем список найденных карточек
    return list(result.scalars().all())
