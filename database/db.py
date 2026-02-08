from typing import Any
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.synchronous.collection import Collection

class DbCollections(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    users: Collection[Any]
    contact_notes: Collection[Any]
    contacts: Collection[Any]

_client: MongoClient | None = None
_db_collections: DbCollections | None = None
_db: Database | None = None

def init_db(mongo_uri: str, db_name: str) -> None:
    global _client, _db_collections, _db
    if _client is None:
        _client = MongoClient(mongo_uri)
        _db = _client[db_name]
        users = _db["users"]
        contacts = _db["contacts"]
        contact_notes = _db["contact_notes"]
        _db_collections = DbCollections(
            users=users,
            contacts=contacts,
            contact_notes=contact_notes
        )

def get_db_collections() -> DbCollections:
    if _db_collections is None:
        raise RuntimeError("DB not initialized. Call init_db() on startup.")
    return _db_collections

def close_db() -> None:
    global _client, _db_collections
    if _client is not None:
        _client.close()
    _client = None
    _db = None
    _db_collections = None