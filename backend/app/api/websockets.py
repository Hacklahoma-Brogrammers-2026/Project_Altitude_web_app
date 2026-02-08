from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import cv2
import numpy as np
import threading
import asyncio
import os

from app.core.container import container

ws_router = APIRouter()
latest_frame = None
latest_frame_bytes = None
last_recognition_id = None
recognition_clients: set[WebSocket] = set()
lock = threading.Lock()
face_service = container.face_service

# We'll store the display thread and a stop event
display_thread = None
display_stop_event = None

def display_loop(stop_event):
    """Runs the OpenCV display loop until stop_event is set."""
    global latest_frame
    cv2.namedWindow("Video Stream", cv2.WINDOW_NORMAL)

    while not stop_event.is_set():
        if latest_frame is not None:
            with lock:
                frame_copy = latest_frame.copy()
            cv2.imshow("Video Stream", frame_copy)

        # GUI update
        if cv2.waitKey(1) & 0xFF == ord("q"):
            stop_event.set()  # allow quitting via 'q'

    cv2.destroyAllWindows()
    print("Display loop stopped")

SAVE_FOLDER = "audiotest"
os.makedirs(SAVE_FOLDER, exist_ok=True)

file_counter = 0  # global counter for sequential filenames

@ws_router.websocket("/ws/audio-debug")
async def websocket_audio_debug(websocket: WebSocket):
    global file_counter
    await websocket.accept()
    print("[INFO] Client connected to /ws/audio-debug")

    try:
        while True:
            message = await websocket.receive_bytes()
            # save the received WAV bytes
            filename = os.path.join(SAVE_FOLDER, f"audio_{file_counter:04d}.wav")
            with open(filename, "wb") as f:
                f.write(message)
            print(f"[INFO] Saved WAV file: {filename}")
            file_counter += 1
    except WebSocketDisconnect:
        print("[INFO] Client disconnected from /ws/audio-debug")

async def _broadcast_recognition(contact_id: str) -> None:
    if not recognition_clients:
        return

    payload = {"contact_id": contact_id}
    # print(f"[INFO] Broadcasting recognition event: {contact_id}")
    disconnected: list[WebSocket] = []
    # Iterate over a copy to handle set modifications during iteration
    for client in list(recognition_clients):
        try:
            await client.send_json(payload)
        except Exception:
            disconnected.append(client)

    for client in disconnected:
        recognition_clients.discard(client)

@ws_router.websocket("/ws/video-debug")
async def websocket_debug(websocket: WebSocket):
    global latest_frame, display_thread, display_stop_event

    await websocket.accept()
    print("Video WebSocket connected")

    # Start display loop only if it's not running
    if display_thread is None or not display_thread.is_alive():
        display_stop_event = threading.Event()
        display_thread = threading.Thread(target=display_loop, args=(display_stop_event,))
        display_thread.start()
        print("Display loop started")

    try:
        while True:
            try:
                data = await websocket.receive_bytes()
            except Exception:
                print("WebSocket disconnected")
                break

            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is not None:
                with lock:
                    latest_frame = frame

            await websocket.send_text("ID1")

    except Exception as e:
        print(f"Video WebSocket error: {e}")

    finally:
        # Stop the display loop when WebSocket disconnects
        if display_stop_event:
            display_stop_event.set()
        if display_thread:
            display_thread.join()
        print("WebSocket connection closed, display loop terminated")

@ws_router.websocket("/ws/video-producer")
async def websocket_producer(websocket: WebSocket):
    global latest_frame, latest_frame_bytes, last_recognition_id
    await websocket.accept()
    print("Video producer connected")
    print("Video WebSocket connected")

    # Reset stop_event at the start of each new connection
    stop_event = threading.Event()

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
            detected_id = None

            if frame is not None:
                # Add overlays/labels before streaming to consumers
                # process_frame now returns (annotated_frame, single_detected_id_or_none)
                frame, detected_id = face_service.process_frame(frame)
                
                if detected_id:
                    await _broadcast_recognition(detected_id)

                success, buffer = cv2.imencode('.jpg', frame)
                if success:
                    with lock:
                        latest_frame = frame
                        latest_frame_bytes = buffer.tobytes()

            await websocket.send_text(detected_id if detected_id else "No Person")

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

@ws_router.websocket("/ws/recognition")
async def websocket_recognition(websocket: WebSocket):
    await websocket.accept()
    recognition_clients.add(websocket)
    print("Recognition WebSocket connected")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Recognition WebSocket error: {e}")
    finally:
        recognition_clients.discard(websocket)
        print("Recognition WebSocket disconnected")