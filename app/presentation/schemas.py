"""PRESENTATION: the JSON shapes of the API (Pydantic validates incoming requests)."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    created_at: datetime | None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class MessageResponse(BaseModel):
    message: str


class AuthEventResponse(BaseModel):
    event: str
    at: datetime
    ip: str | None
    user_agent: str | None


# schemas.py
class CheckoutRequest(BaseModel):
    amount_cents: int = Field(gt=0)

class CheckoutResponse(BaseModel):
    checkout_url: str
