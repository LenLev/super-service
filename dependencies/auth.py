from typing import AsyncIterator, Optional

import asyncpg
from fastapi import Cookie, Depends, HTTPException, status

from db import get_connection
from repositories.accounts import Account, AccountRepository
from services.auth import AccountBlockedError, AuthService, InvalidTokenError

JWT_COOKIE_NAME = "access_token"
JWT_SECRET_KEY = "super-service-secret"
JWT_ALGORITHM = "HS256"
JWT_TTL_SECONDS = 3600


async def get_db_connection() -> AsyncIterator[asyncpg.Connection]:
    async with get_connection() as conn:
        yield conn


def get_account_repository(
    conn: asyncpg.Connection = Depends(get_db_connection),
) -> AccountRepository:
    return AccountRepository(conn)


def get_auth_service(
    account_repo: AccountRepository = Depends(get_account_repository),
) -> AuthService:
    return AuthService(
        account_repo,
        secret_key=JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
        token_ttl_seconds=JWT_TTL_SECONDS,
    )


async def get_current_account(
    access_token: Optional[str] = Cookie(default=None, alias=JWT_COOKIE_NAME),
    auth_service: AuthService = Depends(get_auth_service),
) -> Account:
    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизован",
        )

    try:
        return await auth_service.get_account_from_token(access_token)
    except (InvalidTokenError, AccountBlockedError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительные учетные данные",
        )
