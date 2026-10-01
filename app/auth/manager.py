from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi_users import BaseUserManager
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from app.auth.database import get_user_db
from app.models.user import User


class UserManager(BaseUserManager[User, int]):
    """Менеджер пользователей."""

    # Преобразуем ID пользователя из JWT в целое число
    def parse_id(self, value: str) -> int:
        return int(value)

    async def on_after_register(
        self,
        user: User,
        request=None,
    ):
        # Выводим сообщение после успешной регистрации пользователя
        print(f"Пользователь зарегистрирован: {user.id}")


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase[User, int] = Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    # Создаём менеджер, передавая ему подключение к таблице пользователей
    yield UserManager(user_db)