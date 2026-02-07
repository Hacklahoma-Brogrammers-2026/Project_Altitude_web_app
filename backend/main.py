from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware  # <-- Import this
import uvicorn
import cv2
import numpy as np
from typing import Dict, List
import os

# Import our new service
from services.face_recognition import FaceService
from services.storage import JsonPersonRepository, Person

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# --- FIXED INITIALIZATION ---
# 1. Create the storage backend
storage = JsonPersonRepository(data_file="data/people.json")

# 2. Inject storage into FaceService
# We no longer pass 'known_faces_dir' because the service now manages its own folders
face_service = FaceService(storage=storage)

# 2. MOUNT IMAGES: This lets the browser load photos from http://localhost:8000/images/
os.makedirs("data/faces", exist_ok=True)
app.mount("/images", StaticFiles(directory="data/faces"), name="images")

@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Face Recognition API is running"}

@app.websocket("/ws/video-stream")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    print("Video Stream Connected")
    
    try:
        while True:
            # 1. Receive
            data = await websocket.receive_bytes()
            nparr = np.frombuffer(data, np.uint8)
            
            # 2. Decode
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                continue
            
            # 3. Process
            processed_frame = face_service.process_frame(frame)

            # 4. Display (Optional server-side view)
            cv2.imshow("Server Feed", processed_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break

            await websocket.send_text("ack")
            
    except WebSocketDisconnect:
        print("Video Stream Disconnected")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cv2.destroyAllWindows()
        try:
            await websocket.close()
        except RuntimeError:
            pass

# Add an endpoint to update people since we have the logic now
from pydantic import BaseModel

class PersonUpdate(BaseModel):
    name: str
    age: int

@app.put("/people/{person_id}")
async def update_person(person_id: str, person: PersonUpdate):
    success = face_service.update_person_details(person_id, person.name, person.age)
    if success:
        return {"status": "updated", "person_id": person_id}
    return {"status": "error", "message": "Person not found"}


@app.get("/people", response_model=List[Person])
async def get_people():
    """Returns list of all registered people."""
    return storage.get_all()

class PersonUpdate(BaseModel):
    name: str
    age: int

@app.put("/people/{person_id}")
async def update_person(person_id: str, person: PersonUpdate):
    success = face_service.update_person_details(person_id, person.name, person.age)
    if success:
        return {"status": "updated", "person_id": person_id}
    return {"status": "error", "message": "Person not found"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)