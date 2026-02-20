import pytest
from app.clients.redis import RedisClient
from repositories.prediction_cache import PredictionCacheRepository

@pytest.mark.integration
async def test_redis_cache():
    redis = RedisClient.get_client()
    repo = PredictionCacheRepository(redis)
    
    item_id = 99999
    data = {"is_violation": True, "probability": 0.5}
    
    await repo.set_prediction(item_id, data)
    
    cached = await repo.get_prediction(item_id)
    assert cached is not None
    assert cached["is_violation"] is True
    assert cached["probability"] == 0.5
    
    await repo.delete_prediction(item_id)
    cached = await repo.get_prediction(item_id)
    assert cached is None
    
    await RedisClient.close()
