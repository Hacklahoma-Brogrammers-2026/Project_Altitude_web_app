from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Video Stream API is running"}

# WebSocket endpoint for continuous streaming
@app.websocket("/ws/video-stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected via WebSocket")
    
    try:
        while True:
            # Receive raw bytes (frame data)
            data = await websocket.receive_bytes()
            
            # --- VIDEO PROCESSING LOGIC GOES HERE ---
            # Example: decoding a frame with OpenCV would happen here.
            # For now, we just print the size.
            print(f"Received frame packet: {len(data)} bytes")
            
            # Optional: Send a confirmation back to the device
            await websocket.send_text("ack")
            
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)