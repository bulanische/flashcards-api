from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CommonMixin


class Language(CommonMixin, Base):
    __tablename__ = "languages"

        # Код языка должен быть уникальным среди всех языков
    __table_args__ = (
        Index(
            "uq_language_code",
            "code",
            unique=True,
        ),
    )

    # Название языка: "Русский", "Испанский", "English"
    name: Mapped[str] = mapped_column()

    # Название языка на самом языке: "Русский", "Español", "Deutsch"
    native_name: Mapped[str | None] = mapped_column(
        nullable=True,
    )

    # Код языка: "ru", "es", "en"
    code: Mapped[str] = mapped_column()

    # Колоды, где язык указан первым
    language_a_decks: Mapped[list["Deck"]] = relationship(
        foreign_keys="Deck.language_a_id",
        back_populates="language_a",
    )

    # Колоды, где язык указан вторым
    language_b_decks: Mapped[list["Deck"]] = relationship(
        foreign_keys="Deck.language_b_id",
        back_populates="language_b",
    )

    # Пользователи, для которых этот язык является родным
    native_language_users: Mapped[list["User"]] = relationship(
        foreign_keys="User.native_language_id",
        back_populates="native_language",
    )

    # Пользователи, которые изучают этот язык
    learning_language_users: Mapped[list["User"]] = relationship(
        foreign_keys="User.learning_language_id",
        back_populates="learning_language",
    )

    # Пользователь-владелец языка
    # NULL означает, что язык является системным
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    # Пользователь, создавший язык
    user: Mapped["User | None"] = relationship(
        foreign_keys=[user_id],
        back_populates="created_languages",
    )

