from pydantic import BaseModel, Field


class AdRequest(BaseModel):
    seller_id: int
    is_verified_seller: bool
    item_id: int
    name: str
    description: str
    category: int
    images_qty: int


class SimplePredictRequest(BaseModel):
    item_id: int = Field(gt=0, description="Идентификатор объявления (> 0)")


class PredictResponse(BaseModel):
    is_violation: bool
    probability: float