import pytest
from typing import Optional
from typing import Iterator
from fastapi.testclient import TestClient

from dependencies.auth import get_auth_service
from main import app
from services.auth import AccountBlockedError, InvalidCredentialsError


class FakeAuthService:
    def __init__(self, *, token: Optional[str] = None, error: Optional[Exception] = None) -> None:
        self._token = token
        self._error = error

    async def login(self, login: str, password: str) -> str:
        if self._error is not None:
            raise self._error
        assert self._token is not None
        return self._token


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_login_sets_cookie_and_returns_token(client: TestClient) -> None:
    app.dependency_overrides[get_auth_service] = lambda: FakeAuthService(token="jwt-token")

    response = client.post("/login", json={"login": "user", "password": "pass"})

    assert response.status_code == 200
    assert response.json()["access_token"] == "jwt-token"
    assert "access_token=jwt-token" in response.headers.get("set-cookie", "")


def test_login_returns_401_for_invalid_credentials(client: TestClient) -> None:
    app.dependency_overrides[get_auth_service] = lambda: FakeAuthService(
        error=InvalidCredentialsError("bad creds"),
    )

    response = client.post("/login", json={"login": "user", "password": "pass"})

    assert response.status_code == 401


def test_login_returns_403_for_blocked_account(client: TestClient) -> None:
    app.dependency_overrides[get_auth_service] = lambda: FakeAuthService(
        error=AccountBlockedError("blocked"),
    )

    response = client.post("/login", json={"login": "user", "password": "pass"})

    assert response.status_code == 403
