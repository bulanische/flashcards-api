# Flashcards API

API для изучения слов с помощью карточек (spaced repetition).

## 🚀 Стек

* FastAPI
* SQLAlchemy
* Pydantic v2

## 📦 Установка

```bash
git clone https://github.com/your-username/flashcards-api.git
cd flashcards-api
pip install -r requirements.txt
```

## ▶️ Запуск

```bash
uvicorn app.main:app --reload
```

## 📡 API

Swagger доступен по адресу:

```
http://localhost:8000/docs
```

## 📌 Возможности

* создание карточек
* просмотр карточек
* (в будущем) интервальное повторение
