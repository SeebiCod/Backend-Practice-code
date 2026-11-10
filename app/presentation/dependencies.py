"""PRESENTATION: wires real implementations into the use cases (dependency injection).

This is the only file that knows which concrete classes are used. Tests swap them
with `app.dependency_overrides[get_users] = ...`.
"""

from collections.abc import Iterator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.dtos import UserDTO
from app.application.use_cases import (
    ChangePassword,
    GetCurrentUser,
    GetMyActivity,
    ListUsers,
    Login,
    RegisterUser,
    StartCheckout,
)
from app.domain.repository import AuthEventRepository, UserRepository
from app.infrastructure.database import SessionLocal
from app.infrastructure.mongo import MongoAuthEventRepository, auth_events
from app.infrastructure.security import JwtTokenService, PwdlibPasswordHasher
from app.infrastructure.user_repository import SqlAlchemyUserRepository
from app.infrastructure.stripe_gateway import StripePaymentGateway

hasher = PwdlibPasswordHasher()
tokens = JwtTokenService()


def get_users() -> Iterator[UserRepository]:
    """One database session per request, closed when the request ends."""
    db = SessionLocal()
    try:
        yield SqlAlchemyUserRepository(db)
    finally:
        db.close()


def get_register_user(users: UserRepository = Depends(get_users)) -> RegisterUser:
    return RegisterUser(users, hasher)


def get_events() -> AuthEventRepository:
    """MongoDB activity log. One shared client for the whole app (pymongo pools connections itself)."""
    return MongoAuthEventRepository(auth_events)


def get_login(
    users: UserRepository = Depends(get_users),
    events: AuthEventRepository = Depends(get_events),
) -> Login:
    return Login(users, hasher, tokens, events)


def get_my_activity(events: AuthEventRepository = Depends(get_events)) -> GetMyActivity:
    return GetMyActivity(events)


def get_list_users(users: UserRepository = Depends(get_users)) -> ListUsers:
    return ListUsers(users)


def get_change_password(users: UserRepository = Depends(get_users)) -> ChangePassword:
    return ChangePassword(users, hasher)


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    users: UserRepository = Depends(get_users),
) -> UserDTO:
    """Guard for protected routes: `Authorization: Bearer <token>` -> UserDTO, or 401."""
    token = credentials.credentials if credentials else None
    return GetCurrentUser(users, tokens).execute(token)

payments = StripePaymentGateway()

def get_start_checkout(users=Depends(get_users)) -> StartCheckout:
    return StartCheckout(users, payments)
