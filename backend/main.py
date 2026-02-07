from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
import numpy as np
import cv2
import face_recognition
import os
from typing import Dict, List, Tuple, Any

app = FastAPI()

class FaceRecognitionSystem:
    def __init__(self, known_faces_dir: str = "known_faces"):
        self.known_face_encodings: List[np.ndarray] = []
        self.known_face_metadata: List[Dict[str, Any]] = []
        self.load_known_faces(known_faces_dir)

    def load_known_faces(self, directory: str) -> None:
        """Loads images from a folder and encodes them for recognition."""
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory '{directory}'. Please add images (e.g., mark.jpg) there.")
            return

        print("Loading known faces...")
        for filename in os.listdir(directory):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                # Name derived from filename (e.g., "mark.jpg" -> "Mark")
                name = os.path.splitext(filename)[0].capitalize()
                filepath = os.path.join(directory, filename)
                
                # Load and encode
                image = face_recognition.load_image_file(filepath)
                encodings = face_recognition.face_encodings(image)

                if encodings:
                    self.known_face_encodings.append(encodings[0])
                    # Store extra data here
                    self.known_face_metadata.append({
                        "name": name,
                        "access_level": "Admin" if name == "Mark" else "Guest",
                        "status": "Verified"
                    })
                    print(f"Loaded encoded face for: {name}")
                else:
                    print(f"Warning: No face found in {filename}")

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Detects faces, recognizes them, and draws annotations on the frame.
        """
        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # Convert the image from BGR color (OpenCV) to RGB color (face_recognition)
        # Handle numpy version compatibility for the slice
        rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])

        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        face_infos = []

        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
            name = "Unknown"
            info = {"access_level": "N/A"}

            # Or instead, use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = self.known_face_metadata[best_match_index]["name"]
                    info = self.known_face_metadata[best_match_index]

            face_names.append(name)
            face_infos.append(info)

        # Display the results
        for (top, right, bottom, left), name, info in zip(face_locations, face_names, face_infos):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Draw a box around the face
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255) # Green for known, Red for unknown
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            # Draw a label with a name below the face
            label = f"{name} ({info['access_level']})"
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, label, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

        return frame

# Initialize system
face_system = FaceRecognitionSystem()

@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Face Recognition API is running"}

@app.websocket("/ws/video-stream")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    print("Client connected via WebSocket")
    
    try:
        while True:
            # 1. Receive bytes
            data: bytes = await websocket.receive_bytes()
            nparr: np.ndarray = np.frombuffer(data, np.uint8)
            
            # 2. Decode image
            frame: np.ndarray | None = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                continue
            
            # 3. PROCESS: Detect and Recognize
            # This allows us to modify the frame in place before displaying
            processed_frame = face_system.process_frame(frame)

            # 4. DISPLAY: Show in a window 
            cv2.imshow("Server Video Feed", processed_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            await websocket.send_text("ack")
            
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Unexpected Error: {e}")
    finally:
        cv2.destroyAllWindows()
        try:
            await websocket.close()
        except RuntimeError:
            pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)