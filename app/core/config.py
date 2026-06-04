from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфиг проекта"""

    app_title: str = "Карточки для изучения иностранного языка"
    description: str = (
        "Получение карточек со словом и его значением для изучения "
        "иностранного языка"
    )
    secret: str = "SECRET"
    database_url: str = "sqlite+aiosqlite:///./fastapi.db"
    first_superuser_email: EmailStr | None = None
    first_superuser_password: str | None = None

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
