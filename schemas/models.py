from typing import Optional
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


class AsyncPredictRequest(BaseModel):
    item_id: int = Field(gt=0, description="Идентификатор объявления (> 0)")


class AsyncPredictResponse(BaseModel):
    task_id: int
    status: str
    message: str


class ModerationStatusResponse(BaseModel):
    task_id: int
    status: str
    is_violation: Optional[bool] = None
    probability: Optional[float] = None