"""
Ingestion API Router for Project Greenlight.

Handles:
- File uploads (documents, images, archives)
- Ingestion pipeline execution
- Entity confirmation
- World builder triggering

TRACE: INGEST-001
"""

import asyncio
import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse

from greenlight.core.config import settings
from greenlight.core.ingestion import IngestionPipeline
from greenlight.core.models import (
    ConfirmEntitiesRequest,
    ConfirmEntitiesResponse,
    EntityConfirmation,
    EntityType,
    PipelineStage,
)

router = APIRouter()

# Track running ingestion pipelines
_running_pipelines: dict[str, dict] = {}


# =============================================================================
# FILE UPLOAD ENDPOINTS
# =============================================================================

@router.post("/upload")
async def upload_files(
    project_path: str = Form(...),
    files: list[UploadFile] = File(...),
):
    """
    Upload files to a project for ingestion.

    Supported formats:
    - Documents: .txt, .md, .pdf, .docx
    - Images: .png, .jpg, .jpeg, .gif, .webp
    - Archives: .zip (will be extracted)
    """
    project_dir = Path(project_path)
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    # Create uploads directory
    uploads_dir = project_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    uploaded_files = []
    errors = []

    for file in files:
        try:
            # Validate file extension
            suffix = Path(file.filename).suffix.lower()
            valid_extensions = {
                ".txt", ".md", ".pdf", ".docx",
                ".png", ".jpg", ".jpeg", ".gif", ".webp",
                ".zip"
            }

            if suffix not in valid_extensions:
                errors.append({
                    "filename": file.filename,
                    "error": f"Unsupported file type: {suffix}"
                })
                continue

            # Save file
            file_path = uploads_dir / file.filename
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)

            uploaded_files.append({
                "filename": file.filename,
                "path": str(file_path),
                "size": len(content),
                "type": suffix[1:],  # Remove the dot
            })

        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })

    return {
        "success": len(uploaded_files) > 0,
        "uploaded": uploaded_files,
        "errors": errors,
        "message": f"Uploaded {len(uploaded_files)} files" + (
            f", {len(errors)} errors" if errors else ""
        )
    }


# =============================================================================
# INGESTION PIPELINE ENDPOINTS
# =============================================================================

@router.post("/start")
async def start_ingestion(
    project_path: str = Form(...),
    pitch: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None,
):
    """
    Start the ingestion pipeline for uploaded files and/or pitch.

    This will:
    1. Process all files in the uploads directory (if any)
    2. Extract text from documents
    3. Analyze images with Isaac 0.1
    4. Chunk text content
    5. Extract entities from chunks (and pitch if provided)
    6. Save chunks.json and extracted_entities.json
    """
    project_dir = Path(project_path)
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    uploads_dir = project_dir / "uploads"

    # Collect all files
    file_paths = []
    if uploads_dir.exists():
        for f in uploads_dir.iterdir():
            if f.is_file() and not f.name.startswith('.'):
                file_paths.append(f)

    # Check if we have either files or pitch
    has_pitch = pitch and pitch.strip()
    if not file_paths and not has_pitch:
        raise HTTPException(status_code=400, detail="No files to process and no pitch provided")

    # Create pipeline ID
    pipeline_id = f"ingest-{uuid.uuid4().hex[:8]}"

    # Initialize pipeline status
    _running_pipelines[pipeline_id] = {
        "status": PipelineStage.INITIALIZING.value,
        "progress": 0.0,
        "message": "Starting ingestion...",
        "logs": [],
        "started_at": datetime.now().isoformat(),
    }

    # Run pipeline in background
    async def run_pipeline():
        try:
            def log_callback(msg: str):
                _running_pipelines[pipeline_id]["logs"].append(msg)
                _running_pipelines[pipeline_id]["message"] = msg

            def progress_callback(progress: float):
                _running_pipelines[pipeline_id]["progress"] = progress

            _running_pipelines[pipeline_id]["status"] = PipelineStage.RUNNING.value

            pipeline = IngestionPipeline(
                project_path=project_dir,
                log_callback=log_callback,
                progress_callback=progress_callback,
            )

            # Pass pitch to ingestion if provided
            result = await pipeline.ingest_files(file_paths, pitch=pitch if has_pitch else None)

            if result.get("success"):
                _running_pipelines[pipeline_id]["status"] = PipelineStage.COMPLETE.value
                _running_pipelines[pipeline_id]["result"] = result
            else:
                _running_pipelines[pipeline_id]["status"] = PipelineStage.ERROR.value
                _running_pipelines[pipeline_id]["error"] = result.get("error")

        except Exception as e:
            _running_pipelines[pipeline_id]["status"] = PipelineStage.ERROR.value
            _running_pipelines[pipeline_id]["error"] = str(e)

    # Start background task
    asyncio.create_task(run_pipeline())

    # Build message
    if file_paths and has_pitch:
        msg = f"Ingestion started for {len(file_paths)} files with pitch"
    elif file_paths:
        msg = f"Ingestion started for {len(file_paths)} files"
    else:
        msg = "Ingestion started with pitch only"

    return {
        "success": True,
        "pipeline_id": pipeline_id,
        "message": msg,
        "files": [f.name for f in file_paths],
        "has_pitch": has_pitch,
    }


