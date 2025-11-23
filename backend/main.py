"""
main.py - FastAPI Application Entry Point
"""

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import os

from app.routers import generate

# Initialize FastAPI app
app = FastAPI(
    title="Procedural 3D Model Generator API",
    description="AI-powered procedural generation of 3D models (.obj files)",
    version="1.0.0"
)

# CORS configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(generate.router, prefix="/api", tags=["generation"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "message": "Procedural 3D Model Generator API",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)