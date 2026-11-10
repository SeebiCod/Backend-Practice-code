"""INFRASTRUCTURE: password hashing (pwdlib/Argon2) and JWT tokens (PyJWT)."""

from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.infrastructure.config import ACCESS_TOKEN_MINUTES, JWT_ALGORITHM, JWT_SECRET_KEY


class PwdlibPasswordHasher:
    def __init__(self):
        self._hasher = PasswordHash.recommended()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, hashed_password: str) -> bool:
        return self._hasher.verify(password, hashed_password)


class JwtTokenService:
    lifetime_seconds = ACCESS_TOKEN_MINUTES * 60

    def issue(self, user_id: int) -> str:
        now = datetime.now(timezone.utc)
        payload = {"sub": str(user_id), "iat": now, "exp": now + timedelta(seconds=self.lifetime_seconds)}
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    def verify(self, token: str) -> int | None:
        try:
            # Only HS256 is accepted, which blocks "alg: none" style attacks.
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return int(payload["sub"])
        except (jwt.InvalidTokenError, KeyError, ValueError):
            return None
