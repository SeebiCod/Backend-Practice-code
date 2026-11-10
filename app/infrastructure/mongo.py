"""INFRASTRUCTURE: MongoDB connection and the auth activity log. The only module that imports pymongo.

PostgreSQL (database.py) holds the users. MongoDB holds `auth_events`: one document per login
attempt. It's append-only, high-volume and free-form (`details` can differ per event type).
"""

import logging

from pymongo import DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.domain.auth_event import AuthEvent, AuthEventType
from app.infrastructure.config import MONGODB_DB, MONGODB_URL

logger = logging.getLogger(__name__)

# MongoClient is lazy: it only connects on the first real operation, so importing this
# module (e.g. in tests) never needs a running MongoDB. tz_aware=True gives back UTC datetimes.
client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=2000, tz_aware=True)
auth_events: Collection = client[MONGODB_DB]["auth_events"]


def create_indexes() -> None:
    """Called on startup. Makes "this user's newest events" fast. Mongo's version of create_all."""
    auth_events.create_index([("user_id", 1), ("at", DESCENDING)])


def check_mongo_connection() -> None:
    client.admin.command("ping")


def _to_entity(doc: dict) -> AuthEvent:
    return AuthEvent(
        event=AuthEventType(doc["event"]),
        email=doc["email"],
        user_id=doc.get("user_id"),
        ip=doc.get("ip"),
        user_agent=doc.get("user_agent"),
        details=doc.get("details", {}),
        at=doc["at"],
    )


class MongoAuthEventRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def record(self, event: AuthEvent) -> None:
        document = {
            "event": event.event.value,
            "email": event.email,
            "user_id": event.user_id,
            "ip": event.ip,
            "user_agent": event.user_agent,
            "details": event.details,
            "at": event.at,
        }
        try:
            self.collection.insert_one(document)
        except PyMongoError:
            # Best effort: the activity log is not the source of truth, so a MongoDB outage
            # must not stop people logging in. Users live in PostgreSQL.
            logger.warning("Could not record auth event %s", event.event.value, exc_info=True)

    def list_for_user(self, user_id: int, limit: int) -> list[AuthEvent]:
        cursor = self.collection.find({"user_id": user_id}).sort("at", DESCENDING).limit(limit)
        return [_to_entity(doc) for doc in cursor]
