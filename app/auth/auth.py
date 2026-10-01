from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)

from app.core.config import settings


# Определяем, как JWT-токен будет передаваться клиентом
bearer_transport = BearerTransport(
    tokenUrl="/auth/login",
)


def get_jwt_strategy() -> JWTStrategy:
    # Создаём стратегию, которая подписывает и проверяет JWT
    return JWTStrategy(
        secret=settings.secret_key,
        lifetime_seconds=3600,
    )


# Создаём backend аутентификации на основе Bearer JWT
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)
