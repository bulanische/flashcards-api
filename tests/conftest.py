from httpx import ASGITransport, AsyncClient
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from app.auth.router import current_user
from app.core.config import settings
from app.core.db import Base, get_async_session
from app.main import app
from app.models import Card, Deck, Language, User, UserCardProgress


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """Возвращает URL отдельной тестовой базы данных."""

    # Подключаемся к cards_test вместо рабочей cards.
    return settings.database_url.rsplit("/", 1)[0] + "/cards_test"


@pytest_asyncio.fixture(scope="function", loop_scope="function")
async def test_engine(test_database_url):
    """Создаёт engine и таблицы для одного теста."""

    # Создаём отдельный engine для текущего цикла событий.
    engine = create_async_engine(test_database_url)

    # Создаём таблицы на основе зарегистрированных моделей.
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield engine

    # Закрываем соединения до завершения цикла событий.
    await engine.dispose()


@pytest_asyncio.fixture(scope="function", loop_scope="function")
async def test_session_factory(test_engine):
    """Создаёт фабрику сессий для текущего теста."""

    # Все сессии используют engine этого теста.
    return async_sessionmaker(
        test_engine,
        expire_on_commit=False,
    )

@pytest_asyncio.fixture(scope="function", loop_scope="function")
async def client(test_session_factory):
    """Создаёт HTTP-клиент FastAPI с тестовой базой данных."""

    # Подменяем зависимость БД для запросов внутри теста.
    async def override_get_async_session():
        """Возвращает сессию из тестовой базы данных."""

        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_async_session] = (
        override_get_async_session
    )

    # Отправляем запросы напрямую в приложение без запуска сервера.
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as test_client:
        yield test_client

    # Убираем подмену, чтобы она не влияла на другие тесты.
    app.dependency_overrides.pop(get_async_session, None)

@pytest.fixture
def override_current_user():
    """Подменяет авторизацию и очищает её после теста."""

    def set_user(user_id: int) -> None:
        """Устанавливает пользователя для тестовых запросов."""
        app.dependency_overrides[current_user] = (
            lambda: SimpleNamespace(id=user_id)
        )

    yield set_user

    # Удаляем подмену после завершения теста.
    app.dependency_overrides.pop(current_user, None)