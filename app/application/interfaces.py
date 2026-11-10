"""APPLICATION: services the use cases need. Implemented in infrastructure/security.py."""

from typing import Protocol


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password: str, hashed_password: str) -> bool: ...


class TokenService(Protocol):
    lifetime_seconds: int

    def issue(self, user_id: int) -> str: ...

    def verify(self, token: str) -> int | None:
        """Return the user id inside a valid token, or None."""
        ...

class PaymentGateway(Protocol):
    def create_checkout(self, user_id: int, email: str, amount_cents: int) -> str:
        """Start a payment and return the URL the user should be sent to."""
        ...