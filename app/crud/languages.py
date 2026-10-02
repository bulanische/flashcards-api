from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.language import Language
from app.models.user import User


async def get_all_languages(
    session: AsyncSession,
    user: User,
):
    # Получаем системные языки и языки текущего пользователя
    result = await session.execute(
        select(Language).where(
            or_(
                Language.user_id.is_(None),
                Language.user_id == user.id,
            )
        )
        .order_by(Language.name)
    )

    # Возвращаем список объектов Language
    return result.scalars().all()

async def create_language(
    session: AsyncSession,
    name: str,
    code: str,
    user: User,
):
    # Создаём новый объект языка
    language = Language(
        name=name,
        code=code,
        user_id=user.id,
    )

    # Добавляем язык в текущую транзакцию
    session.add(language)

    # Сохраняем изменения в базе данных
    await session.commit()

    # Обновляем объект данными из базы
    await session.refresh(language)

    return language