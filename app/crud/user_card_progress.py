from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_card_progress import UserCardProgress


async def save_review_answer(
    session: AsyncSession,
    user_id: int,
    card_id: int,
    remembered: bool,
) -> UserCardProgress:
    """Сохраняет оценку пользователя по карточке."""

    # Ищем существующий прогресс для пользователя и карточки.
    result = await session.execute(
        select(UserCardProgress).where(
            UserCardProgress.user_id == user_id,
            UserCardProgress.card_id == card_id,
        )
    )
    progress = result.scalar_one_or_none()

    if progress is None:
        # Создаём запись при первой оценке карточки.
        progress = UserCardProgress(
            user_id=user_id,
            card_id=card_id,
            review_count=0,
        )
        session.add(progress)

    # Обновляем данные при каждой отправленной оценке.
    progress.review_count += 1
    progress.last_answer_correct = remembered
    progress.last_review_at = datetime.now()

    await session.commit()
    await session.refresh(progress)

    return progress
