from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.auth.sessions import create_refresh_token, create_user_session
from app.models.user import User

# Переводим срок действия refresh-сессии из дней в секунды.
REFRESH_COOKIE_MAX_AGE = settings.refresh_token_lifetime_days * 24 * 60 * 60


async def generate_refresh_token(
    session: AsyncSession,
    user: User,
) -> str:
    """Создаёт refresh-токен и сохраняет его сессию в БД."""

    # Генерируем секретный токен; в БД сохраняется только его хеш.
    refresh_token = create_refresh_token()

    await create_user_session(
        session=session,
        user=user,
        refresh_token=refresh_token,
        lifetime_days=settings.refresh_token_lifetime_days,
    )
    return refresh_token


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Устанавливает refresh-токен в защищённую cookie."""

    # HttpOnly запрещает доступ к cookie из JavaScript.
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=REFRESH_COOKIE_MAX_AGE,
        path="/auth",
    )
