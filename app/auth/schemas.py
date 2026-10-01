from fastapi_users import schemas


class UserRead(schemas.BaseUser[int]):
    """Схема пользователя, которую можно возвращать клиенту."""


class UserCreate(schemas.BaseUserCreate):
    """Схема для регистрации нового пользователя."""

