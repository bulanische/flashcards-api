from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import BaseCRUD
from app.models.deck import Deck
from app.models.user import User


deck_crud = BaseCRUD(Deck)


async def get_all_user_decks(
    session: AsyncSession,
    user: User,
) -> list[Deck]:
    """Возвращает колоды, принадлежащие текущему пользователю."""

    # Получаем только колоды текущего пользователя
    result = await session.execute(
        select(Deck).where(
            Deck.user_id == user.id
        )
    )

    # Возвращаем список найденных колод
    return list(result.scalars().all())


async def get_user_deck_by_deck_id(
    session: AsyncSession,
    deck_id: int,
    user: User,
) -> Deck | None:
    """Возвращает колоду текущего пользователя по ID."""

    # Ищем колоду только среди колод текущего пользователя
    result = await session.execute(
        select(Deck).where(
            Deck.id == deck_id,
            Deck.user_id == user.id,
        )
    )

    # Возвращаем найденную колоду или None
    return result.scalar_one_or_none()