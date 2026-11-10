"""DOMAIN: an entry in the auth activity log (stored in MongoDB). No framework imports allowed here."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class AuthEventType(str, Enum):
    LOGIN_SUCCEEDED = "login_succeeded"
    LOGIN_FAILED = "login_failed"


@dataclass
class AuthEvent:
    event: AuthEventType
    email: str
    user_id: int | None = None  # None when the email doesn't belong to any account
    ip: str | None = None
    user_agent: str | None = None
    details: dict = field(default_factory=dict)  # free-form: each event type can store different fields
    at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
