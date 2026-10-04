from pydantic import BaseModel


class CardBase(BaseModel):
    """Базовая схема карточки."""

    # Слово или выражение
    word: str

    # Перевод
    translation: str

    # Колода, которой принадлежит карточка
    deck_id: int

    # Первый язык карточки
    language_a_id: int

    # Второй язык карточки
    language_b_id: int


class CardCreate(CardBase):
    """Схема для создания карточки."""

    pass


class CardRead(CardBase):
    """Схема для получения карточки."""

    # Уникальный идентификатор карточки
    id: int

class CardUpdate(BaseModel):
    """Схема для обновления карточки."""

    word: str
    translation: str
    deck_id: int
