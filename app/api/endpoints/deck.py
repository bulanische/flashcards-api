from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import current_user
from app.core.db import get_async_session
from app.crud.deck import (
    deck_crud,
    get_all_user_decks,
    get_user_deck_by_deck_id,
    )
from app.models.user import User
from app.schemas.deck import (
    DeckCreate,
    DeckRead,
    DeckUpdate
)
from app.crud.language import get_available_language
from app.api.validators.deck import validate_unique_deck

router = APIRouter()

SessionDependency = Annotated[
    AsyncSession,
    Depends(get_async_session),
]


@router.get("/", response_model=list[DeckRead])
async def get_all_decks(
    session: SessionDependency,
    user: User = Depends(current_user),
):
    """Возвращает колоды текущего пользователя."""

    # Получаем все колоды текущего пользователя
    return await get_all_user_decks(
        session=session,
        user=user,
    )


@router.post("/", response_model=DeckRead)
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

    # Проверяем, что такая колода ещё не существует
    try:
        await validate_unique_deck(
            session=session,
            user=user,
            name=deck.name,
            language_a_id=deck.language_a_id,
            language_b_id=deck.language_b_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

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

@router.put("/{deck_id}", response_model=DeckRead)
async def update_deck(
    deck_id: int,
    deck: DeckUpdate,
    session: SessionDependency,
    user: User = Depends(current_user),
):
    """Обновляет название колоды текущего пользователя."""

    # Получаем колоду текущего пользователя
    current_deck = await get_user_deck_by_deck_id(
        session=session,
        deck_id=deck_id,
        user=user,
    )

    # Если колода не найдена или недоступна пользователю
    if current_deck is None:
        raise HTTPException(
            status_code=404,
            detail="Deck not found or unavailable.",
        )

    # Проверяем, что колода с таким названием ещё не существует
    try:
        await validate_unique_deck(
            session=session,
            user=user,
            name=deck.name,
            language_a_id=current_deck.language_a_id,
            language_b_id=current_deck.language_b_id,
            deck_id=deck_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    # Обновляем колоду через универсальный CRUD
    return await deck_crud.update(
        session=session,
        instance=current_deck,
        data=deck.model_dump(),
    )

@router.delete("/{deck_id}", status_code=204)
async def delete_deck(
    deck_id: int,
    session: SessionDependency,
    user: User = Depends(current_user),
):
    """Удаляет колоду текущего пользователя."""

    # Получаем колоду только среди колод текущего пользователя
    deck = await get_user_deck_by_deck_id(
        session=session,
        deck_id=deck_id,
        user=user,
    )

    # Если колода не найдена или недоступна пользователю
    if deck is None:
        raise HTTPException(
            status_code=404,
            detail="Deck not found or unavailable.",
        )

    # Удаляем колоду и связанные с ней карточки
    await deck_crud.delete(
        session=session,
        instance=deck,
    )
