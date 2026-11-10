"""PRESENTATION: turns exceptions from the inner layers into HTTP error responses."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.exceptions import (
    EmailAlreadyRegisteredError,
    IncorrectCurrentPasswordError,
    InvalidCredentialsError,
    InvalidTokenError,
    PasswordUnchangedError,
    PermissionDeniedError,
)

STATUS_CODES = {
    EmailAlreadyRegisteredError: 409,
    InvalidCredentialsError: 401,
    InvalidTokenError: 401,
    PermissionDeniedError: 403,
    IncorrectCurrentPasswordError: 400,
    PasswordUnchangedError: 400,
}


def register_error_handlers(app: FastAPI) -> None:
    def handle(request: Request, exc: Exception) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if isinstance(exc, InvalidTokenError) else None
        return JSONResponse({"detail": str(exc)}, status_code=STATUS_CODES[type(exc)], headers=headers)

    for exc_class in STATUS_CODES:
        app.add_exception_handler(exc_class, handle)
