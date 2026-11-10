import pytest

from app.application.dtos import LoginCommand, RegisterUserCommand
from app.application.use_cases import GetCurrentUser, GetMyActivity, ListUsers, Login, RegisterUser
from app.domain.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidTokenError,
    PermissionDeniedError,
)
from app.domain.auth_event import AuthEventType
from app.domain.user import Role
from app.infrastructure.security import JwtTokenService
from tests.fakes import InMemoryAuthEventRepository, InMemoryUserRepository, PlainTextHasher

PASSWORD = "CorrectHorse123"


@pytest.fixture
def users():
    return InMemoryUserRepository()


@pytest.fixture
def events():
    return InMemoryAuthEventRepository()


def register(users, email="bob@example.com"):
    return RegisterUser(users, PlainTextHasher()).execute(RegisterUserCommand(email, PASSWORD))


def test_register_returns_dto_without_password_hash(users):
    dto = register(users, "Bob@Example.com")
    assert dto.email == "bob@example.com"
    assert not hasattr(dto, "hashed_password")


def test_register_rejects_duplicate_email(users):
    register(users)
    with pytest.raises(EmailAlreadyRegisteredError):
        register(users, "BOB@example.com")


def test_login_token_identifies_the_user(users, events):
    tokens = JwtTokenService()
    user = register(users)

    token = Login(users, PlainTextHasher(), tokens, events).execute(LoginCommand("bob@example.com", PASSWORD))

    assert GetCurrentUser(users, tokens).execute(token.access_token).id == user.id


@pytest.mark.parametrize("email,password", [("bob@example.com", "wrong"), ("nobody@example.com", PASSWORD)])
def test_login_failures_look_the_same(users, events, email, password):
    register(users)
    with pytest.raises(InvalidCredentialsError, match="Invalid email or password"):
        Login(users, PlainTextHasher(), JwtTokenService(), events).execute(LoginCommand(email, password))
    assert events.events[-1].event is AuthEventType.LOGIN_FAILED


@pytest.mark.parametrize("token", [None, "", "garbage"])
def test_bad_tokens_are_rejected(users, token):
    with pytest.raises(InvalidTokenError):
        GetCurrentUser(users, JwtTokenService()).execute(token)


def test_list_users_requires_admin(users):
    normal = register(users, "u@example.com")
    admin = register(users, "admin@example.com")
    users.users[admin.id].role = Role.ADMIN

    with pytest.raises(PermissionDeniedError):
        ListUsers(users).execute(normal.id)
    assert len(ListUsers(users).execute(admin.id)) == 2


def test_login_attempts_are_logged_and_listed_newest_first(users, events):
    user = register(users)
    login = Login(users, PlainTextHasher(), JwtTokenService(), events)

    with pytest.raises(InvalidCredentialsError):
        login.execute(LoginCommand("bob@example.com", "wrong", ip="1.2.3.4"))
    login.execute(LoginCommand("bob@example.com", PASSWORD, ip="1.2.3.4", user_agent="pytest"))

    assert events.events[0].details == {"reason": "wrong_password"}
    activity = GetMyActivity(events).execute(user.id)
    assert [a.event for a in activity] == ["login_succeeded", "login_failed"]
    assert activity[0].ip == "1.2.3.4"
    assert not hasattr(activity[0], "details")  # internal reason never leaves the use case


def test_unknown_email_is_logged_without_a_user(users, events):
    with pytest.raises(InvalidCredentialsError):
        Login(users, PlainTextHasher(), JwtTokenService(), events).execute(LoginCommand("ghost@example.com", "x"))
    assert events.events[0].user_id is None
    assert events.events[0].details == {"reason": "unknown_email"}
