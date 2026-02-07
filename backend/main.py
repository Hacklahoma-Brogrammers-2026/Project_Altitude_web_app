from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
import cv2
import numpy as np
from typing import Dict

# Import our new service
from services.face_recognition import FaceService

app = FastAPI()

# Initialize the service globally
# This triggers the loading of images when the server starts
face_service = FaceService(known_faces_dir="known_faces")

@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Face Recognition API is running"}

@app.websocket("/ws/debug")
async def ws_debug(websocket: WebSocket):
    await websocket.accept()
    print("Debug WebSocket connected")

    try:
        while True:
            # Wait for a message from the Pi
            data = await websocket.receive_text()
            print(f"Received from Pi: {data}")

            # Optional: reply back
            await websocket.send_text("ack")  # just acknowledgment
    except WebSocketDisconnect:
        print("Debug WebSocket disconnected")
    except Exception as e:
        print(f"Error in debug websocket: {e}")
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass

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
            
            # 3. Process (Delegate to Service)
            processed_frame = face_service.process_frame(frame)

            # 4. Display (Server-side debugging)
            # Note: This requires a GUI environment. 
            # If running on a headless server, comment out the imshow/waitKey lines.
            cv2.imshow("Server Feed", processed_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)