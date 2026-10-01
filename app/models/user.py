from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from sqlalchemy import ForeignKey, Integer 
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "users"

    # Уникальный идентификатор пользователя
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # Все колоды, принадлежащие пользователю
    decks: Mapped[list["Deck"]] = relationship(
        back_populates="user"
    )

    # Родной язык пользователя
    native_language_id: Mapped[int | None] = mapped_column(
        ForeignKey("languages.id"),
        nullable=True,
    )

    # Изучаемый язык пользователя
    learning_language_id: Mapped[int | None] = mapped_column(
        ForeignKey("languages.id"),
        nullable=True,
    )

    # Родной язык пользователя
    native_language: Mapped["Language | None"] = relationship(
        foreign_keys=[native_language_id],
        back_populates="native_language_users",
    )

    # Изучаемый язык пользователя
    learning_language: Mapped["Language | None"] = relationship(
        foreign_keys=[learning_language_id],
        back_populates="learning_language_users",
    )

    # Языки, созданные этим пользователем
    created_languages: Mapped[list["Language"]] = relationship(
        foreign_keys="Language.user_id",
        back_populates="user",
    )
