"""
FastAPI application for Project Greenlight.

Simple, clean API with the essential endpoints for the frontend.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from greenlight.core.config import settings
from .projects import router as projects_router
from .pipelines import router as pipelines_router
from .images import router as images_router
from .ingestion import router as ingestion_router

app = FastAPI(
    title="Project Greenlight API",
    description="AI-Powered Cinematic Storyboard Generation",
    version="2.0.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Expose all headers for SSE and file downloads
)

# Include routers
app.include_router(projects_router, prefix="/api/projects", tags=["projects"])
app.include_router(pipelines_router, prefix="/api/pipelines", tags=["pipelines"])
app.include_router(images_router, prefix="/api/images", tags=["images"])
app.include_router(ingestion_router, prefix="/api/ingestion", tags=["ingestion"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Project Greenlight API", "version": "2.0.0"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    keys = settings.validate_keys()
    return {
        "status": "healthy",
        "api_keys_configured": keys,
    }


@app.get("/api/settings")
async def get_settings():
    """Get current settings (safe version without keys)."""
    return {
        "default_llm": settings.default_llm,
        "default_image_model": settings.default_image_model,
        "api_keys_configured": settings.validate_keys(),
    }


@app.get("/api/settings/storyboard-models")
async def get_storyboard_models():
    """Get available image generation models for storyboard generation."""
    models = [
        {
            "key": "flux_2_pro",
            "display_name": "Flux 2 Pro",
            "provider": "Replicate",
            "description": "High quality, up to 8 reference images. Best for character consistency.",
            "default": True,
        },
        {
            "key": "seedream",
            "display_name": "Seedream 4.5",
            "provider": "Replicate",
            "description": "Fast, up to 14 reference images. Great character likeness preservation.",
            "default": False,
        },
        {
            "key": "nano_banana_pro",
            "display_name": "Nano Banana Pro",
            "provider": "Replicate",
            "description": "Fast generation with good quality. Supports reference images.",
            "default": False,
        },
    ]
    return {"models": models}


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Start the FastAPI server."""
    uvicorn.run(
        "greenlight.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    start_server()
