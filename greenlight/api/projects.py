"""
Projects API router.

CRUD operations for projects.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from greenlight.core.config import settings

router = APIRouter()


class ProjectCreate(BaseModel):
    """Request to create a new project."""
    name: str
    path: Optional[str] = None
    location: Optional[str] = None  # Alias for path from frontend
    visual_style: str = "live_action"
    media_type: str = "standard"
    template: str = "feature_film"  # From frontend
    logline: str = ""  # From frontend
    genre: str = "Drama"  # From frontend
    pitch: str = ""


class ProjectResponse(BaseModel):
    """Project information response."""
    name: str
    path: str
    created_at: str
    last_modified: str
    has_pitch: bool = False
    has_world_config: bool = False
    has_script: bool = False
    has_visual_script: bool = False
    has_storyboard: bool = False


def _get_project_status(project_path: Path) -> dict:
    """Check what files exist in a project."""
    return {
        "has_pitch": (project_path / "world_bible" / "pitch.md").exists(),
        "has_world_config": (project_path / "world_bible" / "world_config.json").exists(),
        "has_script": (project_path / "scripts" / "script.md").exists(),
        "has_visual_script": (project_path / "storyboard" / "visual_script.json").exists(),
        "has_storyboard": (project_path / "storyboard_output" / "generated").exists()
            and any((project_path / "storyboard_output" / "generated").iterdir())
            if (project_path / "storyboard_output" / "generated").exists() else False,
    }


def _load_project_config(project_path: Path) -> dict:
    """Load project.json if it exists."""
    config_path = project_path / "project.json"
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8"))
    return {}


def _save_project_config(project_path: Path, config: dict):
    """Save project.json."""
    config_path = project_path / "project.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")


# ============================================================================
# Static routes (must come first)
# ============================================================================

@router.get("")
async def list_projects() -> list[ProjectResponse]:
    """List all projects in the projects directory."""
    projects = []
    projects_dir = settings.projects_dir

    if not projects_dir.exists():
        return []

    for item in projects_dir.iterdir():
        if item.is_dir() and (item / "project.json").exists():
            config = _load_project_config(item)
            status = _get_project_status(item)

            projects.append(ProjectResponse(
                name=config.get("name", item.name),
                path=str(item),
                created_at=config.get("created_at", ""),
                last_modified=config.get("last_modified", ""),
                **status
            ))

    # Sort by last modified, newest first
    projects.sort(key=lambda p: p.last_modified, reverse=True)
    return projects


async def _do_create_project(request: ProjectCreate) -> dict:
    """Internal project creation logic."""
    # Determine project path - check location (frontend) or path
    effective_path = request.path or request.location
    if effective_path:
        project_path = Path(effective_path) / request.name.replace(" ", "_").lower()
    else:
        # Create in default projects directory
        settings.projects_dir.mkdir(parents=True, exist_ok=True)
        project_path = settings.projects_dir / request.name.replace(" ", "_").lower()

    # Check if already exists
    if project_path.exists():
        raise HTTPException(status_code=400, detail="Project already exists")

    # Create directory structure
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / "world_bible").mkdir()
    (project_path / "scripts").mkdir()
    (project_path / "storyboard").mkdir()
    (project_path / "references").mkdir()
    (project_path / "storyboard_output" / "generated").mkdir(parents=True)

    # Create project.json
    now = datetime.now().isoformat()
    config = {
        "name": request.name,
        "visual_style": request.visual_style,
        "media_type": request.media_type,
        "template": request.template,
        "logline": request.logline,
        "genre": request.genre,
        "created_at": now,
        "last_modified": now,
    }
    _save_project_config(project_path, config)

    # Create pitch.md if pitch provided
    if request.pitch:
        pitch_path = project_path / "world_bible" / "pitch.md"
        pitch_path.write_text(request.pitch, encoding="utf-8")

    status = _get_project_status(project_path)

    return {
        "success": True,
        "project_path": str(project_path),
        "name": request.name,
        "path": str(project_path),
        "created_at": now,
        "last_modified": now,
        **status
    }


@router.post("")
async def create_project(request: ProjectCreate) -> ProjectResponse:
    """Create a new project."""
    result = await _do_create_project(request)
    return ProjectResponse(
        name=result["name"],
        path=result["path"],
        created_at=result["created_at"],
        last_modified=result["last_modified"],
        has_pitch=result["has_pitch"],
        has_world_config=result["has_world_config"],
        has_script=result["has_script"],
        has_visual_script=result["has_visual_script"],
        has_storyboard=result["has_storyboard"],
    )


@router.post("/create")
async def create_project_alt(request: ProjectCreate) -> dict:
    """Create a new project (alternative endpoint for frontend compatibility)."""
    return await _do_create_project(request)


# ============================================================================
# Path-based endpoints using query parameters (must come BEFORE /{project_name})
# These handle full project paths from frontend via ?path= query parameter
# ============================================================================

@router.get("/path-data/world")
async def get_world_by_path(path: str) -> dict:
    """Get world config by full project path (passed as query param)."""
    project_path = Path(path)
    config_path = project_path / "world_bible" / "world_config.json"

    if not config_path.exists():
        return {"characters": [], "locations": [], "props": [], "world_context": {}}

    return json.loads(config_path.read_text(encoding="utf-8"))


@router.get("/path-data/prompts")
async def get_prompts_by_path(path: str) -> dict:
    """Get prompts by full project path (passed as query param)."""
    project_path = Path(path)
    prompts_path = project_path / "storyboard" / "prompts.json"

    if not prompts_path.exists():
        return {"frames": []}

    return json.loads(prompts_path.read_text(encoding="utf-8"))


@router.get("/path-data/dialogues")
async def get_dialogues_by_path(path: str) -> dict:
    """Get dialogues by full project path (passed as query param)."""
    project_path = Path(path)
    vs_path = project_path / "storyboard" / "visual_script.json"

    if not vs_path.exists():
        return {"scenes": []}

    return json.loads(vs_path.read_text(encoding="utf-8"))


@router.patch("/path-data/world/entity/{entity_tag}")
async def update_entity_by_path(entity_tag: str, body: dict, path: str) -> dict:
    """Update entity description by full project path (path passed as query param)."""
    project_path = Path(path)
    config_path = project_path / "world_bible" / "world_config.json"

    if not config_path.exists():
        raise HTTPException(status_code=404, detail="World config not found")

    config = json.loads(config_path.read_text(encoding="utf-8"))

    # Find and update the entity
    entities = config.get("entities", [])
    found = False
    for entity in entities:
        if entity.get("tag") == entity_tag:
            if "description" in body:
                entity["description"] = body["description"]
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail=f"Entity {entity_tag} not found")

    # Save updated config
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    return {"success": True}


@router.put("/path-data/pitch")
async def update_pitch_by_path(body: dict, path: str) -> dict:
    """Update pitch by full project path (path passed as query param)."""
    project_path = Path(path)

    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    pitch_path = project_path / "world_bible" / "pitch.md"
    pitch_path.parent.mkdir(parents=True, exist_ok=True)
    pitch_path.write_text(body.get("content", ""), encoding="utf-8")

    # Update last_modified in project.json
    config_file = project_path / "project.json"
    if config_file.exists():
        config = json.loads(config_file.read_text(encoding="utf-8"))
        config["last_modified"] = datetime.now().isoformat()
        config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")

    return {"success": True}


@router.get("/path-data/pitch")
async def get_pitch_by_path(path: str) -> dict:
    """Get pitch by full project path (path passed as query param)."""
    project_path = Path(path)
    pitch_path = project_path / "world_bible" / "pitch.md"

    if not pitch_path.exists():
        return {"content": ""}

    return {"content": pitch_path.read_text(encoding="utf-8")}


# General path-based endpoint for getting project info
@router.get("/by-path/{path:path}")
async def get_project_by_path(path: str) -> ProjectResponse:
    """Get a project by its full path."""
    project_path = Path(path)

    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    config = _load_project_config(project_path)
    status = _get_project_status(project_path)

    return ProjectResponse(
        name=config.get("name", project_path.name),
        path=str(project_path),
        created_at=config.get("created_at", ""),
        last_modified=config.get("last_modified", ""),
        **status
    )


# ============================================================================
# Name-based endpoints (must come AFTER /by-path routes)
# These use project name and look in the default projects directory
# ============================================================================

@router.get("/{project_name}")
async def get_project(project_name: str) -> ProjectResponse:
    """Get a specific project by name."""
    # Check default projects directory
    project_path = settings.projects_dir / project_name

    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    config = _load_project_config(project_path)
    status = _get_project_status(project_path)

    return ProjectResponse(
        name=config.get("name", project_name),
        path=str(project_path),
        created_at=config.get("created_at", ""),
        last_modified=config.get("last_modified", ""),
        **status
    )


@router.delete("/{project_name}")
async def delete_project(project_name: str):
    """Delete a project."""
    project_path = settings.projects_dir / project_name

    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    # Remove directory and all contents
    import shutil
    shutil.rmtree(project_path)

    return {"message": f"Project '{project_name}' deleted"}


@router.get("/{project_name}/pitch")
async def get_pitch(project_name: str) -> dict:
    """Get the pitch content for a project."""
    project_path = settings.projects_dir / project_name
    pitch_path = project_path / "world_bible" / "pitch.md"

    if not pitch_path.exists():
        return {"content": ""}

    return {"content": pitch_path.read_text(encoding="utf-8")}


@router.put("/{project_name}/pitch")
async def update_pitch(project_name: str, body: dict) -> dict:
    """Update the pitch content for a project."""
    project_path = settings.projects_dir / project_name

    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    pitch_path = project_path / "world_bible" / "pitch.md"
    pitch_path.write_text(body.get("content", ""), encoding="utf-8")

    # Update last_modified
    config = _load_project_config(project_path)
    config["last_modified"] = datetime.now().isoformat()
    _save_project_config(project_path, config)

    return {"success": True}


@router.get("/{project_name}/world-config")
async def get_world_config(project_name: str) -> dict:
    """Get the world config for a project."""
    project_path = settings.projects_dir / project_name
    config_path = project_path / "world_bible" / "world_config.json"

    if not config_path.exists():
        return {}

    return json.loads(config_path.read_text(encoding="utf-8"))


@router.get("/{project_name}/script")
async def get_script(project_name: str) -> dict:
    """Get the script content for a project."""
    project_path = settings.projects_dir / project_name
    script_path = project_path / "scripts" / "script.md"

    if not script_path.exists():
        return {"content": ""}

    return {"content": script_path.read_text(encoding="utf-8")}


@router.get("/{project_name}/visual-script")
async def get_visual_script(project_name: str) -> dict:
    """Get the visual script for a project."""
    project_path = settings.projects_dir / project_name
    vs_path = project_path / "storyboard" / "visual_script.json"

    if not vs_path.exists():
        return {}

    return json.loads(vs_path.read_text(encoding="utf-8"))


# =============================================================================
# Reference Generation Routes (path-based via query param)
# =============================================================================

@router.post("/path-data/references/generate")
async def generate_reference_by_path(body: dict, path: str) -> dict:
    """Generate a single entity's reference image by project path."""
    from greenlight.pipelines.references import ReferencesPipeline

    project_path = Path(path)
    world_config_path = project_path / "world_bible" / "world_config.json"

    tag = body.get("tag", "")
    model = body.get("model", "flux_2_pro")
    overwrite = body.get("overwrite", False)

    if not tag:
        return {"success": False, "error": "tag is required"}

    if not world_config_path.exists():
        return {"success": False, "error": "No world_config.json found"}

    world_config = json.loads(world_config_path.read_text(encoding="utf-8"))

    # Determine entity type
    entity_type = None
    for char in world_config.get("characters", []):
        if char.get("tag") == tag:
            entity_type = "character"
            break
    if not entity_type:
        for loc in world_config.get("locations", []):
            if loc.get("tag") == tag:
                entity_type = "location"
                break
    if not entity_type:
        for prop in world_config.get("props", []):
            if prop.get("tag") == tag:
                entity_type = "prop"
                break

    if not entity_type:
        return {"success": False, "error": f"Entity {tag} not found"}

    # Check if reference already exists
    refs_dir = project_path / "references"
    ref_path = refs_dir / f"{tag}.png"

    if ref_path.exists() and not overwrite:
        return {"success": True, "message": "Reference already exists", "path": str(ref_path)}

    try:
        pipeline = ReferencesPipeline(
            project_path=project_path,
            image_model=model,
        )

        result = await pipeline.generate_single(entity_type, tag)
        return result

    except Exception as e:
        return {"success": False, "error": str(e)}
