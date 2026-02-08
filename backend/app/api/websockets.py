from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import cv2
import numpy as np
import threading
import asyncio
from app.core.container import container

ws_router = APIRouter()
latest_frame = None
lock = threading.Lock()
stop_event = threading.Event()  # shared stop signal

async def display_loop():
    global latest_frame
    while True:
        await asyncio.sleep(0.01)  # prevent busy loop
        if latest_frame is not None:
            frame_copy = latest_frame.copy()
            cv2.imshow("Video Stream", frame_copy)
            # This is REQUIRED for the window to update
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    cv2.destroyAllWindows()

# start the display loop in a separate thread
threading.Thread(target=display_loop, daemon=True).start()


@ws_router.websocket("/ws/video-stream")
async def websocket_endpoint(websocket: WebSocket):
    global latest_frame
    await websocket.accept()
    print("Video WebSocket connected")

    # Reset stop_event at the start of each new connection
    stop_event.clear()

    try:
        while not stop_event.is_set():
            try:
                data = await websocket.receive_bytes()
            except Exception:
                print("WebSocket disconnected")
                stop_event.set()  # stop this loop
                break

            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is not None:
                with lock:
                    latest_frame = frame

    except Exception as e:
        print(f"Video WebSocket error: {e}")
        stop_event.set()