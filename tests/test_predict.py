import pytest
from unittest.mock import AsyncMock, MagicMock
from main import app
from fastapi.testclient import TestClient
from repositories.ads import Ad
from repositories.moderation_results import ModerationResult

@pytest.fixture
def client_mock():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def mock_repos_and_db(monkeypatch):
    ad_repo_instance = AsyncMock()
    user_repo_instance = AsyncMock()
    mod_repo_instance = AsyncMock()
    cache_repo_instance = AsyncMock()

    mock_conn = AsyncMock()
    mock_conn.__aenter__.return_value = AsyncMock()
    mock_conn.__aexit__.return_value = None
    
    monkeypatch.setattr("routers.predict.get_connection", lambda: mock_conn)
    
    ad_repo_instance.get.return_value = None
    
    monkeypatch.setattr("routers.predict.AdRepository", lambda conn: ad_repo_instance)
    monkeypatch.setattr("routers.predict.UserRepository", lambda conn: user_repo_instance)
    monkeypatch.setattr("routers.predict.ModerationResultRepository", lambda conn: mod_repo_instance)
    monkeypatch.setattr("routers.predict.PredictionCacheRepository", lambda client: cache_repo_instance)
    
    monkeypatch.setattr("app.clients.redis.RedisClient.get_client", lambda: MagicMock())

    return {
        "ad_repo": ad_repo_instance,
        "user_repo": user_repo_instance,
        "mod_repo": mod_repo_instance,
        "cache_repo": cache_repo_instance
    }

@pytest.fixture
def mock_model(monkeypatch):
    model = MagicMock()
    monkeypatch.setattr(app.state, "model", model, raising=False)
    return model

@pytest.mark.parametrize("payload", [
    {"item_id": 10},
])
def test_simple_predict_cache_hit(client_mock, mock_repos_and_db, mock_model, payload):
    mock_repos_and_db["cache_repo"].get_prediction.return_value = {
        "is_violation": True,
        "probability": 0.95
    }
    
    response = client_mock.post("/simple_predict", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_violation"] is True
    assert data["probability"] == 0.95
    
    mock_repos_and_db["ad_repo"].get.assert_not_called()
    mock_model.predict_proba.assert_not_called()

def test_simple_predict_cache_miss(client_mock, mock_repos_and_db, mock_model):
    mock_repos_and_db["cache_repo"].get_prediction.return_value = None
    
    ad = Ad(id=10, seller_id=1, title="Test", description="Desc", category=1, images_qty=1)
    mock_repos_and_db["ad_repo"].get.return_value = ad
    
    user = MagicMock()
    user.id = 1
    user.is_verified_seller = False
    mock_repos_and_db["user_repo"].get.return_value = user
    
    mock_model.predict_proba.return_value = [[0.1, 0.8]]
    
    response = client_mock.post("/simple_predict", json={"item_id": 10})
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_violation"] is True
    assert data["probability"] == 0.8
    
    mock_repos_and_db["ad_repo"].get.assert_awaited_once_with(10)
    
    mock_repos_and_db["cache_repo"].set_prediction.assert_awaited_once()

def test_close_ad(client_mock, mock_repos_and_db):
    ad = Ad(id=10, seller_id=1, title="Test", description="Desc", category=1, images_qty=1)
    mock_repos_and_db["ad_repo"].get.return_value = ad
    
    response = client_mock.post("/close", params={"item_id": 10})
    assert response.status_code == 200
    
    mock_repos_and_db["ad_repo"].close.assert_awaited_once_with(10)
    mock_repos_and_db["mod_repo"].delete_by_item_id.assert_awaited_once_with(10)
    mock_repos_and_db["cache_repo"].delete_prediction.assert_awaited_once_with(10)
