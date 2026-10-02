from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CommonMixin


class Card(CommonMixin, Base):
    __tablename__ = "cards"

    # Слово или выражение на первом языке
    word: Mapped[str] = mapped_column()

    # Перевод на втором языке
    translation: Mapped[str] = mapped_column()

    # Первый язык карточки
    language_a_id: Mapped[int] = mapped_column(
        ForeignKey("languages.id")
    )

    # Второй язык карточки
    language_b_id: Mapped[int] = mapped_column(
        ForeignKey("languages.id")
    )

    # Первый язык карточки
    language_a: Mapped["Language"] = relationship(
        foreign_keys=[language_a_id]
    )

    # Второй язык карточки
    language_b: Mapped["Language"] = relationship(
        foreign_keys=[language_b_id]
    )

    # Связи между этой карточкой и колодами
    deck_cards: Mapped[list["DeckCard"]] = relationship(
        back_populates="card"
    )
