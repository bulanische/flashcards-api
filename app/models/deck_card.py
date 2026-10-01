from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class DeckCard(Base):
    __tablename__ = "deck_cards"

    # Колода
    deck_id: Mapped[int] = mapped_column(
        ForeignKey("decks.id"),
        primary_key=True,
    )

    # Карточка
    card_id: Mapped[int] = mapped_column(
        ForeignKey("cards.id"),
        primary_key=True,
    )

    # Связанная колода
    deck: Mapped["Deck"] = relationship(
        back_populates="deck_cards"
    )

    # Связанная карточка
    card: Mapped["Card"] = relationship(
        back_populates="deck_cards"
    )