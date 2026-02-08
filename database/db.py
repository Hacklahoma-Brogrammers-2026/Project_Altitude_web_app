from pymongo import MongoClient
from pymongo.database import Database

_client: MongoClient | None = None
_db: Database | None = None

def init_db(mongo_uri: str, db_name: str) -> None:
    global _client, _db
    if _client is None:
        _client = MongoClient(mongo_uri)
        _db = _client[db_name]

def get_db() -> Database:
    if _db is None:
        raise RuntimeError("DB not initialized. Call init_db() on startup.")
    return _db

def close_db() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None