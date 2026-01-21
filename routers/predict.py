from fastapi import APIRouter, HTTPException
from schemas.models import AdRequest

router = APIRouter()

@router.post("/predict")
async def predict(ad: AdRequest):
    """
    Принимает json с полями AdRequest и возвращает dict с ключом 'result' (bool).

    Прогнозирует, пройдет ли объявление модерацию.
    Верифицированные продавцы всегда проходят.
    Неверифицированные проходят только если у них есть фото.
    Обрабатывает ошибки бизнес-логики и возвращает 500 в случае ошибок.
    Возвращает 422 при ошибках валидации Pydantic."""
    try:
        if ad.images_qty < 0:
            raise ValueError("images_qty не может быть отрицательным")
        
        if ad.is_verified_seller:
            return {"result": True}
        return {"result": ad.images_qty > 0}
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )