"""APPLICATION: one class per action. Each takes a command DTO and returns a result DTO.

Use cases only know the interfaces (UserRepository, AuthEventRepository, PasswordHasher, ...);
the real implementations are plugged in by presentation/dependencies.py. A use case never
knows whether data lives in PostgreSQL or MongoDB.
"""

from app.application.dtos import (
    AuthEventDTO,
    ChangePasswordCommand,
    CheckoutCommand,
    CheckoutDTO,
    LoginCommand,
    RegisterUserCommand,
    TokenDTO,
    UserDTO,
)
from app.application.interfaces import PasswordHasher, PaymentGateway, TokenService
from app.domain.auth_event import AuthEvent, AuthEventType
from app.domain.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidTokenError,
    PermissionDeniedError,
)
from app.domain.repository import AuthEventRepository, UserRepository
from app.domain.user import User, normalize_email


class RegisterUser:
    def __init__(self, users: UserRepository, hasher: PasswordHasher):
        self.users = users
        self.hasher = hasher

    def execute(self, command: RegisterUserCommand) -> UserDTO:
        if self.users.get_by_email(normalize_email(command.email)):
            raise EmailAlreadyRegisteredError()

        user = User.register(command.email, self.hasher.hash(command.password))
        return UserDTO.from_entity(self.users.add(user))


class Login:
    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        tokens: TokenService,
        events: AuthEventRepository,
    ):
        self.users = users  # PostgreSQL
        self.hasher = hasher
        self.tokens = tokens
        self.events = events  # MongoDB

    def execute(self, command: LoginCommand) -> TokenDTO:
        email = normalize_email(command.email)
        user = self.users.get_by_email(email)

        if user is None or not self.hasher.verify(command.password, user.hashed_password):
            reason = "unknown_email" if user is None else "wrong_password"
            self._record(command, AuthEventType.LOGIN_FAILED, email, user, {"reason": reason})
            raise InvalidCredentialsError()  # the client still gets the same message either way

        self._record(command, AuthEventType.LOGIN_SUCCEEDED, email, user)
        return TokenDTO(
            access_token=self.tokens.issue(user.id),
            expires_in=self.tokens.lifetime_seconds,
        )

    def _record(self, command, event_type, email, user, details=None) -> None:
        self.events.record(
            AuthEvent(
                event=event_type,
                email=email,
                user_id=user.id if user else None,
                ip=command.ip,
                user_agent=command.user_agent,
                details=details or {},
            )
        )


class GetMyActivity:
    """The logged-in user's recent login attempts, newest first (read from MongoDB)."""

    def __init__(self, events: AuthEventRepository):
        self.events = events

    def execute(self, user_id: int, limit: int = 20) -> list[AuthEventDTO]:
        return [AuthEventDTO.from_entity(e) for e in self.events.list_for_user(user_id, limit)]


class GetCurrentUser:
    """Token from the Authorization header -> the user it belongs to."""

    def __init__(self, users: UserRepository, tokens: TokenService):
        self.users = users
        self.tokens = tokens

    def execute(self, token: str | None) -> UserDTO:
        if not token:
            raise InvalidTokenError("Missing bearer token")

        user_id = self.tokens.verify(token)
        user = self.users.get_by_id(user_id) if user_id else None
        if user is None:
            raise InvalidTokenError("Invalid or expired token")

        return UserDTO.from_entity(user)


class ListUsers:
    def __init__(self, users: UserRepository):
        self.users = users

    def execute(self, requester_id: int) -> list[UserDTO]:
        # Re-read the requester so the check uses their current role in the DB.
        requester = self.users.get_by_id(requester_id)
        if requester is None or not requester.is_admin:
            raise PermissionDeniedError("Admin access required")

        return [UserDTO.from_entity(user) for user in self.users.list_all()]


class ChangePassword:
    def __init__(self, users: UserRepository, hasher: PasswordHasher):
        ...

    def execute(self, command: ChangePasswordCommand) -> None:
        # 1. load the user by id (raise InvalidTokenError if missing)
        # 2. verify current password -> IncorrectCurrentPasswordError
        # 3. if new password also verifies against the current hash -> PasswordUnchangedError
        # 4. hash the new password, call user.change_password(...)
        # 5. users.update(user)  <- saves the change
        pass  # TODO: implement this use case

# app/application/use_cases.py
class StartCheckout:
    def __init__(self, users: UserRepository, payments: PaymentGateway):
        self.users = users
        self.payments = payments

    def execute(self, command: CheckoutCommand) -> CheckoutDTO:
        user = self.users.get_by_id(command.user_id)
        if user is None:
            raise InvalidTokenError("Invalid or expired token")
        url = self.payments.create_checkout(user.id, user.email, command.amount_cents)
        return CheckoutDTO(checkout_url=url)