"""In-memory stand-ins so tests run without PostgreSQL."""

from datetime import datetime, timezone

from app.domain.auth_event import AuthEvent
from app.domain.exceptions import EmailAlreadyRegisteredError
from app.domain.user import User


class InMemoryUserRepository:
    def __init__(self):
        self.users: dict[int, User] = {}

    def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.users.values() if u.email == email), None)

    def get_by_id(self, user_id: int) -> User | None:
        return self.users.get(user_id)

    def add(self, user: User) -> User:
        if self.get_by_email(user.email):
            raise EmailAlreadyRegisteredError()
        user.id = len(self.users) + 1
        user.created_at = datetime.now(timezone.utc)
        self.users[user.id] = user
        return user

    def update(self, user: User) -> None:
        self.users[user.id] = user

    def list_all(self) -> list[User]:
        return list(self.users.values())


class InMemoryAuthEventRepository:
    """Stands in for MongoDB."""

    def __init__(self):
        self.events: list[AuthEvent] = []

    def record(self, event: AuthEvent) -> None:
        self.events.append(event)

    def list_for_user(self, user_id: int, limit: int) -> list[AuthEvent]:
        mine = [e for e in self.events if e.user_id == user_id]
        return sorted(mine, key=lambda e: e.at, reverse=True)[:limit]


class PlainTextHasher:
    """Fast stand-in for Argon2."""

    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, hashed_password: str) -> bool:
        return hashed_password == f"hashed:{password}"

# tests/fakes.py
class FakePaymentGateway:
    def __init__(self):
        self.calls = []

    def create_checkout(self, user_id, email, amount_cents):
        self.calls.append((user_id, amount_cents))
        return "https://fake-checkout/123"