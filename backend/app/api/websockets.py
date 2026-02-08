from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import cv2
import numpy as np
import threading
# from app.core.container import container

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

latest_frame = None
lock = threading.Lock()
stop_event = threading.Event()  # shared stop signal

def display_loop():
    global latest_frame
    print("Display loop started. Press 'q' to exit.")
    while not stop_event.is_set():
        with lock:
            frame = latest_frame
        if frame is not None:
            cv2.imshow("Video Stream", frame)
        # Press 'q' locally to stop
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_event.set()
            break
    cv2.destroyAllWindows()
    print("Display loop exited")


# start the display loop in a separate thread
threading.Thread(target=display_loop, daemon=True).start()


@ws_router.websocket("/ws/video-stream")
async def websocket_endpoint(websocket: WebSocket):
    global latest_frame
    await websocket.accept()
    print("Video WebSocket connected")

    try:
        while not stop_event.is_set():
            try:
                data = await websocket.receive_bytes()
            except Exception:
                print("WebSocket disconnected")
                stop_event.set()
                break

            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is not None:
                with lock:
                    latest_frame = frame

    except Exception as e:
        print(f"Video WebSocket error: {e}")
        stop_event.set()