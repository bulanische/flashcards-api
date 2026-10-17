from pydantic import BaseModel


class ReviewCardRead(BaseModel):
    """Схема карточки, подготовленной для повторения."""

    # ID исходной карточки
    card_id: int

    # Текст, который увидит пользователь
    question: str

    # Правильный ответ
    answer: str

    # Язык вопроса
    question_language_id: int

    # Язык ответа
    answer_language_id: int


class ReviewAnswerCreate(BaseModel):
    """Схема оценки карточки пользователем."""

    remembered: bool
