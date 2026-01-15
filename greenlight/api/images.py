"""
Images API router.

Serves generated images and reference images.
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/{path:path}")
async def get_image(path: str):
    """Serve an image file.

    Supports serving:
    - Generated storyboard frames
    - Reference images
    - Any image within a project directory
    """
    image_path = Path(path)

    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    # Verify it's an image file
    valid_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    if image_path.suffix.lower() not in valid_extensions:
        raise HTTPException(status_code=400, detail="Invalid image type")

    # Determine media type
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_types.get(image_path.suffix.lower(), "image/png")

    return FileResponse(
        path=image_path,
        media_type=media_type,
        headers={"Cache-Control": "max-age=3600"},
    )
