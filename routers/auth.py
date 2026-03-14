from fastapi import APIRouter, Depends, HTTPException, Response, status

from dependencies.auth import (
    JWT_COOKIE_NAME,
    JWT_TTL_SECONDS,
    get_auth_service,
)
from schemas.models import LoginRequest, LoginResponse
from services.auth import AccountBlockedError, AuthService, InvalidCredentialsError

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    try:
        token = await auth_service.login(login=payload.login, password=payload.password)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )
    except AccountBlockedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт заблокирован",
        )

    response.set_cookie(
        key=JWT_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=JWT_TTL_SECONDS,
        samesite="lax",
    )

    return LoginResponse(access_token=token)
