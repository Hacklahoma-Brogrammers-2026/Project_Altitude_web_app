# client.py
import asyncio
import websockets

# Connect to local server
URI = "ws://localhost:8000/ws/debug"

async def send_hello():
    while True:
        try:
            async with websockets.connect(URI) as websocket:
                print(f"Connected to {URI}")

                while True:
                    await websocket.send("hello world")
                    print("Sent: hello world")
                    reply = await websocket.recv()
                    print(f"Received from server: {reply}")
                    await asyncio.sleep(3)

        except Exception as e:
            print(f"Connection failed: {e}, retrying in 3s...")
            await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(send_hello())