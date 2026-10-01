from fastapi import APIRouter, Depends
from fastapi_users import FastAPIUsers


from app.auth.auth import auth_backend
from app.auth.manager import get_user_manager
from app.auth.schemas import UserCreate, UserRead
from app.models.user import User

# Создаём объект FastAPI Users, объединяющий менеджер пользователя и backend авторизации
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)


# Получаем dependency для получения текущего пользователя
current_user = fastapi_users.current_user(active=True)


# Создаём роутер для авторизации
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


# Подключаем маршруты регистрации пользователя
router.include_router(
    fastapi_users.get_register_router(
        UserRead,
        UserCreate,
    ),
)


# Подключаем маршруты входа и выхода
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
)

@router.get("/me")
async def get_current_user(
    user: User = Depends(current_user),
):
    # Возвращаем данные текущего авторизованного пользователя
    return user