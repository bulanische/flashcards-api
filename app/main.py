from fastapi import FastAPI

from app.api.routers import main_router
from app.auth.router import router as auth_router
from app.core.config import settings
from app import models

app = FastAPI(
    title=settings.app_title,
    description=settings.description
)

app.include_router(main_router)
app.include_router(auth_router)




# uvicorn app.main:app --reload
# docker compose up -d
