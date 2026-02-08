import asyncio
import websockets
import cv2
import numpy as np

async def send_video_data() -> None:
    """
    Captures video from the default camera and streams it to the WebSocket server.
    """
    uri: str = "ws://localhost:8000/ws/video-producer"
    
    # Open local webcam (0 is usually the default camera)
    cap: cv2.VideoCapture = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open video device.")
        return

    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}. Streaming...")
            
            while True:
                ret: bool
                frame: np.ndarray | None
                ret, frame = cap.read()
                
                if not ret or frame is None:
                    print("Error: Failed to capture frame.")
                    break
                
                # Encode frame to JPEG (this is an arbitrary choice; you can choose other formats)
                success: bool
                buffer: np.ndarray
                success, buffer = cv2.imencode('.jpg', frame)
                
                if not success:
                    print("Error: Failed to encode frame.")
                    continue

                await websocket.send(buffer.tobytes())
                
                # Wait for server ack to prevent flooding
                _ = await websocket.recv()
                
                # Small delay to control FPS (~20 FPS)
                await asyncio.sleep(0.05)

    except Exception as e:
        print(f"Connection ended: {e}")
    finally:
        cap.release()
        print("Video capture released.")

if __name__ == "__main__":
    asyncio.run(send_video_data())