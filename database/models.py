from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timezone


class User(BaseModel):
    user_id: str
    username: str
    email: EmailStr
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ContactNote(BaseModel):
    note_id: str
    user_id: str
    contact_id: str

    label: str
    content: str

    embedding: list[float] | None = None



class Contact(BaseModel):
    contact_id: str
    owner_user_id: str

    first_name: str = "Unknown First Name"
    last_name: str = "Unknown Last Name"

    note: str | None = None