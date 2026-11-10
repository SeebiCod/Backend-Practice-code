"""APPLICATION: plain data passed in and out of use cases (no Pydantic, no entities)."""

from dataclasses import dataclass
from datetime import datetime

from app.domain.auth_event import AuthEvent
from app.domain.user import User


# Inputs (presentation -> use case)

@dataclass(frozen=True)
class RegisterUserCommand:
    email: str
    password: str


@dataclass(frozen=True)
class LoginCommand:
    email: str
    password: str
    ip: str | None = None  # where the request came from; saved in the activity log
    user_agent: str | None = None


@dataclass(frozen=True)
class ChangePasswordCommand:
    user_id: int
    current_password: str
    new_password: str


# Outputs (use case -> presentation)

@dataclass(frozen=True)
class UserDTO:
    id: int
    email: str
    role: str
    created_at: datetime | None

    @classmethod
    def from_entity(cls, user: User) -> "UserDTO":
        """Entity -> DTO. Drops hashed_password so it can never reach a response."""
        return cls(id=user.id, email=user.email, role=user.role.value, created_at=user.created_at)


@dataclass(frozen=True)
class TokenDTO:
    access_token: str
    expires_in: int  # seconds


@dataclass(frozen=True)
class AuthEventDTO:
    event: str
    at: datetime
    ip: str | None
    user_agent: str | None

    @classmethod
    def from_entity(cls, event: AuthEvent) -> "AuthEventDTO":
        """Entity -> DTO. Leaves out `details` (internal info such as the failure reason)."""
        return cls(event=event.event.value, at=event.at, ip=event.ip, user_agent=event.user_agent)

    # app/application/dtos.py
@dataclass(frozen=True)
class CheckoutCommand:
    user_id: int
    amount_cents: int

@dataclass(frozen=True)
class CheckoutDTO:
    checkout_url: str
