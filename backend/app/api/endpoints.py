from fastapi import APIRouter, HTTPException, status
from typing import List
from pydantic import BaseModel, EmailStr
from services.storage import Person
from app.core.container import container
from repos import user_repo

router = APIRouter()

class PersonUpdate(BaseModel):
    name: str
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