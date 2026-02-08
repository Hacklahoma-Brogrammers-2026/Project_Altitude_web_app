from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timezone


class User(BaseModel):
    user_id: str
    username: str
    email: EmailStr
    password_hash: str

    audio_sample_path: str | None = None

class ContactNote(BaseModel):
    note_id: str
    user_id: str
    contact_id: str

    label: str
    content: str

    last_modified: datetime

    embedding: list[float] | None = None



class Contact(BaseModel):
    contact_id: str
    owner_user_id: str

    first_name: str = "Unknown First Name"
    last_name: str = "Unknown Last Name"

    note: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Unified fields for Face Recognition
    age: int | None = None
    image_path: str | None = None
    encoding: list[float] | None = None
    last_modified: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def name(self) -> str:
        # Helper to maintain compatibility definition of 'name'
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def id(self) -> str:
        # Helper for compatibility with old Person.id
        return self.contact_id