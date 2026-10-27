from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, CommonMixin


class UserSession(CommonMixin, Base):
    """Хранит данные активного сеанса пользователя."""

    __tablename__ = "user_sessions"

    # Пользователь, которому принадлежит сеанс.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Хеш refresh-токена, используемый для поиска сеанса.
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )

    # Срок действия refresh-токена.
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Время отзыва сеанса; NULL означает, что он не отозван.
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
