from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CommonMixin


class Card(CommonMixin, Base):
    __tablename__ = "cards"

    # Полная комбинация карточки должна быть уникальной
    __table_args__ = (
        UniqueConstraint(
            "deck_id",
            "word",
            "translation",
            "language_a_id",
            "language_b_id",
            name="uq_card_content",
        ),
    )

    # Слово или выражение на первом языке
    word: Mapped[str] = mapped_column()

    # Перевод на втором языке
    translation: Mapped[str] = mapped_column()

    # ID колоды, которой принадлежит карточка
    deck_id: Mapped[int] = mapped_column(
        ForeignKey(
            "decks.id",
            ondelete="CASCADE",
        ),
    )

    # Первый язык карточки
    language_a_id: Mapped[int] = mapped_column(
        ForeignKey("languages.id")
    )

    # Второй язык карточки
    language_b_id: Mapped[int] = mapped_column(
        ForeignKey("languages.id")
    )

    # Колода, которой принадлежит карточка
    deck: Mapped["Deck"] = relationship(
        back_populates="cards"
    )

    # Первый язык карточки
    language_a: Mapped["Language"] = relationship(
        foreign_keys=[language_a_id]
    )

    # Второй язык карточки
    language_b: Mapped["Language"] = relationship(
        foreign_keys=[language_b_id]
    )


