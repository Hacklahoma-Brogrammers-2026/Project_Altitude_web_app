import os
import cv2
import face_recognition
import numpy as np
import uuid
from typing import List, Dict, Any, Tuple
from .storage import PersonRepository, JsonPersonRepository, Person

class FaceService:
    def __init__(self, storage: PersonRepository = None, images_dir: str = "data/faces"):
        self.storage = storage or JsonPersonRepository(data_file="data/people.json")
        self.images_dir = images_dir
        
        # Ensure the directory exists (Service level check)
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)

        # In-memory caches for fast recognition
        self.known_face_encodings: List[np.ndarray] = []
        self.known_face_ids: List[str] = []
        self.known_face_metadata: Dict[str, Person] = {}

        self._load_from_storage()

    def _load_from_storage(self) -> None:
        """Loads all people from the repository into memory."""
        people = self.storage.get_all()
        print(f"Loading {len(people)} people from storage...")
        
        for person in people:
            if person.encoding:
                self.known_face_encodings.append(np.array(person.encoding))
                self.known_face_ids.append(person.id)
                self.known_face_metadata[person.id] = person

    def update_person_details(self, person_id: str, name: str, age: int):
        """Public API to update a person's details."""
        updated_person = self.storage.update_person(person_id, {"name": name, "age": age})
        if updated_person:
            # Update in-memory cache
            self.known_face_metadata[person_id] = updated_person
            print(f"Updated person {person_id} -> {name}")
            return True
        return False

    def _register_new_face(self, frame_rgb: np.ndarray, location: Tuple[int, int, int, int], encoding: np.ndarray):
        """Creates a new Person entry for an unknown face."""
        new_id = str(uuid.uuid4())
        
        # 1. Save Image Crop
        top, right, bottom, left = location
        # Add some padding if possible
        h, w, _ = frame_rgb.shape
        top = max(0, top - 20); bottom = min(h, bottom + 20)
        left = max(0, left - 20); right = min(w, right + 20)
        
        face_image = frame_rgb[top:bottom, left:right]
        # Convert back to BGR for OpenCV saving
        face_image_bgr = cv2.cvtColor(face_image, cv2.COLOR_RGB2BGR)
        
        image_path = os.path.join(self.images_dir, f"{new_id}.jpg")
        cv2.imwrite(image_path, face_image_bgr)

        # 2. Create Person Object
        new_person = Person(
            id=new_id,
            name="Unknown", 
            image_path=image_path,
            encoding=encoding.tolist()
        )

        # 3. Save to Storage
        self.storage.add_person(new_person)

        # 4. Update Memory (so we recognize them in the next frame)
        self.known_face_encodings.append(encoding)
        self.known_face_ids.append(new_id)
        self.known_face_metadata[new_id] = new_person
        
        print(f"Registered new face: {new_id}")
        return new_person

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        # Resize to 1/4 for performance
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_display_data = []

        for location, encoding in zip(face_locations, face_encodings):
            name = "Unknown"
            access_label = "Detecting..."
            color = (255, 165, 0) # Orange for uncertain
            
            # 1. Calculate distances to ALL known faces (including previously auto-saved ones)
            if self.known_face_encodings:
                face_distances = face_recognition.face_distance(self.known_face_encodings, encoding)
                best_match_index = np.argmin(face_distances)
                min_distance = face_distances[best_match_index]
            else:
                min_distance = 1.0 # No database yet

            # --- SMART LOGIC ---
            if min_distance < 0.55:
                # STRONG MATCH -> Identify Person
                person_id = self.known_face_ids[best_match_index]
                person_obj = self.known_face_metadata[person_id]
                
                name = person_obj.name
                access_label = f"Age: {person_obj.age}" if person_obj.age else "Verified"
                color = (0, 255, 0) # Green

            elif min_distance < 0.75:
                # WEAK MATCH / AMBIGUOUS -> Do NOT save distinct entry
                # This prevents creating "Person #2" just because "Person #1" turned their head.
                # We assume it's the closest match but don't officially log it or create new junk data.
                if self.known_face_ids:
                    person_id = self.known_face_ids[best_match_index]
                    possible_name = self.known_face_metadata[person_id].name
                    name = f"Possible {possible_name}?"
                    access_label = f"Uncertain ({min_distance:.2f})"
                else:
                    name = "Similarity check"
                color = (0, 255, 255) # Yellow

            else:
                # NO MATCH -> Truly New Face -> Register
                new_person = self._register_new_face(rgb_small_frame, location, encoding)
                name = new_person.name 
                access_label = "New Entry Saved"
                color = (0, 0, 255) # Red

            face_display_data.append((location, name, access_label, color))

        # Draw annotations
        for (top, right, bottom, left), name, label, color in face_display_data:
            top *= 4; right *= 4; bottom *= 4; left *= 4
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 15), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, label, (left + 6, bottom - 2), cv2.FONT_HERSHEY_DUPLEX, 0.4, (200, 200, 200), 1)

        return frame