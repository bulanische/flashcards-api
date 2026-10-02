from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import current_user
from app.core.db import get_async_session
from app.crud.language import (
    get_all_languages,
    create_language,
)
from app.models.user import User
from app.schemas.language import LanguageCreate

router = APIRouter()

SessionDependency = Annotated[
    AsyncSession,
    Depends(get_async_session),
]


@router.get("/")
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


@router.post("/")
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
