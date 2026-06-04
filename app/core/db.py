from datetime import datetime

from sqlalchemy import Integer, Boolean, DateTime
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    declared_attr,
    mapped_column,
    Mapped,
)
from sqlalchemy.sql import func

from app.core.config import settings


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""


class CommonMixin:
    """Миксин для общих полей моделей."""

    @declared_attr
    def __tablename__(cls) -> str:  # noqa: N805
        return cls.__name__.lower()

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )




engine = create_async_engine(settings.database_url)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session():
    async with AsyncSessionLocal() as async_session:
        yield async_session
