from datetime import datetime, timezone
import hashlib

from fastapi import (
    APIRouter, Cookie, Depends, HTTPException, Request, Response, status
)
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users import BaseUserManager
from fastapi_users.authentication import Strategy
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import auth_backend
from app.auth.manager import get_user_manager
from app.auth.sessions import get_active_user_session
from app.auth.manage_tokens import generate_refresh_token, set_refresh_cookie
from app.core.db import get_async_session
from app.models.user import User


router = APIRouter()



@router.post("/login")
async def login(
    request: Request,
    response: Response,
    credentials: OAuth2PasswordRequestForm = Depends(),
    user_manager: BaseUserManager[User, int] = Depends(get_user_manager),
    session: AsyncSession = Depends(get_async_session),
    strategy: Strategy[User, int] = Depends(auth_backend.get_strategy),
):
    """Выполняет вход и выдаёт access- и refresh-токены."""
    # Проверяем учётные данные через FastAPI Users.
    user = await user_manager.authenticate(credentials)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LOGIN_BAD_CREDENTIALS",
        )

    # Создаём access-токен и refresh-сессию.
    access_token = await strategy.write_token(user)
    refresh_token = await generate_refresh_token(session, user)
    await session.commit()

    # Передаём refresh-токен браузеру через HttpOnly cookie.
    set_refresh_cookie(response, refresh_token)

    await user_manager.on_after_login(user, request, response)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/refresh")
async def refresh_access_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_async_session),
    strategy: Strategy[User, int] = Depends(auth_backend.get_strategy),
):
    """Обновляет пару токенов по действующей refresh-сессии."""

    # Без refresh-cookie пользователь не может обновить токены.
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="REFRESH_TOKEN_MISSING",
        )

    # Ищем действующую сессию по хешу refresh-токена.
    user_session = await get_active_user_session(session, refresh_token)
    
    # Отклоняем отсутствующие, истёкшие и отозванные сессии.
    if user_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="REFRESH_TOKEN_INVALID",
        )

    # Находим владельца сессии.
    result = await session.execute(
        select(User).where(User.id == user_session.user_id)
    )
    user = result.scalar_one_or_none()

    # Не выдаём токены удалённому или неактивному пользователю.
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="USER_INACTIVE",
        )

    # Создаём новую refresh-сессию и новый access-токен.
    new_refresh_token = await generate_refresh_token(session, user)
    access_token = await strategy.write_token(user)

    # Отзываем прежнюю сессию, чтобы старый токен нельзя было периспользовать
    user_session.revoked_at = datetime.now(timezone.utc)

    # Сохраняем изменения и затем проверяем их в БД.
    await session.commit()
    await session.refresh(user_session)

    # Заменяем refresh-cookie новой.
    set_refresh_cookie(response, new_refresh_token)
    # Проверяем, сформирован ли заголовок Set-Cookie.

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
