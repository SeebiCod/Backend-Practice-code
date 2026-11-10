# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Practice project: a small FastAPI authentication API using JWT bearer tokens. Users live in PostgreSQL (SQLAlchemy 2.x + psycopg 3); the login activity log lives in MongoDB (pymongo). It is laid out as a deliberately minimal onion architecture, with one module per concern in each layer. Keep it simple; this is for learning, not production. Python 3.14, virtualenv in `.venv/`.

## Commands

```bash
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload                       # dev server; docs at /docs
pytest                                              # full suite (no database needed)
pytest tests/test_api.py::test_login_and_me         # single test
```

`.env` needs `DATABASE_URL` and `JWT_SECRET_KEY`; `MONGODB_URL` (default `mongodb://localhost:27017`), `MONGODB_DB` and `STRIPE_SECRET_KEY` are optional. Only `app/infrastructure/config.py` reads it. The `users` table and the Mongo indexes are created on startup; there are no migrations.

MongoDB runs in Docker. Use `mongo:8.2` or newer, because `mongo:8.0` refuses to start on the newer Docker VM kernel:

```bash
docker run -d -p 27017:27017 --name mongo -v mongo-data:/data/db mongo:8.2   # first time
docker start mongo                                                           # afterwards
docker exec -it mongo mongosh auth_api                                       # shell
``` Admins are made by setting `users.role = 'admin'` in the database.

## Architecture

`presentation → application → domain`. `infrastructure` implements the `Protocol` interfaces from `domain/repository.py` and `application/interfaces.py`. `domain/` and `application/` must not import FastAPI, Pydantic, SQLAlchemy, PyJWT or pwdlib.

- `domain/`: `user.py` (User entity, Role, `normalize_email`), `auth_event.py` (AuthEvent entity), `repository.py` (UserRepository and AuthEventRepository interfaces), `exceptions.py` (every app error).
- `application/`: `use_cases.py` (one class per action, each with an `execute()` method; `Login` records every attempt), `dtos.py` (commands in, `UserDTO`/`TokenDTO`/`AuthEventDTO` out), `interfaces.py` (PasswordHasher, TokenService, PaymentGateway).
- `infrastructure/`: `config.py`, `database.py` (engine and `UserModel`), `user_repository.py` (commits on each write), `mongo.py` (the only pymongo import: client, `auth_events` collection, `MongoAuthEventRepository`), `security.py` (Argon2 hasher, JWT service), `stripe_gateway.py`.

There are two databases and no shared transaction. PostgreSQL is the source of truth. Writes to the Mongo activity log are best-effort: `MongoAuthEventRepository.record` logs a warning on failure and doesn't block login.
- `presentation/`: `routes.py`, `schemas.py` (Pydantic), `dependencies.py` (the only place concrete classes are chosen; `current_user` guards protected routes), `error_handlers.py` (the `STATUS_CODES` dict maps exceptions to HTTP codes; routes never try/except).

A request flows: Pydantic schema → command DTO built in the route → use case → `UserDTO.from_entity` (drops `hashed_password`) → response schema.

`ChangePassword` in `use_cases.py` is the user's in-progress exercise (TODO steps). Don't implement it unless asked.

## Endpoints

`GET /`, `GET /health/db`, `POST /auth/register`, `POST /auth/login` (returns a JWT), `GET /auth/me`, `GET /auth/me/activity` (recent logins, from MongoDB), `POST /auth/change-password`, `POST /payments/checkout`, `GET /users` (admin only), `GET /health/mongo`. Protected routes need `Authorization: Bearer <token>`.

## Tests

`tests/fakes.py` has in-memory user and auth-event repositories and a plain-text hasher. API tests override `dependencies.get_users` and `dependencies.get_events` and monkeypatch `dependencies.hasher`. They use `TestClient(app)` without `with`, so neither PostgreSQL nor MongoDB is touched (the pymongo client is lazy).
