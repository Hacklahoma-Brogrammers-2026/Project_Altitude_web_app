from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
import numpy as np
import cv2
from typing import Dict

app = FastAPI()

@app.get("/")
async def root() -> Dict[str, str]:
    """Health check endpoint."""
    return {"message": "Video Stream API is running"}

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
    """
    WebSocket endpoint that receives encoded image frames (JPEG),
    decodes them, processes them, and displays them server-side.
    """
    await websocket.accept()
    print("Client connected via WebSocket")
    
    try:
        while True:
            # 1. Receive bytes (Most common formats will be accepted)
            data: bytes = await websocket.receive_bytes()
            nparr: np.ndarray = np.frombuffer(data, np.uint8)
            
            # 2. Decode image
            frame: np.ndarray | None = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                print("Could not decode frame")
                continue
            
            # 3. DISPLAY: Show in a window 
            cv2.imshow("Server Video Feed", frame)
            
            # Check for 'q' key to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # 4. send confirmation back to client 
            await websocket.send_text("ack")
            
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Unexpected Error: {e}")
    finally:
        cv2.destroyAllWindows()
        # Attempt to close the websocket gracefully if it's still open
        try:
            await websocket.close()
        except RuntimeError:
            pass # Websocket already closed

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)