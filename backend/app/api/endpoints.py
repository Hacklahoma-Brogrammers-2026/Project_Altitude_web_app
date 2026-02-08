from pathlib import Path
import shutil
import uuid
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, Query, Request, status, UploadFile, File, Form
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from backend.services.audio_embedding_service import AUDIO_FILE_DIR
from backend.services.audio_transcription_service import process_audio
from backend.services.note_taker_service import take_notes
import subprocess
import os
from services.storage import Person # Keep for backwards compat if needed, but we prefer Contact
from database.models import Contact
from app.core.container import container
from repos import contact_note_repo, contact_repo, user_repo
from pathlib import Path

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

@router.get("/")
def hello_world():
    return "hello_world"

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

@router.get("/profile/{person_id}/search")
async def search_person_notes(person_id: str, q: str):
    """
    Search within a single profile (contact notes).
    """
    current_user = container.face_service.current_user_id
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not logged in",
        )

    # 1. Verify existence/ownership
    contact = contact_repo.get_contact_by_id(person_id)
    if not contact or contact.owner_user_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        )

    # 2. Semantic search scoped to this contact_id
    note_results = contact_note_repo.semantic_search_notes(
        user_id=current_user,
        query=q,
        limit=20,
        contact_id=person_id
    )

    # 3. Format response
    results = []
    for item in note_results:
        note = item.note
        results.append({
            "label": note.label,
            "content": note.content
        })

    return {"results": results}


@router.get("/searchUser")
async def search_user(q: str, request: Request):
    """
    Search people by name.
    """
    current_user = container.face_service.current_user_id
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not logged in",
        )
    
    contacts = contact_repo.search_contacts_by_name(current_user, q)
    
    results = []
    for contact in contacts:
        results.append({
            "id": contact.contact_id,
            "name": f"{contact.first_name} {contact.last_name}",
            "avatar": _build_photo_url(request, contact.image_path)
        })
        
    return {"results": results}


@router.get("/searchInfo")
async def search_info(q: str, request: Request):
    """
    Semantic search based on context labels/notes.
    """
    current_user = container.face_service.current_user_id
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not logged in",
        )
        
    # Search notes
    note_results = contact_note_repo.semantic_search_notes(
        user_id=current_user,
        query=q,
        limit=20 # Fetch a few more to filter if needed
    )
    
    search_results = []
    seen_notes = set()

    for item in note_results:
        note = item.note
        if note.note_id in seen_notes:
            continue
        seen_notes.add(note.note_id)

        # Get associated contact
        contact = contact_repo.get_contact_by_id(note.contact_id)
        if not contact:
            continue
            
        search_results.append({
            "id": contact.contact_id,
            "name": f"{contact.first_name} {contact.last_name}",
            "avatar": _build_photo_url(request, contact.image_path),
            "label": note.label,
            "content": note.content
        })
        
    return {"results": search_results}


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

@router.post("/uploadAudio")
async def upload_audio(
    user_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Upload an audio sample for a user/person.
    Saves and converts the incoming WebM/Ogg audio to a standard WAV file using ffmpeg.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file sent")

    # Ensure backend/data/audio exists
    audio_dir = Path("data/audio")
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    # Paths
    temp_filename = f"temp_{user_id}.webm"
    final_filename = f"{user_id}.wav"
    
    temp_path = audio_dir / temp_filename
    final_path = audio_dir / final_filename
    
    try:
        # 1. Save the incoming stream to a temporary file
        with open(temp_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)
        
        # 2. Convert to WAV using ffmpeg
        # -i: input file
        # -y: overwrite output file if it exists
        # -ac 1: convert to mono (optional, but good for standardization)
        # -ar 16000: set sample rate to 16kHz (optional, standard for ML)
        command = [
            "ffmpeg", 
            "-i", str(temp_path),
            "-y", 
            "-ac", "1",
            "-ar", "16000",
            str(final_path)
        ]
        
        process = subprocess.run(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )

        if process.returncode != 0:
            print(f"FFmpeg error: {process.stderr}")
            raise RuntimeError("FFmpeg conversion failed")

        # 3. Clean up temp file
        if temp_path.exists():
            temp_path.unlink()
                
        return {"message": "Audio uploaded and converted successfully", "url": f"/audio/{final_filename}"}

    except Exception as e:
        print(f"Error saving audio: {e}")
        # Clean up on error
        if 'temp_path' in locals() and temp_path.exists():
            temp_path.unlink()
            
        raise HTTPException(status_code=500, detail=f"Could not save and convert audio file: {str(e)}")

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
        # Update the face service with the logged-in user
        container.face_service.set_current_user(result.user.user_id)
        print(f"LOGIN SUCCESS: FaceService updated with user {result.user.user_id}")
        
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

