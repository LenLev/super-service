import pytest
from typing import Optional

from repositories.accounts import Account
from services.auth import (
    AccountBlockedError,
    AuthService,
    InvalidCredentialsError,
    InvalidTokenError,
)


class FakeAccountRepo:
    def __init__(self) -> None:
        self.by_id: dict[int, Account] = {}
        self.by_credentials: dict[tuple[str, str], Account] = {}

    async def get_by_id(self, account_id: int) -> Optional[Account]:
        return self.by_id.get(account_id)

    async def get_by_login_password(self, login: str, password: str) -> Optional[Account]:
        return self.by_credentials.get((login, password))


@pytest.mark.asyncio
async def test_login_returns_token_for_valid_account() -> None:
    repo = FakeAccountRepo()
    account = Account(id=1, login="user", password="pass", is_blocked=False)
    repo.by_credentials[("user", "pass")] = account
    repo.by_id[1] = account

    service = AuthService(repo, secret_key="test-secret", token_ttl_seconds=600)

    token = await service.login("user", "pass")

    parsed_account = await service.get_account_from_token(token)
    assert parsed_account.id == 1


@pytest.mark.asyncio
async def test_login_raises_for_invalid_credentials() -> None:
    repo = FakeAccountRepo()
    service = AuthService(repo, secret_key="test-secret")

    with pytest.raises(InvalidCredentialsError):
        await service.login("missing", "missing")


@pytest.mark.asyncio
async def test_login_raises_for_blocked_account() -> None:
    repo = FakeAccountRepo()
    blocked = Account(id=2, login="blocked", password="pass", is_blocked=True)
    repo.by_credentials[("blocked", "pass")] = blocked

    service = AuthService(repo, secret_key="test-secret")

    with pytest.raises(AccountBlockedError):
        await service.login("blocked", "pass")


@pytest.mark.asyncio
async def test_get_account_from_token_raises_when_account_missing() -> None:
    repo = FakeAccountRepo()
    service = AuthService(repo, secret_key="test-secret")

    token = service.issue_token(Account(id=100, login="ghost", password="x", is_blocked=False))

    with pytest.raises(InvalidTokenError):
        await service.get_account_from_token(token)


@pytest.mark.asyncio
async def test_get_account_from_token_raises_when_account_blocked() -> None:
    repo = FakeAccountRepo()
    blocked = Account(id=7, login="u", password="p", is_blocked=True)
    repo.by_id[7] = blocked

    service = AuthService(repo, secret_key="test-secret")
    token = service.issue_token(blocked)

    with pytest.raises(AccountBlockedError):
        await service.get_account_from_token(token)


def test_decode_token_raises_for_invalid_token() -> None:
    repo = FakeAccountRepo()
    service = AuthService(repo, secret_key="test-secret")

    with pytest.raises(InvalidTokenError):
        service.decode_token("invalid.token.value")
