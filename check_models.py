from sqlalchemy.orm import configure_mappers

from app.core.db import Base
from app import models


# Принудительно настраиваем все ORM-связи между моделями
configure_mappers()


# Выводим все таблицы, зарегистрированные в SQLAlchemy
print("Зарегистрированные таблицы:")
for table_name in Base.metadata.tables:
    print(f"- {table_name}")

print("ORM-связи успешно настроены.")