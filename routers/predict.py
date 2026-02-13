import logging

from fastapi import APIRouter, HTTPException, Request

from db import get_connection
from repositories.ads import AdRepository
from repositories.moderation_results import ModerationResultRepository
from repositories.users import UserRepository
from schemas.models import (
    AdRequest,
    AsyncPredictRequest,
    AsyncPredictResponse,
    ModerationStatusResponse,
    PredictResponse,
    SimplePredictRequest,
)
from services.moderation import prepare_features


router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_model_from_app(request: Request):
    model = getattr(request.app.state, "model", None)
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Модель не загружена",
        )
    return model


@router.post("/predict", response_model=PredictResponse)
async def predict(ad: AdRequest, request: Request):

    model = _get_model_from_app(request)

    try:
        features = prepare_features(ad)

        logger.info(
            "Request: seller_id=%s, item_id=%s, features=%s",
            ad.seller_id,
            ad.item_id,
            features.tolist(),
        )

        probability = float(model.predict_proba(features)[0][1])
        is_violation = probability > 0.5

        logger.info(
            "Result: is_violation=%s, probability=%s",
            is_violation,
            probability,
        )

        return PredictResponse(
            is_violation=is_violation,
            probability=probability,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )


@router.post("/simple_predict", response_model=PredictResponse)
async def simple_predict(payload: SimplePredictRequest, request: Request):
    model = _get_model_from_app(request)

    async with get_connection() as conn:
        ad_repo = AdRepository(conn)
        user_repo = UserRepository(conn)

        ad = await ad_repo.get(payload.item_id)
        if ad is None:
            raise HTTPException(status_code=404, detail="Объявление не найдено")

        user = await user_repo.get(ad.seller_id)
        if user is None:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        ad_request = AdRequest(
            seller_id=user.id,
            is_verified_seller=user.is_verified_seller,
            item_id=ad.id,
            name=ad.title,
            description=ad.description,
            category=ad.category,
            images_qty=ad.images_qty,
        )

        try:
            features = prepare_features(ad_request)
            probability = float(model.predict_proba(features)[0][1])
            is_violation = probability > 0.5

            logger.info(
                "Simple predict: item_id=%s, seller_id=%s, is_violation=%s, probability=%s",
                ad.id,
                user.id,
                is_violation,
                probability,
            )

            return PredictResponse(
                is_violation=is_violation,
                probability=probability,
            )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error: {str(e)}",
            )


@router.post("/async_predict", response_model=AsyncPredictResponse)
async def async_predict(payload: AsyncPredictRequest, request: Request):

    # объявление существует
    async with get_connection() as conn:
        ad_repo = AdRepository(conn)
        mod_repo = ModerationResultRepository(conn)

        ad = await ad_repo.get(payload.item_id)
        if ad is None:
            raise HTTPException(status_code=404, detail="Объявление не найдено")

        moderation_result = await mod_repo.create_pending(item_id=ad.id)

    # отправляем задачу в Kafka
    kafka_client = getattr(request.app.state, "kafka_client", None)
    if kafka_client is None:
        raise HTTPException(status_code=503, detail="Kafka producer недоступен")

    await kafka_client.send_moderation_request(
        item_id=moderation_result.item_id,
        task_id=moderation_result.id,
    )

    return AsyncPredictResponse(
        task_id=moderation_result.id,
        status=moderation_result.status,
        message="Moderation request accepted",
    )


@router.get("/moderation_result/{task_id}", response_model=ModerationStatusResponse)
async def get_moderation_result(task_id: int):
    async with get_connection() as conn:
        repo = ModerationResultRepository(conn)
        result = await repo.get(task_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Задача модерации не найдена")

    return ModerationStatusResponse(
        task_id=result.id,
        status=result.status,
        is_violation=result.is_violation,
        probability=result.probability,
    )