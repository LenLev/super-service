import pytest
from typing import Optional
from fastapi import HTTPException

from dependencies.auth import get_current_account
from repositories.accounts import Account
from services.auth import AccountBlockedError, InvalidTokenError


class FakeAuthService:
    def __init__(self, *, result: Optional[Account] = None, error: Optional[Exception] = None) -> None:
        self._result = result
        self._error = error

    async def get_account_from_token(self, token: str) -> Account:
        if self._error is not None:
            raise self._error
        assert self._result is not None
        return self._result


@pytest.mark.asyncio
async def test_get_current_account_success() -> None:
    auth_service = FakeAuthService(
        result=Account(id=1, login="u", password="p", is_blocked=False),
    )

    account = await get_current_account(access_token="token", auth_service=auth_service)

    assert account.id == 1


@pytest.mark.asyncio
async def test_get_current_account_raises_when_cookie_missing() -> None:
    auth_service = FakeAuthService(
        result=Account(id=1, login="u", password="p", is_blocked=False),
    )

    with pytest.raises(HTTPException) as exc:
        await get_current_account(access_token=None, auth_service=auth_service)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [InvalidTokenError("bad token"), AccountBlockedError("blocked")],
)
async def test_get_current_account_raises_for_invalid_token_or_blocked(error: Exception) -> None:
    auth_service = FakeAuthService(error=error)

    with pytest.raises(HTTPException) as exc:
        await get_current_account(access_token="token", auth_service=auth_service)

    assert exc.value.status_code == 401
