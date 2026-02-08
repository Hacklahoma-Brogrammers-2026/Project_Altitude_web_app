import os
from services.recognition_service import FaceService
from services.storage import JsonPersonRepository

class Container:
    def __init__(self):
        # Ensure data directories exist
        os.makedirs("data/faces", exist_ok=True)
        
        # Initialize Storage
        self.storage = JsonPersonRepository(data_file="data/people.json")
        
        # Initialize Logic Service
        self.face_service = FaceService(storage=self.storage)

# Create a singleton instance
container = Container()