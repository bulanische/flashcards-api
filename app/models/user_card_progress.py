from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CommonMixin


class UserCardProgress(CommonMixin, Base):
    __tablename__ = "user_card_progress"

    # Один пользователь может иметь только одну запись прогресса
    # по конкретной карточке
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "card_id",
            name="uq_user_card_progress",
        ),
    )

    # Пользователь, которому принадлежит прогресс
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    # Карточка, по которой хранится прогресс
    card_id: Mapped[int] = mapped_column(
        ForeignKey("cards.id")
    )

    # Сколько раз карточка уже была показана пользователю
    review_count: Mapped[int] = mapped_column(
        default=0
    )

    # Когда карточка последний раз повторялась
    last_review_at: Mapped[datetime | None] = mapped_column(
        nullable=True
    )

    # Когда карточку нужно показать снова
    next_review_at: Mapped[datetime | None] = mapped_column(
        nullable=True
    )

    # Связь с пользователем
    user: Mapped["User"] = relationship()

    # Связь с карточкой
    card: Mapped["Card"] = relationship()