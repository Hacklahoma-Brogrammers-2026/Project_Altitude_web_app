import uuid
from datetime import datetime, timezone
from typing import Literal, Optional
from pymongo.errors import DuplicateKeyError
from pydantic import BaseModel
from database.models import ContactNote
from database.db import get_db_collections
from backend.repos.user_repo import get_user_by_user_id
from services.vector_embedding_service import get_vector_embedding


class NoteSearchResult(BaseModel):
    note: ContactNote
    score: float


def create_contact_note(
    user_id: str,
    contact_id: str,
    label: str,
    content: str,
) -> ContactNote:
    if get_user_by_user_id(user_id) is None:
        raise RuntimeError("Invalid user_id: user not found")

    note_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    embedding = get_vector_embedding(f"Label: {label}\nContent: {content}")

    return ContactNote(
        note_id=note_id,
        user_id=user_id,
        contact_id=contact_id,
        label=label,
        content=content,
        last_modified=now,
        embedding=embedding,
    )


def save_contact_note_to_database(note: ContactNote) -> ContactNote:
    contact_notes = get_db_collections().contact_notes
    doc = note.model_dump()

    try:
        contact_notes.insert_one(doc)
    except DuplicateKeyError as e:
        raise ValueError("ContactNote with this note_id already exists") from e

    return note


def get_contact_note_by_id(note_id: str) -> ContactNote | None:
    contact_notes = get_db_collections().contact_notes
    doc = contact_notes.find_one({"note_id": note_id}, {"_id": 0})
    return ContactNote(**doc) if doc else None


def list_contact_notes_for_contact(
    user_id: str,
    contact_id: str,
    limit: int = 100,
    skip: int = 0,
) -> list[ContactNote]:
    contact_notes = get_db_collections().contact_notes

    cursor = (
        contact_notes.find(
            {"user_id": user_id, "contact_id": contact_id},
            {"_id": 0},
        )
        .sort("last_modified", -1)
        .skip(skip)
        .limit(limit)
    )

    return [ContactNote(**d) for d in cursor]


def list_contact_notes_for_user(
    user_id: str,
    limit: int = 50,
    skip: int = 0,
) -> list[ContactNote]:
    """
    List notes for a given user across all contacts.
    """
    contact_notes = get_db_collections().contact_notes

    cursor = (
        contact_notes.find({"user_id": user_id}, {"_id": 0})
        .sort("last_modified", -1)
        .skip(skip)
        .limit(limit)
    )

    return [ContactNote(**d) for d in cursor]


def update_contact_note(note: ContactNote) -> ContactNote:
    updates = note.model_dump()
    updates.pop("note_id", None)

    updates["last_modified"] = datetime.now(timezone.utc)

    contact_notes = get_db_collections().contact_notes
    result = contact_notes.find_one_and_update(
        {"note_id": note.note_id},
        {"$set": updates},
        return_document=True,
        projection={"_id": 0},
    )

    if result is None:
        raise ValueError("ContactNote was not found")

    return ContactNote(**result)

def delete_contact_note(note_id: str) -> bool:
    contact_notes = get_db_collections().contact_notes
    res = contact_notes.delete_one({"note_id": note_id})
    return res.deleted_count == 1


def semantic_search_notes(
    user_id: str,
    query: str,
    limit: int = 10,
    num_candidates: int = 200,
    contact_id: str | None = None,
    label: str | None = None,
) -> list[NoteSearchResult]:
    """
    Semantic search notes using $vectorSearch.
    Scopes results to a user, and optionally to a contact or label.
    Requires:
      - vector index name: 'contact_note_vector_index'
      - index includes filter fields: user_id, contact_id
    """
    contact_notes = get_db_collections().contact_notes

    query_vector = get_vector_embedding(query)
    

    filt: dict = {"user_id": {"$eq": user_id}}
    if contact_id is not None:
        filt["contact_id"] = {"$eq": contact_id}
    if label is not None:
        # NOTE: for this to be in $vectorSearch.filter efficiently,
        # add {"type":"filter","path":"label"} to the search index definition.
        # Otherwise, you can post-filter after vectorSearch.
        filt["label"] = {"$eq": label}

    pipeline = [
        {
            "$vectorSearch": {
                "index": "contact_note_vector_index",
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": num_candidates,
                "limit": limit,
                "filter": filt,
            }
        },
        {
            "$project": {
                "_id": 0,
                "note_id": 1,
                "user_id": 1,
                "contact_id": 1,
                "label": 1,
                "content": 1,
                "last_modified": 1,
                "embedding": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]

    out: list[NoteSearchResult] = []
    for d in contact_notes.aggregate(pipeline):
        score = float(d.pop("score"))
        out.append(NoteSearchResult(note=ContactNote(**d), score=score))
    return out
