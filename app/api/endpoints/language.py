from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import current_user
from app.core.db import get_async_session
from app.crud.language import (
    get_all_languages,
    create_language,
    language_crud,
)
from app.models.user import User
from app.schemas.language import LanguageCreate, LanguageRead
from app.api.validators.language import validate_language_not_in_use

router = APIRouter()

SessionDependency = Annotated[
    AsyncSession,
    Depends(get_async_session),
]


@router.get("/", response_model=list[LanguageRead])
async def get_languages(
    session: SessionDependency,
    user: User = Depends(current_user),
):
    """Возвращает языки, доступные текущему пользователю."""

    # Получаем все языки через CRUD-слой
    return await get_all_languages(
        session=session,
        user=user,
    )

@router.post("/", response_model=LanguageRead)
async def create_new_language(
    session: SessionDependency,
    language: LanguageCreate,
    user: User = Depends(current_user),
):
    """Создаёт пользовательский язык для текущего пользователя."""

    # Создаём язык для текущего пользователя
    return await create_language(
        session=session,
        name=language.name,
        native_name=language.native_name,
        code=language.code,
        user=user,
    )

@router.delete("/{language_id}", status_code=204)
async def delete_language(
    language_id: int,
    session: SessionDependency,
    user: User = Depends(current_user),
) -> None:
    """Удаляет пользовательский язык текущего пользователя."""

    # Получаем язык по ID
    language = await language_crud.get_by_id(
        session=session,
        object_id=language_id,
    )

    # Если язык не найден
    if language is None:
        raise HTTPException(
            status_code=404,
            detail="Language not found.",
        )

    # Системные языки принадлежат системе и не могут быть удалены
    if language.user_id is None:
        raise HTTPException(
            status_code=403,
            detail="System languages cannot be deleted.",
        )

    # Пользователь может удалить только собственный язык
    if language.user_id != user.id:
        raise HTTPException(
            status_code=404,
            detail="Language not found.",
        )

    # Проверяем, что язык не используется в колодах или карточках
    try:
        await validate_language_not_in_use(
            session=session,
            language_id=language_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    # Удаляем язык через универсальный CRUD
    await language_crud.delete(
        session=session,
        instance=language,
    )
