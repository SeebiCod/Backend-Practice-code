"""Entry point: `uvicorn app.main:app --reload`.

Layers (arrows = "depends on"):
    presentation -> application -> domain
    infrastructure implements the interfaces declared in domain/application.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure.database import Base, engine
from app.infrastructure.mongo import create_indexes
from app.presentation.error_handlers import register_error_handlers
from app.presentation.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # PostgreSQL: create the users table if missing
    create_indexes()  # MongoDB: collections appear on first insert; only indexes need creating
    yield


app = FastAPI(title="Authentication API", lifespan=lifespan)
app.include_router(router)
register_error_handlers(app)
