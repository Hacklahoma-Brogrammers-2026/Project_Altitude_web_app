import uuid
from backend.repos.user_repo import get_user_by_user_id
from database.models import Contact, User
from database.db import get_db_collections
from pymongo.errors import DuplicateKeyError

def create_contact(owner_user_id: str, first_name:str = "unknown user", last_name: str = "unknown user") -> Contact:
    if get_user_by_user_id(owner_user_id) is None:
        raise RuntimeError("Invalid User ID: User ID not in database")

    contact_id = str(uuid.uuid4())
    return Contact(
        contact_id=contact_id,
        owner_user_id=owner_user_id,
        first_name=first_name,
        last_name=last_name,
    )

def save_contact_to_database(contact: Contact) -> Contact:
    contacts = get_db_collections().contacts
    doc = contact.model_dump()
    try:
        contacts.insert_one(doc)
    except DuplicateKeyError as e:
        raise ValueError("Contact with this username or email already exists")

    return contact

def update_contact(contact: Contact) -> Contact:
    updates = contact.model_dump()
    updates.pop("contact_id")

    contacts = get_db_collections().contacts
    result = contacts.find_one_and_update(
        filter={"contact_id": contact.contact_id},
        update={"$set": updates},
        return_document=True,
        projection={"_id": 0}
    )

    if result is None:
        raise ValueError("Contact was not found")
    return Contact(**result)

from typing import List

def get_all_contacts_for_user(user_id: str) -> List[Contact]:
    contacts = get_db_collections().contacts
    cursor = contacts.find({"owner_user_id": user_id}, {"_id": 0})
    return [Contact(**doc) for doc in cursor]

def get_contact_by_id(contact_id: str) -> Contact | None:
    contacts = get_db_collections().contacts
    doc = contacts.find_one({"contact_id": contact_id}, {"_id": 0})
    if doc:
        return Contact(**doc)
    return None