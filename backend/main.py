import sys
import os
from pathlib import Path

from backend.services.audio_embedding_service import init_audio_service

# --- PATH CONFIGURATION ---
# Get the absolute path of the 'backend' directory (where this file lives)
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent

# Add it to sys.path if it's not already there
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

if str(project_root) not in sys.path:
    sys.path.append(str(project_root))
# ---------------------------

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware


# Import Routers
from app.api.endpoints import router as api_router
from app.api.websockets import ws_router

# from dotenv import load_dotenv
# load_dotenv()

from backend.config import config

from database.db import init_db
# init_db(config.mongo_url, config.db_name)

init_audio_service()
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