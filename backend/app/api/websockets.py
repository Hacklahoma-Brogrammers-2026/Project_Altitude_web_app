from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import cv2
import numpy as np
import threading
import asyncio
import os
from services.recognition_service import FaceService
# from app.core.container import container

ws_router = APIRouter()
latest_frame = None
latest_frame_bytes = None
lock = threading.Lock()
stop_event = threading.Event()  # shared stop signal
face_service = FaceService()

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


if os.getenv("DISPLAY_STREAM") == "1":
    # start the display loop in a separate thread
    threading.Thread(target=display_loop, daemon=True).start()


@ws_router.websocket("/ws/video-producer")
async def websocket_producer(websocket: WebSocket):
    global latest_frame, latest_frame_bytes
    await websocket.accept()
    print("Video producer connected")
    print("Video WebSocket connected")

    # Reset stop_event at the start of each new connection
    stop_event.clear()

    try:
        while not stop_event.is_set():
            try:
                data = await websocket.receive_bytes()
            except WebSocketDisconnect:
                print("Video producer disconnected")
                break
            except Exception:
                print("WebSocket disconnected")
                stop_event.set()  # stop this loop
                break

            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is not None:
                # Add overlays/labels before streaming to consumers
                frame = face_service.process_frame(frame)
                success, buffer = cv2.imencode('.jpg', frame)
                if success:
                    with lock:
                        latest_frame = frame
                        latest_frame_bytes = buffer.tobytes()

            await websocket.send_text("ack")

    except Exception as e:
        print(f"Video producer error: {e}")


@ws_router.websocket("/ws/video-consumer")
async def websocket_consumer(websocket: WebSocket):
    await websocket.accept()
    print("Video consumer connected")

    try:
        while True:
            await asyncio.sleep(0.03)
            with lock:
                frame_bytes = latest_frame_bytes
            if frame_bytes:
                await websocket.send_bytes(frame_bytes)

    except Exception as e:
        print(f"Video consumer error: {e}")