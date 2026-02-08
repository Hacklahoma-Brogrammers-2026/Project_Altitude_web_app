from fastapi import APIRouter, HTTPException, Query, Request, status
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from services.storage import Person # Keep for backwards compat if needed, but we prefer Contact
from database.models import Contact
from app.core.container import container
from repos import contact_note_repo, contact_repo, user_repo

router = APIRouter()

class PersonUpdate(BaseModel):
    name: str # The frontend sends "name", we need to split it for Contact
    age: int

class UserRegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: EmailStr

def _build_photo_url(request: Request, image_path: Optional[str]) -> Optional[str]:
    if not image_path:
        return None
    if image_path.startswith("http://") or image_path.startswith("https://"):
        return image_path

    clean_path = image_path.replace("\\", "/").split("data/faces/")[-1].lstrip("/")
    base_url = str(request.base_url).rstrip("/")
    return f"{base_url}/images/{clean_path}"

@router.get("/people", response_model=List[Contact])
async def get_people(sort: str = Query("last_modified")):
    """Returns list of all registered people for the current user."""
    print(f"GET /people called with sort={sort}")
    
    current_user = container.face_service.current_user_id
    if not current_user:
        # For now, return empty or raise error? 
        # If we return empty list, frontend just shows nothing.
        print("GET /people: No user logged in.")
        return []

    people = container.storage.get_all(user_id=current_user)

    if sort == "alphabetical":
        # Sort by first check name
        return sorted(people, key=lambda p: (p.first_name + p.last_name).casefold())

    if sort == "last_modified":
        return sorted(people, key=lambda p: p.last_modified, reverse=True)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid sort option",
    )

@router.put("/people/{person_id}")
async def update_person(person_id: str, person: PersonUpdate):
    """Updates a person's name and age."""
    success = container.face_service.update_person_details(person_id, person.name, person.age)
    if success:
        return {"status": "updated", "person_id": person_id}
    return {"status": "error", "message": "Person not found"}

@router.get("/person/{person_id}")
async def get_person(person_id: str, request: Request):
    current_user = container.face_service.current_user_id
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not logged in",
        )

    contact = contact_repo.get_contact_by_id(person_id)
    if not contact or contact.owner_user_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        )

    notes = contact_note_repo.list_contact_notes_for_contact(
        user_id=current_user,
        contact_id=person_id,
    )

    return {
        "contact_id": contact.contact_id,
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "note": contact.note,
        "photo": _build_photo_url(request, contact.image_path),
        "notes": [
            {"label": note.label, "content": note.content}
            for note in notes
        ],
        "last_modified": contact.last_modified,
    }

@router.post("/register", response_model=UserResponse)
async def register(request: UserRegisterRequest):
    try:
        new_user = user_repo.create_user(
            username=request.username,
            email=request.email,
            password=request.password
        )
        saved_user = user_repo.save_user_to_database(new_user)
        return UserResponse(
            user_id=saved_user.user_id,
            username=saved_user.username,
            email=saved_user.email
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=UserResponse)
async def login(request: UserLoginRequest):
    result = user_repo.validate_login(request.email, request.password)
    
    if result.status == "USER_NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if result.status == "PASSWORD_INVALID":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    if result.status == "SUCCESS" and result.user:
        # Update the face service with the logged-in user
        container.face_service.set_current_user(result.user.user_id)
        print(f"LOGIN SUCCESS: FaceService updated with user {result.user.user_id}")
        
        return UserResponse(
            user_id=result.user.user_id,
            username=result.user.username,
            email=result.user.email
        )
    
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unknown login error")