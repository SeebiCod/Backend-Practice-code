# Backend-Practice-code

A practice FastAPI authentication API built with an onion (clean) architecture.

- **JWT** bearer-token auth (register, login, `/auth/me`, admin-only `/users`)
- **PostgreSQL** (SQLAlchemy) stores users
- **MongoDB** (pymongo) stores a login activity log (`/auth/me/activity`)
- **Stripe** checkout (test mode)
- Layers: `domain` → `application` (use cases + DTOs) → `infrastructure` (adapters) / `presentation` (FastAPI)

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in your values
docker run -d -p 127.0.0.1:27017:27017 --name mongo -v mongo-data:/data/db mongo:8.2
uvicorn app.main:app --reload # docs at http://localhost:8000/docs
```

## Tests

```bash
pytest   # uses in-memory fakes, so no database is needed
```
