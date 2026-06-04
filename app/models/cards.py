from sqlalchemy import Column, Integer, String
from app.core.db import Base

class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String)
    translation = Column(String)