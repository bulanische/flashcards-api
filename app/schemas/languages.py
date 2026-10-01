from pydantic import BaseModel


class LanguageCreate(BaseModel):
    # Название языка
    name: str

    # Код языка, например ru, es, en
    code: str


class LanguageRead(BaseModel):
    # Уникальный идентификатор языка
    id: int

    # Название языка
    name: str

    # Код языка
    code: str
