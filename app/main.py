from fastapi import FastAPI
from api.endpoints.cards import cards_router
from api.endpoints.decks import decks_router 

app = FastAPI()

app.include_router(cards_router)
app.include_router(decks_router)