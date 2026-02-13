from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.clients.kafka import KafkaModerationClient
from db import close_db, init_db
from model import get_or_train_model
from routers.predict import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Жизненный цикл:
    - при старте инициализируем пул подключений к БД (PostgreSQL через asyncpg)
    - поднимаем Kafka producer для задач модерации
    - загружаем/обучаем модель и сохраняем её в app.state.model
    - при остановке закрываем пул подключений и Kafka producer
    """
    await init_db()
    kafka_client = KafkaModerationClient()
    await kafka_client.start()

    app.state.model = get_or_train_model()
    app.state.kafka_client = kafka_client

    try:
        yield
    finally:
        await kafka_client.stop()
        await close_db()


app = FastAPI(lifespan=lifespan)
app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
