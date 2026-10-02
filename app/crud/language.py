from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import BaseCRUD
from app.models.language import Language
from app.models.user import User

language_crud = BaseCRUD(Language)


async def get_all_languages(
    session: AsyncSession,
    user: User,
) -> list[Language]:
    """Возвращает системные языки + языки текущего пользователя."""

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
    return list(result.scalars().all())


async def create_language(
    session: AsyncSession,
    name: str,
    native_name: str | None,
    code: str,
    user: User,
)-> Language:
    """Создаёт пользовательский язык для текущего пользователя."""

    # Передаём данные языка в универсальный CRUD
    return await language_crud.create(
        session=session,
        data={
            "name": name,
            "native_name": native_name,
            "code": code,
            "user_id": user.id,
        },
    )


async def get_available_language(
    session: AsyncSession,
    language_id: int,
    user: User,
) -> Language | None:
    """Возвращает доступный пользователю язык по его ID."""

    # Ищем системный язык или язык текущего пользователя
    result = await session.execute(
        select(Language).where(
            Language.id == language_id,
            or_(
                Language.user_id.is_(None),
                Language.user_id == user.id,
            ),
        )
    )

    # Возвращаем найденный язык или None
    return result.scalar_one_or_none()
