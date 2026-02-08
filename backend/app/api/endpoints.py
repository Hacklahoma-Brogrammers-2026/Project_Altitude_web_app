from fastapi import APIRouter
from typing import List
from pydantic import BaseModel
from services.storage import Person
from app.core.container import container

router = APIRouter()

class PersonUpdate(BaseModel):
    name: str
    age: int

@router.get("/people", response_model=List[Person])
async def get_people():
    """Returns list of all registered people."""
    return container.storage.get_all()

@router.put("/people/{person_id}")
async def update_person(person_id: str, person: PersonUpdate):
    """Updates a person's name and age."""
    success = container.face_service.update_person_details(person_id, person.name, person.age)
    if success:
        return {"status": "updated", "person_id": person_id}
    return {"status": "error", "message": "Person not found"}