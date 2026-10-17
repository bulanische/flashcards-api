import random

from fastapi import APIRouter, Depends, HTTPException


from app.api.endpoints.card import SessionDependency
from app.auth.router import current_user
from app.crud.card import get_random_deck_cards
from app.crud.deck import get_user_deck_by_deck_id
from app.crud.card import get_user_card_by_card_id
from app.crud.user_card_progress import save_review_answer
from app.models.user import User
from app.schemas.review import ReviewCardRead, ReviewAnswerCreate


router = APIRouter()


@router.get(
    "/{deck_id}",
    response_model=list[ReviewCardRead],
)
async def get_deck_review(
    deck_id: int,
    session: SessionDependency,
    user: User = Depends(current_user),
) -> list[ReviewCardRead]:
    """Возвращает карточки колоды для повторения."""

    # Проверяем, что колода принадлежит пользователю
    deck = await get_user_deck_by_deck_id(
        session=session,
        deck_id=deck_id,
        user=user,
    )

    if deck is None:
        raise HTTPException(
            status_code=404,
            detail="Deck not found or unavailable.",
        )

    # Получаем карточки колоды в случайном порядке
    cards = await get_random_deck_cards(
        session=session,
        deck_id=deck_id,
    )

    # Случайно выбираем направление для каждой карточки
    review_cards = []

    for card in cards:
        if random.choice([True, False]):
            question = card.word
            answer = card.translation
            question_language_id = card.language_a_id
            answer_language_id = card.language_b_id
        else:
            question = card.translation
            answer = card.word
            question_language_id = card.language_b_id
            answer_language_id = card.language_a_id

        review_cards.append(
            ReviewCardRead(
                card_id=card.id,
                question=question,
                answer=answer,
                question_language_id=question_language_id,
                answer_language_id=answer_language_id,
            )
        )

    return review_cards

@router.post("/{card_id}/answer")
async def submit_review_answer(
    card_id: int,
    answer: ReviewAnswerCreate,
    session: SessionDependency,
    user: User = Depends(current_user),
) -> dict[str, str]:
    """Сохраняет оценку пользователя по карточке."""

    # Проверяем, что карточка принадлежит пользователю.
    card = await get_user_card_by_card_id(
        session=session,
        card_id=card_id,
        user=user,
    )

    if card is None:
        raise HTTPException(
            status_code=404,
            detail="Card not found or unavailable.",
        )

    # Сохраняем результат оценки.
    await save_review_answer(
        session=session,
        user_id=user.id,
        card_id=card_id,
        remembered=answer.remembered,
    )

    return {"detail": "Review answer saved."}