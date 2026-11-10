"""DOMAIN: the User entity and its rules. No framework imports allowed here."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"


def normalize_email(email: str) -> str:
    """Rule: emails are case-insensitive, so " Bob@X.com" and "bob@x.com" are the same account."""
    return email.strip().lower()


@dataclass
class User:
    email: str
    hashed_password: str
    role: Role = Role.USER
    id: int | None = None  # assigned by the database on save
    created_at: datetime | None = None

    @classmethod
    def register(cls, email: str, hashed_password: str) -> "User":
        """Factory for new accounts. Rule: nobody can sign up as an admin."""
        return cls(email=normalize_email(email), hashed_password=hashed_password)

    @property
    def is_admin(self) -> bool:
        return self.role is Role.ADMIN

    def change_password(self, new_hashed_password: str) -> None:
        self.hashed_password = new_hashed_password
