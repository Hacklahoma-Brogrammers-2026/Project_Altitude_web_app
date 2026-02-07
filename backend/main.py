import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Import Routers
from app.api.endpoints import router as api_router
from app.api.websockets import ws_router

# Initialize App
app = FastAPI(title="Project Altitude API")

# 1. CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Static Files (Images)
app.mount("/images", StaticFiles(directory="data/faces"), name="images")

# 3. Register Routes
app.include_router(api_router)
app.include_router(ws_router)

@app.get("/")
async def root():
    return {"message": "Face Recognition API is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)