from pydantic import BaseModel


class DeckBase(BaseModel):
    """Базовая схема колоды."""

    # Название колоды
    name: str

    # Первый язык колоды
    language_a_id: int

    # Второй язык колоды
    language_b_id: int


class DeckCreate(DeckBase):
    """Схема для создания колоды."""

    pass


class DeckRead(DeckBase):
    """Схема для получения колоды."""

    # Уникальный идентификатор колоды
    id: int

    # Пользователь-владелец колоды
    user_id: int