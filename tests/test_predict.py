import pytest
from main import app

@pytest.mark.parametrize(
    "is_verified_seller, images_qty",
    [
        (True, 0),     # верифицированный продавец
        (False, 3),    # не верифицированный, есть фото
        (False, 0),    # не верифицированный, нет фото
    ]
)
def test_predict_logic_basic(client, is_verified_seller, images_qty):
    data = {
        "seller_id": 1,
        "is_verified_seller": is_verified_seller,
        "item_id": 10,
        "name": "Я тестовое объявление",
        "description": "Я тестовое описание объявления",
        "category": 1,
        "images_qty": images_qty
    }

    response = client.post("/predict", json=data)

    assert response.status_code == 200

    response_data = response.json()
    
    assert "is_violation" in response_data
    assert "probability" in response_data

    assert isinstance(response_data["is_violation"], bool)
    assert isinstance(response_data["probability"], float)

    assert 0.0 <= response_data["probability"] <= 1.0

# Тест успешного предсказания (is_violation = True)
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

# Тест успешного предсказания (is_violation = False)
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
        "seller_id": "четыре",   # неправильный тип
        "is_verified_seller": False,
        "item_id": 13,
        "name": "Сухофрукты",
        "description": "Размоченные",
        "category": 1,
        "images_qty": 1
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
        "images_qty": 1
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
        "images_qty": -100   # ошибка бизнес-логики
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
        "images_qty": 1
    }

    response = client.post("/predict", json=data)
    assert response.status_code == 503
    assert response.json()["detail"] == "Модель не загружена"


def test_root(client):
    response = client.get("/")

    assert response.status_code == 200

    response_data = response.json()
    assert "message" in response_data
