import os
from pathlib import Path
from services.recognition_service import FaceService
from services.storage import JsonPersonRepository

class Container:
    def __init__(self):
        # 1. Calculate Absolute Paths
        # This gets the 'backend' folder path regardless of where the app is run
        base_dir = Path(__file__).resolve().parent.parent.parent
        
        # Define data paths
        self.data_dir = base_dir / "data"
        self.faces_dir = self.data_dir / "faces"
        self.people_file = self.data_dir / "people.json"

        # 2. Create Directory Structure on Startup
        # parents=True creates 'data' if 'data/faces' is requested and both are missing
        self.faces_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Verified data directory: {self.data_dir}")
        print(f"Verified faces directory: {self.faces_dir}")
        
        # 3. Initialize Storage with absolute path
        # The storage class handles creating the empty json file if missing
        self.storage = JsonPersonRepository(data_file=str(self.people_file))
        
        # 4. Initialize Service with absolute path
        self.face_service = FaceService(
            storage=self.storage,
            images_dir=str(self.faces_dir)
        )

# Create a singleton instance
container = Container()