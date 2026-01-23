"""Main FastAPI application."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import auth, conversations, messages, files, alerts
from backend.db import Base, engine

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Supply Chain AI Assistant API",
    description="Backend API for Supply Chain AI Assistant with RAG capabilities",
    version="1.0.0",
)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(messages.router)
app.include_router(files.router)
app.include_router(alerts.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Supply Chain AI Assistant API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
