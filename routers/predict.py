import logging

from fastapi import APIRouter, HTTPException, Request

from schemas.models import AdRequest
from services.moderation import prepare_features


router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/predict")
async def predict(ad: AdRequest, request: Request):

    model = getattr(request.app.state, "model", None)

    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Модель не загружена",
        )

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

        return {
            "is_violation": is_violation,
            "probability": probability,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )