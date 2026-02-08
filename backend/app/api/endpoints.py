from pathlib import Path
import shutil
import uuid
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, status
from typing import List
from pydantic import BaseModel, EmailStr
from backend.services.audio_embedding_service import AUDIO_FILE_DIR
from backend.services.audio_transcription_service import process_audio
from backend.services.note_taker_service import take_notes
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
        with open("./backend/most_recent_login_id.txt", "w") as f:
            f.write(result.user.user_id)
        return UserResponse(
            user_id=result.user.user_id,
            username=result.user.username,
            email=result.user.email
        )
    
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unknown login error")

@router.post("/process-audio")
async def analyze_audio(audio: UploadFile = File(...), contact_id: str = "", background: BackgroundTasks = BackgroundTasks()):
    if audio.filename is None:
        raise HTTPException(
            status_code=400,
            detail="audio file must have a file name"
        )
    ext = Path(audio.filename).suffix.lower()
    if ext not in [".wav"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Needs to be one of {[".wav"]}"
        )

    file_id = uuid.uuid4().hex
    dest_path = Path(f"{AUDIO_FILE_DIR}/{file_id}{ext}")

    try:
        with dest_path.open("wb") as f:
            shutil.copyfileobj(audio.file, f)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {e}"
        )

    with open("./backend/most_recent_login_id.txt", 'r') as f:
        user_id = f.readline()
    background.add_task(take_notes, str(dest_path), user_id, contact_id)

    return 

