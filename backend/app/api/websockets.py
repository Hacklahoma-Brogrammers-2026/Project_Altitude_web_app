from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import cv2
import numpy as np
from app.core.container import container

ws_router = APIRouter()

@ws_router.websocket("/ws/debug")
async def ws_debug(websocket: WebSocket):
    await websocket.accept()
    print("Debug WebSocket connected")
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received from Pi: {data}")
            await websocket.send_text("ack")
    except WebSocketDisconnect:
        print("Debug WebSocket disconnected")
    except Exception as e:
        print(f"Error in debug websocket: {e}")

@ws_router.websocket("/ws/video-stream")
async def websocket_endpoint(websocket: WebSocket):
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
            
            # 3. Process via Service
            processed_frame = container.face_service.process_frame(frame)

            # 4. Display (Server-side debug)
            # Note: Comment this out in production/headless environments
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