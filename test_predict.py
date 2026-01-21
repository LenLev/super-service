import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Верифицированный продавец
def test_predict_verified_seller():
    data = {
        "seller_id": 1,
        "is_verified_seller": True,
        "item_id": 10,
        "name": "Обезьяна",
        "description": "Хорошая обезьяна",
        "category": 1,
        "images_qty": 0
    }
    
    response = client.post("/predict/", json=data)
    assert response.status_code == 200
    assert response.json() == {"result": True}

# Неверифицированный с фото
def test_predict_unverified_with_images():
    data = {
        "seller_id": 2,
        "is_verified_seller": False,
        "item_id": 11,
        "name": "Детские башмаки",
        "description": "Не ношеные",
        "category": 2,
        "images_qty": 3
    }
    
    response = client.post("/predict/", json=data)
    assert response.status_code == 200
    assert response.json() == {"result": True}

# Неверифицированный без фото
def test_predict_unverified_no_images():
    data = {
        "seller_id": 3,
        "is_verified_seller": False,
        "item_id": 12,
        "name": "Сосдка",
        "description": "Красивая сосдка",
        "category": 3,
        "images_qty": 0
    }
    
    response = client.post("/predict", json=data)
    assert response.status_code == 200
    assert response.json() == {"result": False}

# Неправильный тип данных
def test_validation_wrong_type():
    data = {
        "seller_id": "четыре",
        "is_verified_seller": False,
        "item_id": 13,
        "name": "Сухофрукты",
        "description": "Размоченные",
        "category": 1,
        "images_qty": 1
    }
    
    response = client.post("/predict/", json=data)
    assert response.status_code == 422

# Отсутствующее обязательное поле
def test_validation_missing_field():
    data = {
        # Нету id!
        "is_verified_seller": False,
        "item_id": 14,
        "name": "Календарь",
        "description": "2012 год",
        "category": 1,
        "images_qty": 1
    }
    
    response = client.post("/predict/", json=data)
    assert response.status_code == 422

def test_business_logic_error():
    data = {
        "seller_id": 5,
        "is_verified_seller": False,
        "item_id": 20,
        "name": "Яблоко",
        "description": "Отгрызенное яблоко",
        "category": 1,
        "images_qty": -100
    }

    response = client.post("/predict/", json=data)
    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
