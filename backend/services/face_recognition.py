import os
import cv2
import face_recognition
import numpy as np
from typing import List, Dict, Any, Tuple

class FaceService:
    def __init__(self, known_faces_dir: str = "known_faces"):
        self.known_face_encodings: List[np.ndarray] = []
        self.known_face_metadata: List[Dict[str, Any]] = []
        self._load_known_faces(known_faces_dir)

    def _load_known_faces(self, directory: str) -> None:
        """Internal method to load images from disk on startup."""
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory '{directory}'. Please add images there.")
            return

        print(f"Loading known faces from {directory}...")
        for filename in os.listdir(directory):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                name = os.path.splitext(filename)[0].capitalize()
                filepath = os.path.join(directory, filename)
                
                try:
                    image = face_recognition.load_image_file(filepath)
                    encodings = face_recognition.face_encodings(image)

                    if encodings:
                        self.known_face_encodings.append(encodings[0])
                        self.known_face_metadata.append({
                            "name": name,
                            "access_level": "Admin" if name == "Mark" else "Guest"
                        })
                        print(f" - Loaded: {name}")
                    else:
                        print(f" - Warning: No face found in {filename}")
                except Exception as e:
                    print(f" - Error loading {filename}: {e}")

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Takes a raw OpenCV frame, performs recognition, draws annotations,
        and returns the annotated frame.
        """
        # Resize to 1/4 for performance
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        
        # Convert BGR (OpenCV) to RGB (face_recognition)
        rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])

        # Detect
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names: List[str] = []
        face_infos: List[Dict[str, Any]] = []

        # Identify
        for face_encoding in face_encodings:
            name = "Unknown"
            info = {"access_level": "N/A"}

            # Calculate distances to known faces
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                # arbitrary threshold for strictness (lower is stricter)
                if face_distances[best_match_index] < 0.6:
                    name = self.known_face_metadata[best_match_index]["name"]
                    info = self.known_face_metadata[best_match_index]

            face_names.append(name)
            face_infos.append(info)

        # Draw checks
        self._draw_annotations(frame, face_locations, face_names, face_infos)
        
        return frame

    def _draw_annotations(
        self, 
        frame: np.ndarray, 
        locations: List[Tuple[int, int, int, int]], 
        names: List[str], 
        infos: List[Dict[str, Any]]
    ) -> None:
        """Helper to draw rectangles and text on the frame."""
        for (top, right, bottom, left), name, info in zip(locations, names, infos):
            # Scale back up by 4
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)

            # Box
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            # Label
            label = f"{name} ({info['access_level']})"
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, label, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)