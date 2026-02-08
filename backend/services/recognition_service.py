import os
import cv2
import face_recognition
import numpy as np
import uuid
import traceback
from typing import List, Dict, Any, Tuple
from .storage import PersonRepository, Contact
from repos import contact_repo

class FaceService:
    def __init__(self, storage: PersonRepository = None, images_dir: str = "data/faces"):
        self.storage = storage 
        self.images_dir = images_dir
        
        # Ensure the directory exists (Service level check)
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)

        # In-memory caches for fast recognition
        self.known_face_encodings: List[np.ndarray] = []
        self.known_face_ids: List[str] = []
        self.known_face_metadata: Dict[str, Contact] = {}
        self.current_user_id = None
        self.last_recognized_id: str | None = None

        # self._load_from_storage() # Do not load at init, wait for user login

    def set_current_user(self, user_id: str):
        self.current_user_id = user_id
        print(f"FaceService: current user set to {user_id}")
        self._load_from_storage()

    def _load_from_storage(self) -> None:
        """Loads all people from the repository into memory for CURRENT USER."""
        if not self.current_user_id:
             print("FaceService: No user logged in, clearing cache.")
             self.known_face_encodings = []
             self.known_face_ids = []
             self.known_face_metadata = {}
             return

        people = self.storage.get_all(user_id=self.current_user_id)
        print(f"Loading {len(people)} people from storage for user {self.current_user_id}...")
        
        # Reset cache
        self.known_face_encodings = []
        self.known_face_ids = []
        self.known_face_metadata = {}

        for person in people:
            if person.encoding:
                self.known_face_encodings.append(np.array(person.encoding))
                self.known_face_ids.append(person.contact_id)
                self.known_face_metadata[person.contact_id] = person

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
        """Creates a new Person entry for an unknown face.
           Now ensures DB consistency and User isolation.
        """
        
        if not self.current_user_id:
            print("WARNING: No current_user_id set. Skipping face registration.")
            # Return a temporary person object so the UI considers it handled (but not saved)
            # Using Dummy Contact
            return Contact(contact_id="unsaved", owner_user_id="none", first_name="Unsaved", last_name="(Login Required)")
            
        try:
            # 1. Create Contact in DB FIRST (Ground Truth)
            print(f"Attempting to create contact for user_id: {self.current_user_id}")
            # Note: create_contact is just a factory, it doesn't save yet in db but it validates user
            # We want to use storage.add_person eventually, or manual repo usage.
            # But the service logic requires specific steps.
            
            # Let's create the object locally
            new_id = str(uuid.uuid4())
            
            # 2. Save Image Crop (Path: data/faces/{user_id}/{contact_id}.jpg)
            top, right, bottom, left = location
            h, w, _ = frame_rgb.shape
            top = max(0, top - 20); bottom = min(h, bottom + 20)
            left = max(0, left - 20); right = min(w, right + 20)
            
            face_image = frame_rgb[top:bottom, left:right]
            face_image_bgr = cv2.cvtColor(face_image, cv2.COLOR_RGB2BGR)
            
            user_faces_dir = os.path.join(self.images_dir, self.current_user_id)
            if not os.path.exists(user_faces_dir):
                os.makedirs(user_faces_dir)
            
            relative_image_path = os.path.join(self.current_user_id, f"{new_id}.jpg")
            full_image_path = os.path.join(self.images_dir, relative_image_path)
            
            cv2.imwrite(full_image_path, face_image_bgr)

            # 3. Create Contact Object (Unified)
            new_person = Contact(
                contact_id=new_id,
                owner_user_id=self.current_user_id,
                first_name="Unknown",
                last_name="Person",
                image_path=relative_image_path, # Store relative path or absolute? Storage was just "path"
                encoding=encoding.tolist()
            )

            # 4. Save to Storage (DB)
            self.storage.add_person(new_person)

            # 5. Update Memory (so we recognize them in the next frame)
            self.known_face_encodings.append(encoding)
            self.known_face_ids.append(new_id)
            self.known_face_metadata[new_id] = new_person
            
            print(f"Registered new face: {new_id}")
            return new_person

        except Exception as e:
            traceback.print_exc()
            print(f"ERROR: Failed to register face: {e}")
            return Contact(contact_id="error", owner_user_id="none", first_name="Registration", last_name="Failed")

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, str | None]:
        """
        Processes a video frame, detects faces, draws bounding boxes/labels,
        and returns the annotated frame plus a SINGLE detected person ID (strongest match).
        """
        # Resize to 1/4 for performance
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_display_data = []
        
        # Track the best candidate found in this frame
        strongest_person_id = None
        lowest_distance_found = 1.0 

        for location, encoding in zip(face_locations, face_encodings):
            name = "Unknown"
            access_label = "Detecting..."
            color = (255, 165, 0) # Orange for uncertain
            current_id = None
            is_strong_match = False
            
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
                
                current_id = person_id
                is_strong_match = True

            elif min_distance < 0.75:
                # WEAK MATCH / AMBIGUOUS -> Do NOT save distinct entry
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
                
                current_id = new_person.contact_id

            # Update Best Match Logic
            if current_id:
                if is_strong_match:
                    # If this is a strong match, and it's better than previous strong matches
                    if min_distance < lowest_distance_found:
                        lowest_distance_found = min_distance
                        strongest_person_id = current_id
                else:
                    # It's a new registration. Use it if we don't have a strong match yet.
                    if strongest_person_id is None:
                        strongest_person_id = current_id

            face_display_data.append((location, name, access_label, color))

        # Draw annotations
        for (top, right, bottom, left), name, label, color in face_display_data:
            top *= 4; right *= 4; bottom *= 4; left *= 4
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 15), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, label, (left + 6, bottom - 2), cv2.FONT_HERSHEY_DUPLEX, 0.4, (200, 200, 200), 1)

        return frame, strongest_person_id