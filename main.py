from contextlib import asynccontextmanager

from fastapi import FastAPI

from db import close_db, init_db
from model import get_or_train_model
from routers.predict import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Жизненный цикл:
    - при старте инициализируем пул подключений к БД (PostgreSQL через asyncpg)
    - загружаем/обучаем модель и сохраняем её в app.state.model
    - при остановке закрываем пул подключений
    """
    await init_db()
    app.state.model = get_or_train_model()
    try:
        yield
    finally:
        await close_db()


app = FastAPI(lifespan=lifespan)
app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
