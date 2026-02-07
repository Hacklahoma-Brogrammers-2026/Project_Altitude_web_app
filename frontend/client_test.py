import asyncio
import websockets

async def send_video_data():
    uri = "ws://localhost:8000/ws/video-stream"
    async with websockets.connect(uri) as websocket:
        # Simulate sending 10 "frames"
        for i in range(10):
            # Create dummy bytes (simulating a video frame)
            dummy_frame = bytes([0] * 1024) 
            
            await websocket.send(dummy_frame)
            print(f"Sent frame {i}")
            
            response = await websocket.recv()
            print(f"Server said: {response}")
            
            await asyncio.sleep(0.1) # Simulate 10 FPS

if __name__ == "__main__":
    # You might need to install 'websockets' client lib first:
    # pip install websockets
    asyncio.run(send_video_data())