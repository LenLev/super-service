import os
import sys
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from main import app


class _FakeKafkaClient:
    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None


@pytest.fixture(autouse=True)
def _stub_lifespan_dependencies(monkeypatch):
    async def _noop_async() -> None:
        return None

    monkeypatch.setattr("main.init_db", _noop_async)
    monkeypatch.setattr("main.close_db", _noop_async)
    monkeypatch.setattr("main.KafkaModerationClient", _FakeKafkaClient)
    monkeypatch.setattr("main.get_or_train_model", lambda: MagicMock())
    monkeypatch.setattr("app.clients.redis.RedisClient.get_client", lambda: MagicMock())
    monkeypatch.setattr("app.clients.redis.RedisClient.close", _noop_async)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c