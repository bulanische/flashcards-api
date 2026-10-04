from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import current_user
from app.core.db import get_async_session
from app.crud.card import (
    create_card,
    get_all_user_cards,
    get_user_card_by_card_id,
    update_card,
)
from app.models.user import User
from app.schemas.card import (
    CardCreate,
    CardRead,
    CardUpdate,
)
from app.api.validators.card import (
    validate_card_deck,
    validate_match_card_deck_langs,
)


router = APIRouter()

SessionDependency = Annotated[
    AsyncSession,
    Depends(get_async_session),
]


@router.post("/")
async def create_new_card(
    card: CardCreate,
    session: SessionDependency,
    user: User = Depends(current_user),
):
    """Создаёт карточку в колоде текущего пользователя."""

    # Проверяем, принадлежит ли колода текущему пользователю
    try:
        deck = await validate_card_deck(
            session=session,
            deck_id=card.deck_id,
            user=user,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    try:
        validate_match_card_deck_langs(
            deck=deck,
            language_a_id=card.language_a_id,
            language_b_id=card.language_b_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    # Создаём карточку
    return await create_card(
        session=session,
        word=card.word,
        translation=card.translation,
        deck_id=card.deck_id,
        language_a_id=card.language_a_id,
        language_b_id=card.language_b_id,
    )

@router.get(
    "/",
    response_model=list[CardRead],
)
async def get_all_cards(
    session: SessionDependency,
    deck_ids: list[int] | None = Query(default=None),
    user: User = Depends(current_user),
):
    """Возвращает все карточки из колод текущего пользователя."""

    return await get_all_user_cards(
        session=session,
        user=user,
        deck_ids=deck_ids,
    )


@router.put("/{card_id}", response_model=CardRead)
async def update_existing_card(
    card_id: int,
    card: CardUpdate,
    session: SessionDependency,
    user: User = Depends(current_user),
):
    """Обновляет карточку текущего пользователя."""

    # Получаем существующую карточку текущего пользователя
    current_card = await get_user_card_by_card_id(
        session=session,
        card_id=card_id,
        user=user,
    )

    # Если карточка не найдена или недоступна пользователю
    if current_card is None:
        raise HTTPException(
            status_code=404,
            detail="Card not found or unavailable.",
        )

    # Проверяем, принадлежит ли новая колода текущему пользователю
    try:
        deck = await validate_card_deck(
            session=session,
            deck_id=card.deck_id,
            user=user,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    # Проверяем соответствие языков карточки языкам новой колоды
    try:
        validate_match_card_deck_langs(
            deck=deck,
            language_a_id=current_card.language_a_id,
            language_b_id=current_card.language_b_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    # Обновляем карточку и возвращаем её
    return await update_card(
        session=session,
        card=current_card,
        data=card.model_dump(),
    )


@router.delete("/{card_id}")
async def delete_card(
    card_id: int,
    session: SessionDependency,
    user: User = Depends(current_user),
):
    """Удаляет карточку текущего пользователя."""

    # Получаем карточку текущего пользователя
    card = await get_user_card_by_card_id(
        session=session,
        card_id=card_id,
        user=user,
    )

    # Если карточка не найдена или недоступна пользователю
    if card is None:
        raise HTTPException(
            status_code=404,
            detail="Card not found or unavailable.",
        )

    # Удаляем карточку из базы данных
    await session.delete(card)

    # Сохраняем изменения в базе данных
    await session.commit()

    return {"detail": "Card deleted successfully."}