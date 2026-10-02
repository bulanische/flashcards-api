import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.language import Language

# Путь к файлу со справочником языков
LANGUAGES_FILE = Path(__file__).parent / "data" / "languages.json"

# Создаём синхронный URL для подключения к PostgreSQL
DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{settings.postgres_user}:{settings.postgres_password.get_secret_value()}"
    f"@{settings.postgres_server}:{settings.postgres_port}"
    f"/{settings.postgres_db}"
)

def load_languages():
    # Открываем JSON-файл с кодировкой UTF-8
    with LANGUAGES_FILE.open("r", encoding="utf-8") as file:
        # Преобразуем JSON в Python-словарь
        return json.load(file)

# Создаём синхронный движок SQLAlchemy
engine = create_engine(DATABASE_URL)


def seed_languages():
    # Загружаем языки из JSON-файла
    languages = load_languages()

    # Открываем соединение с базой данных
    with Session(engine) as session:
        # Перебираем все языки из справочника
        for language_data in languages.values():
            # Получаем ISO 639-1 код языка
            code = language_data["639-1"]

            # Проверяем, существует ли такой код в базе
            existing_language = session.query(Language).filter_by(
                code=code
            ).first()

            # Пропускаем язык, если он уже есть
            if existing_language:
                continue

            # Создаём системный язык
            language = Language(
                name=language_data["name"],
                native_name=language_data["nativeName"],
                code=code,
                user_id=None,
            )

            session.add(language)

        # Сохраняем все новые языки
        session.commit()

if __name__ == "__main__":
    seed_languages()