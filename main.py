from contextlib import asynccontextmanager

from fastapi import FastAPI

from model import get_or_train_model
from routers.predict import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Жизненный цикл приложения: при старте загружаем/обучаем модель
    и сохраняем её в app.state.model.
    """
    app.state.model = get_or_train_model()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
