import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_session import UserSession
from app.models.user import User


def create_refresh_token() -> str:
    """Создаёт криптографически случайный refresh-токен."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """Возвращает SHA-256-хеш refresh-токена."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def create_user_session(
    session: AsyncSession,
    user: User,
    refresh_token: str,
    lifetime_days: int = 7,
) -> UserSession:
    """Создаёт запись пользовательской refresh-сессии."""
    user_session = UserSession(
        user_id=user.id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=lifetime_days),
    )

    session.add(user_session)
    await session.flush()

    return user_session


async def get_active_user_session(
    session: AsyncSession,
    refresh_token: str,
) -> UserSession | None:
    """Находит действующую refresh-сессию по токену."""

    # Ищем в БД по хешу, не сохраняя открытый токен.
    token_hash = hash_refresh_token(refresh_token)

    # Учитываем только неотозванные и ещё не истёкшие сессии.
    result = await session.execute(
        select(UserSession).where(
            UserSession.token_hash == token_hash,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > datetime.now(timezone.utc),
        )
    )

    # Возвращаем найденную сессию или None, если она недействительна.
    return result.scalar_one_or_none()