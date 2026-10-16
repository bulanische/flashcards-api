import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


@pytest.mark.asyncio
async def test_database_connection(test_engine: AsyncEngine):
    """Проверяет подключение к тестовой базе данных."""

    # Получаем имя базы данных, к которой подключён engine.
    async with test_engine.connect() as connection:
        result = await connection.execute(
            text("SELECT current_database()")
        )

    # Проверяем, что тесты работают с отдельной базой.
    assert result.scalar_one() == "cards_test"