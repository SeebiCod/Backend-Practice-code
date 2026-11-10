"""PRESENTATION: HTTP endpoints. Each one is: request schema -> command DTO -> use case -> response.

No business logic here, and no try/except: errors are turned into HTTP codes in error_handlers.py.
"""

from fastapi import APIRouter, Depends, Request, status

from app.application.dtos import ChangePasswordCommand, LoginCommand, RegisterUserCommand, UserDTO, CheckoutCommand
from app.application.use_cases import ChangePassword, GetMyActivity, ListUsers, Login, RegisterUser, StartCheckout
from app.infrastructure.database import check_database_connection
from app.infrastructure.mongo import check_mongo_connection
from app.presentation.dependencies import (
    current_user,
    get_change_password,
    get_list_users,
    get_login,
    get_my_activity,
    get_register_user,
    get_start_checkout,
)
from app.presentation.schemas import (
    AuthEventResponse,
    ChangePasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    CheckoutRequest,
    CheckoutResponse,
)

router = APIRouter()


@router.get("/")
def root():
    return {"message": "Authentication API is running"}


@router.get("/health/db")
def database_health():
    check_database_connection()
    return {"database": "connected"}


@router.get("/health/mongo")
def mongo_health():
    check_mongo_connection()
    return {"mongodb": "connected"}


@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, use_case: RegisterUser = Depends(get_register_user)):
    user = use_case.execute(RegisterUserCommand(email=body.email, password=body.password))
    return UserResponse(**vars(user))


@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, use_case: Login = Depends(get_login)):
    command = LoginCommand(
        email=body.email,
        password=body.password,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    token = use_case.execute(command)
    return TokenResponse(access_token=token.access_token, expires_in=token.expires_in)


@router.get("/auth/me", response_model=UserResponse)
def me(user: UserDTO = Depends(current_user)):
    return UserResponse(**vars(user))


@router.get("/auth/me/activity", response_model=list[AuthEventResponse])
def my_activity(user: UserDTO = Depends(current_user), use_case: GetMyActivity = Depends(get_my_activity)):
    return [AuthEventResponse(**vars(e)) for e in use_case.execute(user.id)]


@router.post("/auth/change-password", response_model=MessageResponse)
def change_password(
    body: ChangePasswordRequest,
    user: UserDTO = Depends(current_user),
    use_case: ChangePassword = Depends(get_change_password),
):
    use_case.execute(
        ChangePasswordCommand(
            user_id=user.id,
            current_password=body.current_password,
            new_password=body.new_password,
        )
    )
    return MessageResponse(message="Password changed successfully")


@router.get("/users", response_model=list[UserResponse])
def list_users(user: UserDTO = Depends(current_user), use_case: ListUsers = Depends(get_list_users)):
    return [UserResponse(**vars(u)) for u in use_case.execute(user.id)]


# routes.py
@router.post("/payments/checkout", response_model=CheckoutResponse)
def checkout(body: CheckoutRequest, user=Depends(current_user),
             use_case: StartCheckout = Depends(get_start_checkout)):
    result = use_case.execute(CheckoutCommand(user_id=user.id, amount_cents=body.amount_cents))
    return CheckoutResponse(checkout_url=result.checkout_url)
