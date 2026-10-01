from fastapi import APIRouter

from app.api.endpoints import cards_router, decks_router, languages_router


main_router = APIRouter()

main_router.include_router(
    cards_router,
    prefix='/cards',
    tags=['Карточки'],
)

main_router.include_router(
    decks_router,
    prefix='/decks',
    tags=['Колоды'],
)

main_router.include_router(
    languages_router,
    prefix='/languages',
    tags=['Языки'],
)
