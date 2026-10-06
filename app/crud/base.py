from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


ModelType = TypeVar("ModelType")


class BaseCRUD(Generic[ModelType]):
    """Базовый CRUD-класс с общими операциями для моделей."""

    def __init__(self, model: type[ModelType]):
        """Инициализирует CRUD для указанной модели."""

        # Сохраняем модель, с которой работает конкретный CRUD
        self.model = model

    async def create(
        self,
        session: AsyncSession,
        data: dict[str, Any],
    ) -> ModelType:
        """Создаёт новую запись в базе данных."""

        # Создаём объект переданной модели из словаря данных
        instance = self.model(**data)

        # Добавляем объект в текущую транзакцию
        session.add(instance)

        # Сохраняем изменения в базе данных
        await session.commit()

        # Получаем актуальные данные объекта из базы
        await session.refresh(instance)

        return instance

    async def get_by_id(
        self,
        session: AsyncSession,
        object_id: int,
    ) -> ModelType | None:
        """Возвращает объект по его идентификатору."""

        # Формируем запрос на поиск объекта по ID
        result = await session.execute(
            select(self.model).where(
                getattr(self.model, "id") == object_id
            )
        )

        # Возвращаем найденный объект или None
        return result.scalar_one_or_none()

    async def get_all(
        self,
        session: AsyncSession,
    ) -> list[ModelType]:
        """Возвращает все записи модели."""

        # Формируем запрос на получение всех записей
        result = await session.execute(
            select(self.model)
        )

        # Возвращаем список найденных объектов
        return list(result.scalars().all())

    async def update(
        self,
        session: AsyncSession,
        instance: ModelType,
        data: dict[str, Any],
    ) -> ModelType:
        """Обновляет существующую запись в базе данных."""

        # Обновляем переданные поля объекта
        for field, value in data.items():
            setattr(instance, field, value)

        # Сохраняем изменения в базе данных
        await session.commit()

        # Получаем актуальные данные объекта из базы
        await session.refresh(instance)

        return instance

    async def delete(
        self,
        session: AsyncSession,
        instance: ModelType,
    ) -> None:
        """Удаляет существующую запись из базы данных."""

        # Удаляем объект из текущей сессии
        await session.delete(instance)

        # Сохраняем изменения в базе данных
        await session.commit()
