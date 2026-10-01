from pydantic import EmailStr, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфиг проекта"""

    app_title: str = "Карточки для изучения иностранного языка"
    description: str = (
        "Получение карточек со словом и его значением для изучения "
        "иностранного языка"
    )
    # Секретный ключ для JWT и других криптографических операций
    secret_key: str
    database_url: str = "DB_URL"
    first_superuser_email: EmailStr | None = None
    first_superuser_password: str | None = None
    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    postgres_server: str
    postgres_port: int = 5432

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
