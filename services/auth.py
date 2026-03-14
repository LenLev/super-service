from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt

from repositories.accounts import Account, AccountRepository


class AuthError(Exception):
    pass


class InvalidCredentialsError(AuthError):
    pass


class AccountBlockedError(AuthError):
    pass


class InvalidTokenError(AuthError):
    pass


class AuthService:
    def __init__(
        self,
        account_repo: AccountRepository,
        *,
        secret_key: str,
        algorithm: str = "HS256",
        token_ttl_seconds: int = 3600,
    ) -> None:
        self._account_repo = account_repo
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._token_ttl_seconds = token_ttl_seconds

    async def login(self, login: str, password: str) -> str:
        account = await self._account_repo.get_by_login_password(login=login, password=password)
        if account is None:
            raise InvalidCredentialsError("Неверный логин или пароль")

        if account.is_blocked:
            raise AccountBlockedError("Аккаунт заблокирован")

        return self.issue_token(account)

    def issue_token(self, account: Account) -> str:
        now = datetime.now(tz=timezone.utc)
        payload = {
            "sub": str(account.id),
            "login": account.login,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=self._token_ttl_seconds)).timestamp()),
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def decode_token(self, token: str) -> dict[str, Any]:
        try:
            return jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except jwt.PyJWTError as exc:
            raise InvalidTokenError("Недействительный токен") from exc

    async def get_account_from_token(self, token: str) -> Account:
        payload = self.decode_token(token)
        sub: Optional[str] = payload.get("sub")
        if sub is None or not sub.isdigit():
            raise InvalidTokenError("Токен содержит некорректный идентификатор")

        account = await self._account_repo.get_by_id(int(sub))
        if account is None:
            raise InvalidTokenError("Аккаунт не найден")
        if account.is_blocked:
            raise AccountBlockedError("Аккаунт заблокирован")

        return account