@router.get("/status/{pipeline_id}")
async def get_ingestion_status(pipeline_id: str):
    """Get the status of a running ingestion pipeline."""
    if pipeline_id not in _running_pipelines:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    return _running_pipelines[pipeline_id]


@router.get("/entities/{project_path:path}")
async def get_extracted_entities(project_path: str):
    """
    Get extracted entities for user confirmation.

    Returns the pre-confirmation entity list from extracted_entities.json.
    """
    project_dir = Path(project_path)
    entities_path = project_dir / "ingestion" / "extracted_entities.json"

    if not entities_path.exists():
        raise HTTPException(
            status_code=404,
            detail="No extracted entities found. Run ingestion first."
        )

    try:
        data = json.loads(entities_path.read_text(encoding="utf-8"))
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load entities: {e}")


@router.get("/pending-confirmation/{project_path:path}")
async def check_pending_confirmation(project_path: str):
    """
    Check if there are entities pending confirmation.

    Returns true if extracted_entities.json exists and status is not 'confirmed'.
    This allows the UI to show a recovery option for interrupted entity confirmation.
    """
    project_dir = Path(project_path)
    entities_path = project_dir / "ingestion" / "extracted_entities.json"
    confirmed_path = project_dir / "ingestion" / "confirmed_entities.json"

    # No extracted entities = nothing pending
    if not entities_path.exists():
        return {
            "pending": False,
            "reason": "no_extracted_entities"
        }

    try:
        data = json.loads(entities_path.read_text(encoding="utf-8"))
        status = data.get("status", "pending")

        # If already confirmed, check if confirmed_entities exists
        if status == "confirmed" and confirmed_path.exists():
            return {
                "pending": False,
                "reason": "already_confirmed"
            }

        # Count entities to confirm
        entities = data.get("entities", {})
        total_entities = (
            len(entities.get("characters", [])) +
            len(entities.get("locations", [])) +
            len(entities.get("props", []))
        )

        if total_entities == 0:
            return {
                "pending": False,
                "reason": "no_entities_found"
            }

        return {
            "pending": True,
            "status": status,
            "entity_counts": {
                "characters": len(entities.get("characters", [])),
                "locations": len(entities.get("locations", [])),
                "props": len(entities.get("props", [])),
                "total": total_entities,
            },
            "created_at": data.get("created_at"),
        }
    except Exception as e:
        return {
            "pending": False,
            "reason": "error",
            "error": str(e)
        }


# =============================================================================
# ENTITY CONFIRMATION ENDPOINTS
# =============================================================================

