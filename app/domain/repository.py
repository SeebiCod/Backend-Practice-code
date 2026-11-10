"""DOMAIN: what the app needs from storage.

UserRepository is implemented in infrastructure/user_repository.py (PostgreSQL),
AuthEventRepository in infrastructure/mongo.py (MongoDB).
"""

from typing import Protocol

from app.domain.auth_event import AuthEvent
from app.domain.user import User


class UserRepository(Protocol):
    def get_by_email(self, email: str) -> User | None: ...

    def get_by_id(self, user_id: int) -> User | None: ...

    def add(self, user: User) -> User:
        """Save a new user and return it with `id` set. Raises EmailAlreadyRegisteredError."""
        ...

    def update(self, user: User) -> None:
        """Save changes to an existing user."""
        ...

    def list_all(self) -> list[User]: ...


class AuthEventRepository(Protocol):
    def record(self, event: AuthEvent) -> None:
        """Append an event to the activity log."""
        ...

    def list_for_user(self, user_id: int, limit: int) -> list[AuthEvent]:
        """Newest first."""
        ...
