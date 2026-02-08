from typing import Literal

from database.models import User
from pymongo.errors import DuplicateKeyError
from pydantic import BaseModel, EmailStr
from utils.password_util import hash_password, verify_password
import uuid
from database.db import get_db_collections

class ValidatedLoginResponse(BaseModel):
    status: Literal["USER_NOT_FOUND", "PASSWORD_INVALID", "SUCCESS"]
    user: User | None = None
    
def create_user(username: str, email: EmailStr, password: str):
    password_hash = hash_password(password)
    user_id = str(uuid.uuid4())
    return User(
        user_id=user_id,
        username=username,
        email=email,
        password_hash=password_hash
    )

def update_user(user: User) -> User:
    updates = user.model_dump()
    updates.pop("user_id", None)

    users = get_db_collections().users
    result = users.find_one_and_update(
        {"user_id": user.user_id},
        {"$set": updates},
        return_document=True,
        projection={"_id": 0}
    )

    if result is None:
        raise ValueError("User was not found")

    return User(**result)
    


def validate_login(username: str, password: str) -> ValidatedLoginResponse:
    user = get_user_by_username(username)
    if user is None:
        return ValidatedLoginResponse(status="USER_NOT_FOUND")

    if not verify_password(password, user.password_hash):
        return ValidatedLoginResponse(status="PASSWORD_INVALID")

    return ValidatedLoginResponse(status="SUCCESS", user=user) 
    

def get_user_by_username(username: str) -> User | None:
    users = get_db_collections().users
    doc = users.find_one(
        {"username": username},
        {"_id": 0}
    )

    if doc is None:
        return None
    return User(**doc)

def get_user_by_user_id(user_id: str) -> User | None:
    users = get_db_collections().users
    doc = users.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )

    if doc is None:
        return None
    return User(**doc)

def save_user_to_database(user: User):
    users = get_db_collections().users
    doc = user.model_dump()

    try:
        users.insert_one(doc)
    except DuplicateKeyError as e:
        raise ValueError("User with this username or email already exists") from e

    return user