@router.post("/confirm-entities")
async def confirm_entities(request: ConfirmEntitiesRequest):
    """
    Confirm extracted entities and assign canonical tags.

    This is called after the user reviews the entity confirmation modal.
    Confirmed entities will be used to trigger the world builder pipeline.
    """
    project_dir = Path(request.project_path)
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    entities_path = project_dir / "ingestion" / "extracted_entities.json"
    if not entities_path.exists():
        raise HTTPException(status_code=404, detail="No extracted entities found")

    # Load existing entities
    data = json.loads(entities_path.read_text(encoding="utf-8"))

    # Process confirmations
    confirmed_entities = {
        "characters": [],
        "locations": [],
        "props": [],
    }

    for entity in request.entities:
        if not entity.confirmed:
            continue

        entity_data = {
            "name": entity.name,
            "tag": entity.tag,
            "confirmed": True,
        }

        if entity.type == EntityType.CHARACTER:
            # Include role_hint for characters (protagonist, antagonist, etc.)
            if entity.role_hint:
                entity_data["role_hint"] = entity.role_hint
            confirmed_entities["characters"].append(entity_data)
        elif entity.type == EntityType.LOCATION:
            confirmed_entities["locations"].append(entity_data)
        elif entity.type == EntityType.PROP:
            confirmed_entities["props"].append(entity_data)

    # Save confirmed entities
    confirmed_path = project_dir / "ingestion" / "confirmed_entities.json"
    confirmed_path.write_text(
        json.dumps({
            "created_at": datetime.now().isoformat(),
            "status": "confirmed",
            "world_hints": data.get("world_hints", {}),
            "entities": confirmed_entities,
        }, indent=2),
        encoding="utf-8"
    )

    # Update original file status
    data["status"] = "confirmed"
    entities_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    return ConfirmEntitiesResponse(
        success=True,
        message="Entities confirmed successfully",
        characters_confirmed=len(confirmed_entities["characters"]),
        locations_confirmed=len(confirmed_entities["locations"]),
        props_confirmed=len(confirmed_entities["props"]),
    )


@router.post("/add-entity")
async def add_entity(
    project_path: str = Form(...),
    name: str = Form(...),
    entity_type: str = Form(...),
    tag: str = Form(...),
):
    """
    Manually add an entity that wasn't extracted.

    Users can add entities they know exist but weren't found by extraction.
    """
    project_dir = Path(project_path)
    confirmed_path = project_dir / "ingestion" / "confirmed_entities.json"

    if not confirmed_path.exists():
        # Create initial file
        data = {
            "created_at": datetime.now().isoformat(),
            "status": "confirmed",
            "world_hints": {},
            "entities": {
                "characters": [],
                "locations": [],
                "props": [],
            }
        }
    else:
        data = json.loads(confirmed_path.read_text(encoding="utf-8"))

    # Add entity to appropriate list
    entity_data = {
        "name": name,
        "tag": tag.upper(),
        "confirmed": True,
        "manually_added": True,
    }

    entity_type_lower = entity_type.lower()
    if entity_type_lower == "character":
        data["entities"]["characters"].append(entity_data)
    elif entity_type_lower == "location":
        data["entities"]["locations"].append(entity_data)
    elif entity_type_lower == "prop":
        data["entities"]["props"].append(entity_data)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid entity type: {entity_type}"
        )

    # Save
    confirmed_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    return {
        "success": True,
        "message": f"Added {entity_type} '{name}' with tag {tag}",
    }


@router.delete("/remove-entity")
async def remove_entity(
    project_path: str = Form(...),
    tag: str = Form(...),
):
    """Remove an entity from the confirmed list."""
    project_dir = Path(project_path)
    confirmed_path = project_dir / "ingestion" / "confirmed_entities.json"

    if not confirmed_path.exists():
        raise HTTPException(status_code=404, detail="No confirmed entities found")

    data = json.loads(confirmed_path.read_text(encoding="utf-8"))
    tag_upper = tag.upper()

    # Search and remove from all lists
    removed = False
    for entity_list in ["characters", "locations", "props"]:
        original_len = len(data["entities"][entity_list])
        data["entities"][entity_list] = [
            e for e in data["entities"][entity_list]
            if e.get("tag", "").upper() != tag_upper
        ]
        if len(data["entities"][entity_list]) < original_len:
            removed = True

    if not removed:
        raise HTTPException(status_code=404, detail=f"Entity with tag '{tag}' not found")

    # Save
    confirmed_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    return {
        "success": True,
        "message": f"Removed entity with tag {tag}",
    }


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@router.get("/chunks/{project_path:path}")
async def get_chunks(project_path: str):
    """Get the processed text chunks."""
    project_dir = Path(project_path)
    chunks_path = project_dir / "ingestion" / "chunks.json"

    if not chunks_path.exists():
        raise HTTPException(status_code=404, detail="No chunks found")

    try:
        data = json.loads(chunks_path.read_text(encoding="utf-8"))
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load chunks: {e}")


@router.delete("/clear-uploads/{project_path:path}")
async def clear_uploads(project_path: str):
    """Clear all uploaded files from a project."""
    project_dir = Path(project_path)
    uploads_dir = project_dir / "uploads"

    if uploads_dir.exists():
        shutil.rmtree(uploads_dir)

    return {
        "success": True,
        "message": "Uploads cleared",
    }
