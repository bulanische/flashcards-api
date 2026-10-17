from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routers import main_router
from app.auth.router import router as auth_router
from app.core.config import settings
from app import models


app = FastAPI(
    title=settings.app_title,
    description=settings.description
)

# Определяем путь к папке с frontend относительно этого файла.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

# Подключаем CSS и JavaScript.
app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static",
)

# Подключаем главную страницу клиентского приложения.
@app.get("/", include_in_schema=False)
async def get_frontend() -> FileResponse:
    """Возвращает главную страницу frontend."""
    return FileResponse(FRONTEND_DIR / "index.html")

app.include_router(main_router)
app.include_router(auth_router)




# uvicorn app.main:app --reload
# docker compose up -d
# workflow для запуска всего проекта: из директории /cards команда "./start.sh"
