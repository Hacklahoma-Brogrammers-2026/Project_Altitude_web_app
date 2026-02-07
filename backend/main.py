from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

app = FastAPI()

# Pydantic model for metadata (if sent alongside the stream)
class VideoMetadata(BaseModel):
    camera_id: str = Field(..., description="ID of the source camera")
    timestamp: float = Field(..., description="Unix timestamp of the stream start")
    resolution: str | None = Field(None, description="Resolution like '1920x1080'")

@app.get("/")
async def root():
    return {"message": "Video Stream API is running"}

# Receive raw bytes stream (e.g., for live streaming)
# This endpoint expects the body to be the raw video bytes
@app.post("/stream-bytes/")
async def stream_bytes(request: Request):
    total_bytes = 0
    async for chunk in request.stream():
        # Process the chunk here 
        total_bytes += len(chunk)
        print(f"\tReceived chunk of size: {len(chunk)} bytes, total so far: {total_bytes} bytes")
        print(f"\tChunk content (first 100 bytes): {chunk[:100]}\n")  # Print first 100 bytes of the chunk for debugging
        
    return JSONResponse(content={"status": "stream recieved", "bytes_processed": total_bytes})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)