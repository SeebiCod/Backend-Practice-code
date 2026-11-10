"""INFRASTRUCTURE: the UserRepository interface implemented with SQLAlchemy.

Flow: use case -> repository (domain User) -> UserModel row -> PostgreSQL, and back.
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.exceptions import EmailAlreadyRegisteredError
from app.domain.user import Role, User
from app.infrastructure.database import UserModel


def _to_entity(row: UserModel) -> User:
    return User(
        id=row.id,
        email=row.email,
        hashed_password=row.hashed_password,
        role=Role(row.role),
        created_at=row.created_at,
    )


class SqlAlchemyUserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        row = self.db.scalars(select(UserModel).where(UserModel.email == email)).first()
        return _to_entity(row) if row else None

    def get_by_id(self, user_id: int) -> User | None:
        row = self.db.get(UserModel, user_id)
        return _to_entity(row) if row else None

    def add(self, user: User) -> User:
        row = UserModel(email=user.email, hashed_password=user.hashed_password, role=user.role.value)
        self.db.add(row)
        try:
            self.db.commit()
        except IntegrityError as exc:  # two requests registered the same email at once
            self.db.rollback()
            raise EmailAlreadyRegisteredError() from exc
        self.db.refresh(row)  # load the id and created_at set by the database
        return _to_entity(row)

    def update(self, user: User) -> None:
        row = self.db.get(UserModel, user.id)
        row.email = user.email
        row.hashed_password = user.hashed_password
        row.role = user.role.value
        self.db.commit()

    def list_all(self) -> list[User]:
        rows = self.db.scalars(select(UserModel).order_by(UserModel.id))
        return [_to_entity(row) for row in rows]
