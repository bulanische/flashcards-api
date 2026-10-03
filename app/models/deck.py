from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CommonMixin


class Deck(CommonMixin, Base):
    __tablename__ = "decks"

    # Название колоды
    name: Mapped[str] = mapped_column()

    # Пользователь, которому принадлежит колода
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    # ID первого языка колоды
    language_a_id: Mapped[int] = mapped_column(
        ForeignKey("languages.id")
    )

    # ID второго языка колоды
    language_b_id: Mapped[int] = mapped_column(
        ForeignKey("languages.id")
    )

    # Пользователь-владелец колоды
    user: Mapped["User"] = relationship(
        back_populates="decks"
    )

    # Первый язык колоды
    language_a: Mapped["Language"] = relationship(
        foreign_keys=[language_a_id],
        back_populates="language_a_decks",
    )

    # Второй язык колоды
    language_b: Mapped["Language"] = relationship(
        foreign_keys=[language_b_id],
        back_populates="language_b_decks",
    )

    # Карточки этой колоды
    cards: Mapped[list["Card"]] = relationship(
        back_populates="deck"
    )
