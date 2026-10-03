from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import current_user
from app.core.db import get_async_session
from app.crud.deck import deck_crud, get_user_deck_by_deck_id
from app.models.user import User
from app.schemas.deck import DeckCreate
from app.crud.language import get_available_language

router = APIRouter()

SessionDependency = Annotated[
    AsyncSession,
    Depends(get_async_session),
]


@router.get("/")
async def get_all_decks(
    session: SessionDependency,
    user: User = Depends(current_user),
):
    """Возвращает колоды текущего пользователя."""

    # Получаем колоды текущего пользователя
    return await get_user_deck_by_deck_id(
        session=session,
        user=user,
    )


@router.post("/")
async def create_deck(
    deck: DeckCreate,
    session: SessionDependency,
    user: User = Depends(current_user),
):
    """Создаёт колоду для текущего пользователя."""

    # Проверяем доступность первого языка для текущего пользователя
    language_a = await get_available_language(
        session=session,
        language_id=deck.language_a_id,
        user=user,
    )
    if language_a is None:
        raise HTTPException(
            status_code=404,
            detail="Language not found or unavailable."
        )
    # Проверяем доступность второго языка для текущего пользователя
    language_b = await get_available_language(
        session=session,
        language_id=deck.language_b_id,
        user=user,
    )

    # Проверяем, что второй язык доступен пользователю
    if language_b is None:
        raise HTTPException(
            status_code=404,
            detail="Language not found or unavailable.",
        )

    # Создаём колоду через универсальный CRUD
    return await deck_crud.create(
        session=session,
        data={
            "name": deck.name,
            "language_a_id": deck.language_a_id,
            "language_b_id": deck.language_b_id,
            "user_id": user.id,
        },
    )

