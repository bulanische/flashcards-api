from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import current_user
from app.core.db import get_async_session
from app.crud.card import (
    create_card,
    get_all_user_cards
)
from app.models.user import User
from app.schemas.card import (
    CardCreate,
    CardRead
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
    user: User = Depends(current_user),
):
    """Возвращает все карточки из колод текущего пользователя."""

    return await get_all_user_cards(
        session=session,
        user=user,
    )
