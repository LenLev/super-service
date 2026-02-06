import os
import tempfile

import pytest

from db import get_db_path, init_db
from main import app
from repositories.ads import AdRepository
from repositories.users import UserRepository


@pytest.fixture(autouse=True)
def _temp_db(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_db.sqlite3")
        monkeypatch.setenv("DATABASE_PATH", db_path)
        init_db()
        yield


@pytest.mark.parametrize(
    "is_verified_seller, images_qty",
    [
        (True, 0),  # верифицированный продавец
        (False, 3),  # не верифицированный, есть фото
        (False, 0),  # не верифицированный, нет фото
    ],
)
def test_predict_logic_basic(client, is_verified_seller, images_qty):
    data = {
        "seller_id": 1,
        "is_verified_seller": is_verified_seller,
        "item_id": 10,
        "name": "Я тестовое объявление",
        "description": "Я тестовое описание объявления",
        "category": 1,
        "images_qty": images_qty,
    }

    response = client.post("/predict", json=data)

    assert response.status_code == 200

    response_data = response.json()

    assert "is_violation" in response_data
    assert "probability" in response_data

    assert isinstance(response_data["is_violation"], bool)
    assert isinstance(response_data["probability"], float)

    assert 0.0 <= response_data["probability"] <= 1.0


def test_predict_violation_true(client, monkeypatch):
    class DummyModel:
        def predict_proba(self, X):
            return [[0.1, 0.9]]

    monkeypatch.setattr(app.state, "model", DummyModel(), raising=False)

    data = {
        "seller_id": 1,
        "is_verified_seller": False,
        "item_id": 10,
        "name": "Я тесто",
        "description": "Я тестовое описание",
        "category": 1,
        "images_qty": 1,
    }

    response = client.post("/predict", json=data)
    assert response.status_code == 200
    body = response.json()
    assert body["is_violation"] is True
    assert 0.0 <= body["probability"] <= 1.0


def test_predict_violation_false(client, monkeypatch):
    class DummyModel:
        def predict_proba(self, X):
            return [[0.9, 0.1]]

    monkeypatch.setattr(app.state, "model", DummyModel(), raising=False)

    data = {
        "seller_id": 1,
        "is_verified_seller": True,
        "item_id": 10,
        "name": "Клавиатура",
        "description": "Тактильная клавиатура",
        "category": 1,
        "images_qty": 1,
    }

    response = client.post("/predict", json=data)
    assert response.status_code == 200
    body = response.json()
    assert body["is_violation"] is False
    assert 0.0 <= body["probability"] <= 1.0


def test_validation_wrong_type(client):
    data = {
        "seller_id": "четыре",  # неправильный тип
        "is_verified_seller": False,
        "item_id": 13,
        "name": "Сухофрукты",
        "description": "Размоченные",
        "category": 1,
        "images_qty": 1,
    }

    response = client.post("/predict", json=data)
    assert response.status_code == 422


def test_validation_missing_field(client):
    data = {
        # нет seller_id
        "is_verified_seller": False,
        "item_id": 14,
        "name": "Календарь",
        "description": "2012 год",
        "category": 1,
        "images_qty": 1,
    }

    response = client.post("/predict", json=data)
    assert response.status_code == 422


def test_business_logic_error(client):
    data = {
        "seller_id": 5,
        "is_verified_seller": False,
        "item_id": 20,
        "name": "Яблоко",
        "description": "Отгрызенное яблоко",
        "category": 1,
        "images_qty": -100,  # ошибка бизнес-логики
    }

    response = client.post("/predict", json=data)
    assert response.status_code == 500

    response_data = response.json()
    assert "detail" in response_data
    assert "Internal server error" in response_data["detail"]


def test_model_not_loaded(client, monkeypatch):
    monkeypatch.setattr(app.state, "model", None, raising=False)

    data = {
        "seller_id": 1,
        "is_verified_seller": True,
        "item_id": 1,
        "name": "Товар",
        "description": "Описание",
        "category": 1,
        "images_qty": 1,
    }

    response = client.post("/predict", json=data)
    assert response.status_code == 503
    assert response.json()["detail"] == "Модель не загружена"


def test_simple_predict_positive(client, monkeypatch, tmp_path):
    class DummyModel:
        def predict_proba(self, X):
            return [[0.1, 0.9]]

    monkeypatch.setattr(app.state, "model", DummyModel(), raising=False)

    from db import get_connection

    with get_connection() as conn:
        user_repo = UserRepository(conn)
        ad_repo = AdRepository(conn)

        user = user_repo.create(is_verified_seller=False)
        ad = ad_repo.create(
            seller_id=user.id,
            title="Объявление",
            description="Описание",
            category=1,
            images_qty=1,
        )

    response = client.post("/simple_predict", json={"item_id": ad.id})

    assert response.status_code == 200
    body = response.json()
    assert body["is_violation"] is True
    assert 0.0 <= body["probability"] <= 1.0


def test_simple_predict_negative(client, monkeypatch):
    class DummyModel:
        def predict_proba(self, X):
            return [[0.9, 0.1]]

    monkeypatch.setattr(app.state, "model", DummyModel(), raising=False)

    from db import get_connection

    with get_connection() as conn:
        user_repo = UserRepository(conn)
        ad_repo = AdRepository(conn)

        user = user_repo.create(is_verified_seller=True)
        ad = ad_repo.create(
            seller_id=user.id,
            title="Честное объявление",
            description="Просто товар",
            category=1,
            images_qty=1,
        )

    response = client.post("/simple_predict", json={"item_id": ad.id})

    assert response.status_code == 200
    body = response.json()
    assert body["is_violation"] is False
    assert 0.0 <= body["probability"] <= 1.0


def test_repositories_create_and_read():
    from db import get_connection

    with get_connection() as conn:
        user_repo = UserRepository(conn)
        ad_repo = AdRepository(conn)

        user = user_repo.create(is_verified_seller=True)
        assert user.id is not None
        loaded_user = user_repo.get(user.id)
        assert loaded_user is not None
        assert loaded_user.is_verified_seller is True

        ad = ad_repo.create(
            seller_id=user.id,
            title="Тестовое объявление",
            description="Описание",
            category=2,
            images_qty=5,
        )
        assert ad.id is not None

        loaded_ad = ad_repo.get(ad.id)
        assert loaded_ad is not None
        assert loaded_ad.seller_id == user.id
        assert loaded_ad.title == "Тестовое объявление"


def test_root(client):
    response = client.get("/")

    assert response.status_code == 200

    response_data = response.json()
    assert "message" in response_data
