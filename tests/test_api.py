"""HTTP tests with the database swapped for an in-memory repository.

TestClient is used without `with`, so the startup hook never touches PostgreSQL.
"""

import pytest
from fastapi.testclient import TestClient

from app.domain.user import Role
from app.main import app
from app.presentation import dependencies
from tests.fakes import InMemoryAuthEventRepository, InMemoryUserRepository, PlainTextHasher

PASSWORD = "CorrectHorse123"


@pytest.fixture
def users(monkeypatch):
    repo = InMemoryUserRepository()
    events = InMemoryAuthEventRepository()  # MongoDB is swapped out too
    app.dependency_overrides[dependencies.get_users] = lambda: repo
    app.dependency_overrides[dependencies.get_events] = lambda: events
    monkeypatch.setattr(dependencies, "hasher", PlainTextHasher())
    yield repo
    app.dependency_overrides.clear()


@pytest.fixture
def client(users):
    return TestClient(app)


def signup_and_login(client, email="carol@example.com"):
    client.post("/auth/register", json={"email": email, "password": PASSWORD})
    token = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()
    return {"Authorization": f"Bearer {token['access_token']}"}


def test_register_then_duplicate(client):
    body = {"email": "carol@example.com", "password": PASSWORD}
    first = client.post("/auth/register", json=body)
    assert first.status_code == 201
    assert set(first.json()) == {"id", "email", "role", "created_at"}
    assert client.post("/auth/register", json=body).status_code == 409


def test_register_validates_password_length(client):
    response = client.post("/auth/register", json={"email": "x@example.com", "password": "short"})
    assert response.status_code == 422


def test_login_and_me(client):
    headers = signup_and_login(client)
    assert client.get("/auth/me", headers=headers).json()["email"] == "carol@example.com"


def test_me_rejects_missing_and_bad_tokens(client):
    assert client.get("/auth/me").status_code == 401
    bad = client.get("/auth/me", headers={"Authorization": "Bearer garbage"})
    assert bad.status_code == 401
    assert bad.headers["www-authenticate"] == "Bearer"


def test_bad_login_is_401(client):
    signup_and_login(client)
    response = client.post("/auth/login", json={"email": "carol@example.com", "password": "nope"})
    assert response.status_code == 401


def test_users_endpoint_is_admin_only(client, users):
    headers = signup_and_login(client)
    assert client.get("/users", headers=headers).status_code == 403

    users.get_by_email("carol@example.com").role = Role.ADMIN
    assert client.get("/users", headers=headers).status_code == 200


def test_my_activity_lists_login_attempts(client):
    headers = signup_and_login(client)
    client.post("/auth/login", json={"email": "carol@example.com", "password": "wrong"})

    activity = client.get("/auth/me/activity", headers=headers).json()

    assert [a["event"] for a in activity] == ["login_failed", "login_succeeded"]
    assert set(activity[0]) == {"event", "at", "ip", "user_agent"}
    assert client.get("/auth/me/activity").status_code == 401
