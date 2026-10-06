from pydantic import BaseModel


class LanguageBase(BaseModel):
    """Базовая схема языка."""

    # Название языка
    name: str

    # Название языка на самом языке
    native_name: str | None = None

    # Код языка, например ru, es, en
    code: str


class LanguageCreate(LanguageBase):
    """Схема для создания языка."""

    pass


class LanguageRead(LanguageBase):
    """Схема для получения языка."""

    # Уникальный идентификатор языка
    id: int
