from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Импортируем настройки подключения к базе данных
from app.core.config import settings
# Импортируем Base, в котором зарегистрирована metadata всех моделей
from app.core.db import Base
# Импортируем все модели, чтобы SQLAlchemy зарегистрировал их в Base.metadata
from app import models

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Получаем аргументы, переданные через -x.
is_test = context.get_x_argument(as_dictionary=True).get("test") == "true"

# Выбираем базу по аргументу команды.
database_url = settings.database_url
if is_test:
    database_url = database_url.rsplit("/", 1)[0] + "/cards_test"

# Временно проверяем выбранную базу.
print(f"Alembic test mode: {is_test}")
print(f"Alembic database URL: {database_url}")
# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Передаём Alembic metadata всех наших SQLAlchemy-моделей
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Используем URL базы данных из настроек приложения
    url = database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()



def run_migrations_online() -> None:
    """Запускает миграции в обычном режиме."""

    # Создаём синхронный URL для Alembic.
    sync_database_url = database_url.replace(
        "postgresql+asyncpg://",
        "postgresql://",
    )

    # Создаём подключение к выбранной базе данных.
    connectable = engine_from_config(
        {"sqlalchemy.url": sync_database_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Открываем соединение с базой данных.
    with connectable.connect() as connection:
        # Передаём соединение и metadata моделей Alembic.
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        # Запускаем миграции внутри транзакции.
        with context.begin_transaction():
            context.run_migrations()
