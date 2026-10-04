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
    deck_ids: list[int] | None = None,
) -> list[Card]:
    """Возвращает все карточки из колод текущего пользователя."""

    # Получаем карточки только из колод текущего пользователя
    query = select(Card).where(
        Card.deck.has(
            Deck.user_id == user.id
        )
    )

    # Если указаны конкретные колоды, ограничиваем выборку ими
    if deck_ids:
        query = query.where(
            Card.deck_id.in_(deck_ids)
        )

    result = await session.execute(query)

    # Возвращаем список найденных карточек
    return list(result.scalars().all())

async def get_user_card_by_card_id(
    session: AsyncSession,
    card_id: int,
    user: User,
) -> Card | None:
    """Возвращает карточку текущего пользователя по ID."""

    # Ищем карточку только в колодах текущего пользователя
    result = await session.execute(
        select(Card).where(
            Card.id == card_id,
            Card.deck.has(
                Deck.user_id == user.id
            ),
        )
    )

    # Возвращаем найденную карточку или None
    return result.scalar_one_or_none()

async def update_card(
    session: AsyncSession,
    card: Card,
    data: dict,
) -> Card:
    """Обновляет данные карточки."""

    for field, value in data.items():
        setattr(card, field, value)

    # Сохраняем изменения в базе данных
    await session.commit()

    # Обновляем объект данными из базы
    await session.refresh(card)

    return card
