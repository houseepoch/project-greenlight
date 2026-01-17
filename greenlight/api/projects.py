"""
Projects API router.

CRUD operations for projects.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, File, UploadFile
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
    """Get world config by full project path (passed as query param).

    Dynamically adds imagePath for each entity based on whether
    the reference image exists in the references/ directory.
    """
    project_path = Path(path)
    config_path = project_path / "world_bible" / "world_config.json"

    if not config_path.exists():
        return {"characters": [], "locations": [], "props": [], "world_context": {}}

    world_config = json.loads(config_path.read_text(encoding="utf-8"))
    refs_dir = project_path / "references"

    # Add imagePath to each entity if reference image exists
    for entity_type in ["characters", "locations", "props"]:
        entities = world_config.get(entity_type, [])
        for entity in entities:
            tag = entity.get("tag", "")
            if tag:
                ref_path = refs_dir / f"{tag}.png"
                if ref_path.exists():
                    # Use absolute path for the image API
                    entity["imagePath"] = str(ref_path)
                else:
                    entity["imagePath"] = None

    return world_config


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
    """Update entity fields by full project path (path passed as query param).

    Searches in characters, locations, and props arrays for the entity.
    Updates any fields provided in the body.
    """
    project_path = Path(path)
    config_path = project_path / "world_bible" / "world_config.json"

    if not config_path.exists():
        raise HTTPException(status_code=404, detail="World config not found")

    config = json.loads(config_path.read_text(encoding="utf-8"))

    # Search in all entity arrays
    found = False
    for entity_type in ["characters", "locations", "props"]:
        entities = config.get(entity_type, [])
        for entity in entities:
            if entity.get("tag") == entity_tag:
                # Update all fields provided in body
                for field, value in body.items():
                    entity[field] = value
                found = True
                break
        if found:
            break

    if not found:
        raise HTTPException(status_code=404, detail=f"Entity {entity_tag} not found")

    # Save updated config
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    return {"success": True, "updated_fields": list(body.keys())}


@router.patch("/path-data/world/context/{field_key}")
async def update_world_context_field(field_key: str, body: dict, path: str) -> dict:
    """Update a single world context field by project path."""
    project_path = Path(path)
    config_path = project_path / "world_bible" / "world_config.json"

    if not config_path.exists():
        raise HTTPException(status_code=404, detail="World config not found")

    config = json.loads(config_path.read_text(encoding="utf-8"))

    # Ensure world_context exists
    if "world_context" not in config:
        config["world_context"] = {}

    # Valid field keys
    valid_fields = {
        "setting", "time_period", "cultural_context", "social_structure",
        "technology_level", "clothing_norms", "architecture_style",
        "color_palette", "lighting_style", "mood"
    }

    if field_key not in valid_fields:
        raise HTTPException(status_code=400, detail=f"Invalid field key: {field_key}")

    # Update the field
    new_value = body.get("value", "")
    config["world_context"][field_key] = new_value

    # Save updated config
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    return {"success": True, "field": field_key, "value": new_value}


@router.put("/path-data/visual-style")
async def update_visual_style(body: dict, path: str) -> dict:
    """Update the visual style of a project by project path."""
    project_path = Path(path)
    config_path = project_path / "world_bible" / "world_config.json"

    new_style = body.get("visual_style", "live_action")

    # Valid visual styles
    valid_styles = {
        "live_action", "anime", "animation_2d", "animation_3d",
        "cartoon", "claymation", "mixed"
    }

    if new_style not in valid_styles:
        raise HTTPException(status_code=400, detail=f"Invalid visual style: {new_style}")

    # Update world_config.json if it exists
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["visual_style"] = new_style
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    # Also update project.json
    project_config_path = project_path / "project.json"
    if project_config_path.exists():
        project_config = json.loads(project_config_path.read_text(encoding="utf-8"))
        project_config["visual_style"] = new_style
        project_config["last_modified"] = datetime.now().isoformat()
        project_config_path.write_text(json.dumps(project_config, indent=2), encoding="utf-8")

    return {"success": True, "visual_style": new_style}


@router.delete("/path-data/project")
async def delete_project_by_path(path: str) -> dict:
    """Delete a project by full project path (passed as query param).

    This permanently removes the project directory and all its contents.
    """
    import shutil

    project_path = Path(path)

    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    # Verify it's actually a project directory (has project.json)
    if not (project_path / "project.json").exists():
        raise HTTPException(status_code=400, detail="Not a valid project directory")

    # Remove directory and all contents
    shutil.rmtree(project_path)

    return {"success": True, "message": f"Project deleted: {project_path.name}"}


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


# =============================================================================
# URL-path-based storyboard routes (for frontend that sends encoded paths in URL)
# Pattern: /encoded_path/storyboard where encoded_path could be full project path
# =============================================================================

@router.get("/{project_path:path}/storyboard")
async def get_storyboard_by_url_path(project_path: str) -> dict:
    """Get storyboard frames and visual script.

    Handles both project names and full paths (URL-decoded).
    Returns frames from prompts.json (card UI format) and visual_script.json.
    """
    from urllib.parse import unquote

    # URL decode the path
    decoded_path = unquote(project_path)

    # Check if it's a full path or just a project name
    path_obj = Path(decoded_path)
    if path_obj.is_absolute() and path_obj.exists():
        project_dir = path_obj
    else:
        # Try as project name in default directory
        project_dir = settings.projects_dir / decoded_path

    storyboard_dir = project_dir / "storyboard"
    output_dir = project_dir / "storyboard_output" / "generated"

    frames = []
    visual_script = None

    # Load prompts.json (preferred) or generate from visual_script.json
    prompts_path = storyboard_dir / "prompts.json"
    vs_path = storyboard_dir / "visual_script.json"

    if prompts_path.exists():
        prompts_data = json.loads(prompts_path.read_text(encoding="utf-8"))
        # Handle both list format (new) and dict format (legacy)
        prompts_list = prompts_data if isinstance(prompts_data, list) else prompts_data.get("prompts", [])

        for prompt in prompts_list:
            frame_id = prompt.get("frame_id", "")
            # Parse frame_id: [scene.frame.camera] format
            # Remove brackets and split
            clean_id = frame_id.strip("[]")
            parts = clean_id.split(".")
            scene_num = int(parts[0]) if parts else 1
            frame_num = int(parts[1]) if len(parts) > 1 else 1
            camera = parts[2] if len(parts) > 2 else "cA"

            # Check if image exists
            image_path = output_dir / f"{clean_id}.png"
            if not image_path.exists():
                # Try alternative naming
                image_path = output_dir / f"{frame_id}.png"

            frames.append({
                "id": frame_id,
                "scene": scene_num,
                "frame": frame_num,
                "camera": camera,
                "prompt": prompt.get("prompt", ""),
                "imagePath": str(image_path) if image_path.exists() else None,
                "tags": _extract_tags_from_prompt(prompt),
                "camera_notation": prompt.get("shot_type", "MS"),
                "characters": prompt.get("characters", []),
                "generated": prompt.get("generated", image_path.exists()),
                "word_count": prompt.get("word_count", len(prompt.get("prompt", "").split())),
            })

    # Load visual_script for scene metadata
    if vs_path.exists():
        visual_script = json.loads(vs_path.read_text(encoding="utf-8"))

    return {
        "frames": frames,
        "visual_script": visual_script,
    }


def _extract_tags_from_prompt(prompt: dict) -> list[str]:
    """Extract all tags from a prompt's characters, locations, etc."""
    tags = []
    characters = prompt.get("characters", [])
    if isinstance(characters, list):
        tags.extend(characters)
    # Add location tags if present
    if prompt.get("location"):
        tags.append(prompt.get("location"))
    return tags


@router.post("/{project_path:path}/storyboard/frame/update-prompt")
async def update_frame_prompt_by_url_path(project_path: str, body: dict) -> dict:
    """Update a single frame's prompt by URL path."""
    from urllib.parse import unquote

    decoded_path = unquote(project_path)
    path_obj = Path(decoded_path)
    if path_obj.is_absolute() and path_obj.exists():
        project_dir = path_obj
    else:
        project_dir = settings.projects_dir / decoded_path

    prompts_path = project_dir / "storyboard" / "prompts.json"

    frame_id = body.get("frame_id", "")
    new_prompt = body.get("prompt", "")

    if not frame_id:
        return {"success": False, "error": "frame_id is required"}

    if not prompts_path.exists():
        return {"success": False, "error": "No prompts.json found"}

    prompts_data = json.loads(prompts_path.read_text(encoding="utf-8"))
    prompts_list = prompts_data if isinstance(prompts_data, list) else prompts_data.get("prompts", [])

    # Find and update the frame
    updated = False
    for prompt in prompts_list:
        if prompt.get("frame_id") == frame_id:
            prompt["prompt"] = new_prompt
            prompt["word_count"] = len(new_prompt.split())
            prompt["generated"] = False  # Mark as not generated since prompt changed
            updated = True
            break

    if not updated:
        return {"success": False, "error": f"Frame {frame_id} not found"}

    # Save updated prompts
    if isinstance(prompts_data, list):
        prompts_path.write_text(json.dumps(prompts_list, indent=2), encoding="utf-8")
    else:
        prompts_data["prompts"] = prompts_list
        prompts_path.write_text(json.dumps(prompts_data, indent=2), encoding="utf-8")

    return {"success": True, "message": f"Updated prompt for {frame_id}"}


@router.post("/{project_path:path}/storyboard/frame/regenerate")
async def regenerate_frame_by_url_path(project_path: str, body: dict) -> dict:
    """Regenerate a single storyboard frame by URL path."""
    from urllib.parse import unquote
    from greenlight.pipelines.storyboard import StoryboardPipeline

    decoded_path = unquote(project_path)
    path_obj = Path(decoded_path)
    if path_obj.is_absolute() and path_obj.exists():
        project_dir = path_obj
    else:
        project_dir = settings.projects_dir / decoded_path

    frame_id = body.get("frame_id", "")

    if not frame_id:
        return {"success": False, "error": "frame_id is required"}

    try:
        pipeline = StoryboardPipeline(
            project_path=project_dir,
            image_model=body.get("image_model", "flux_2_pro"),
        )

        result = await pipeline.generate_single_frame(frame_id, force=True)
        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


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
# Storyboard Routes (path-based via query param)
# =============================================================================

@router.get("/path-data/storyboard")
async def get_storyboard_by_path(path: str) -> dict:
    """Get storyboard frames and visual script by project path.

    Returns frames from prompts.json (card UI format) and visual_script.json.
    Frames include generated status and image paths.
    """
    project_path = Path(path)
    storyboard_dir = project_path / "storyboard"
    output_dir = project_path / "storyboard_output" / "generated"

    frames = []
    visual_script = None

    # Load prompts.json (preferred) or generate from visual_script.json
    prompts_path = storyboard_dir / "prompts.json"
    vs_path = storyboard_dir / "visual_script.json"

    if prompts_path.exists():
        prompts_data = json.loads(prompts_path.read_text(encoding="utf-8"))
        # Handle both list format (new) and dict format (legacy)
        prompts_list = prompts_data if isinstance(prompts_data, list) else prompts_data.get("prompts", [])

        for prompt in prompts_list:
            frame_id = prompt.get("frame_id", "")
            # Parse frame_id: [scene.frame.camera] format
            # Remove brackets and split
            clean_id = frame_id.strip("[]")
            parts = clean_id.split(".")
            scene_num = int(parts[0]) if parts else 1
            frame_num = int(parts[1]) if len(parts) > 1 else 1
            camera = parts[2] if len(parts) > 2 else "cA"

            # Check if image exists
            image_path = output_dir / f"{clean_id}.png"
            if not image_path.exists():
                # Try alternative naming
                image_path = output_dir / f"{frame_id}.png"

            frames.append({
                "id": frame_id,
                "scene": scene_num,
                "frame": frame_num,
                "camera": camera,
                "prompt": prompt.get("prompt", ""),
                "imagePath": str(image_path) if image_path.exists() else None,
                "tags": _extract_tags(prompt),
                "camera_notation": prompt.get("shot_type", "MS"),
                "characters": prompt.get("characters", []),
                "generated": prompt.get("generated", image_path.exists()),
                "word_count": prompt.get("word_count", len(prompt.get("prompt", "").split())),
            })

    # Load visual_script for scene metadata
    if vs_path.exists():
        visual_script = json.loads(vs_path.read_text(encoding="utf-8"))

    return {
        "frames": frames,
        "visual_script": visual_script,
    }


def _extract_tags(prompt: dict) -> list[str]:
    """Extract all tags from a prompt's characters, locations, etc."""
    tags = []
    characters = prompt.get("characters", [])
    if isinstance(characters, list):
        tags.extend(characters)
    # Add location tags if present
    if prompt.get("location"):
        tags.append(prompt.get("location"))
    return tags


@router.post("/path-data/storyboard/frame/update-prompt")
async def update_frame_prompt_by_path(body: dict, path: str) -> dict:
    """Update a single frame's prompt by project path."""
    project_path = Path(path)
    prompts_path = project_path / "storyboard" / "prompts.json"

    frame_id = body.get("frame_id", "")
    new_prompt = body.get("prompt", "")

    if not frame_id:
        return {"success": False, "error": "frame_id is required"}

    if not prompts_path.exists():
        return {"success": False, "error": "No prompts.json found"}

    prompts_data = json.loads(prompts_path.read_text(encoding="utf-8"))
    prompts_list = prompts_data if isinstance(prompts_data, list) else prompts_data.get("prompts", [])

    # Find and update the frame
    updated = False
    for prompt in prompts_list:
        if prompt.get("frame_id") == frame_id:
            prompt["prompt"] = new_prompt
            prompt["word_count"] = len(new_prompt.split())
            prompt["generated"] = False  # Mark as not generated since prompt changed
            updated = True
            break

    if not updated:
        return {"success": False, "error": f"Frame {frame_id} not found"}

    # Save updated prompts
    if isinstance(prompts_data, list):
        prompts_path.write_text(json.dumps(prompts_list, indent=2), encoding="utf-8")
    else:
        prompts_data["prompts"] = prompts_list
        prompts_path.write_text(json.dumps(prompts_data, indent=2), encoding="utf-8")

    return {"success": True, "message": f"Updated prompt for {frame_id}"}


@router.post("/path-data/storyboard/frame/regenerate")
async def regenerate_frame_by_path(body: dict, path: str) -> dict:
    """Regenerate a single storyboard frame by project path."""
    from greenlight.pipelines.storyboard import StoryboardPipeline

    project_path = Path(path)
    frame_id = body.get("frame_id", "")

    if not frame_id:
        return {"success": False, "error": "frame_id is required"}

    try:
        pipeline = StoryboardPipeline(
            project_path=project_path,
            image_model=body.get("image_model", "flux_2_pro"),
        )

        result = await pipeline.generate_single_frame(frame_id, force=True)
        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# Reference Generation Routes (path-based via query param)
# =============================================================================

@router.post("/path-data/references/upload")
async def upload_reference_by_path(
    file: UploadFile = File(...),
    path: str = "",
    tag: str = "",
) -> dict:
    """Upload a reference image for an entity by project path.

    Accepts PNG, JPEG, and WebP images.
    Saves as {tag}.png in the references directory.
    """
    import shutil
    from PIL import Image
    import io

    if not path:
        return {"success": False, "error": "path is required"}

    if not tag:
        return {"success": False, "error": "tag is required"}

    project_path = Path(path)
    refs_dir = project_path / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)

    # Validate file type
    valid_types = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
    if file.content_type not in valid_types:
        return {"success": False, "error": f"Invalid file type: {file.content_type}. Accepts PNG, JPEG, WebP."}

    try:
        # Read file content
        content = await file.read()

        # Open image and convert to PNG
        image = Image.open(io.BytesIO(content))

        # Convert to RGB if necessary (for RGBA or palette images)
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')

        # Save as PNG
        ref_path = refs_dir / f"{tag}.png"
        image.save(ref_path, 'PNG')

        return {
            "success": True,
            "message": f"Reference uploaded for {tag}",
            "path": str(ref_path),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/path-data/references/generate")
async def generate_reference_by_path(body: dict, path: str) -> dict:
    """Generate a single entity's reference image by project path."""
    from greenlight.pipelines.references import ReferencesPipeline

    project_path = Path(path)
    world_config_path = project_path / "world_bible" / "world_config.json"

    tag = body.get("tag", "")
    model = body.get("model", "z_image_turbo")
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


# =============================================================================
# Checkpoint and Version Control Routes
# =============================================================================

@router.get("/{project_path:path}/storyboard/checkpoints")
async def get_checkpoints(project_path: str) -> dict:
    """Get all checkpoints and storage stats for a project."""
    from urllib.parse import unquote
    from greenlight.core.checkpoints import CheckpointService

    decoded_path = unquote(project_path)
    path_obj = Path(decoded_path)
    if path_obj.is_absolute() and path_obj.exists():
        project_dir = path_obj
    else:
        project_dir = settings.projects_dir / decoded_path

    service = CheckpointService(project_dir)
    checkpoints = service.get_all_checkpoints()
    storage = service.get_storage_stats()

    return {
        "checkpoints": [cp.model_dump() for cp in checkpoints],
        "storage": storage.model_dump(),
    }


@router.post("/{project_path:path}/storyboard/checkpoints/create")
async def create_checkpoint(project_path: str, body: dict) -> dict:
    """Create a new checkpoint of current project state."""
    from urllib.parse import unquote
    from greenlight.core.checkpoints import CheckpointService

    decoded_path = unquote(project_path)
    path_obj = Path(decoded_path)
    if path_obj.is_absolute() and path_obj.exists():
        project_dir = path_obj
    else:
        project_dir = settings.projects_dir / decoded_path

    name = body.get("name", f"Checkpoint {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    description = body.get("description", "")

    service = CheckpointService(project_dir)
    checkpoint = service.create_checkpoint(
        name=name,
        description=description,
    )

    return {
        "success": True,
        "checkpoint": checkpoint.model_dump(),
    }


@router.post("/{project_path:path}/storyboard/checkpoints/restore")
async def restore_checkpoint(project_path: str, body: dict) -> dict:
    """Restore project to a checkpoint state."""
    from urllib.parse import unquote
    from greenlight.core.checkpoints import CheckpointService

    decoded_path = unquote(project_path)
    path_obj = Path(decoded_path)
    if path_obj.is_absolute() and path_obj.exists():
        project_dir = path_obj
    else:
        project_dir = settings.projects_dir / decoded_path

    checkpoint_id = body.get("checkpoint_id", "")
    if not checkpoint_id:
        return {"success": False, "error": "checkpoint_id is required"}

    service = CheckpointService(project_dir)
    result = service.restore_checkpoint(checkpoint_id)

    return result


@router.delete("/{project_path:path}/storyboard/checkpoints/{checkpoint_id}")
async def delete_checkpoint(project_path: str, checkpoint_id: str) -> dict:
    """Delete a checkpoint."""
    from urllib.parse import unquote
    from greenlight.core.checkpoints import CheckpointService

    decoded_path = unquote(project_path)
    path_obj = Path(decoded_path)
    if path_obj.is_absolute() and path_obj.exists():
        project_dir = path_obj
    else:
        project_dir = settings.projects_dir / decoded_path

    service = CheckpointService(project_dir)
    result = service.delete_checkpoint(checkpoint_id)

    return result


@router.get("/{project_path:path}/storyboard/versions")
async def get_frame_versions(project_path: str) -> dict:
    """Get all frame versions for a project."""
    from urllib.parse import unquote
    from greenlight.core.checkpoints import CheckpointService

    decoded_path = unquote(project_path)
    path_obj = Path(decoded_path)
    if path_obj.is_absolute() and path_obj.exists():
        project_dir = path_obj
    else:
        project_dir = settings.projects_dir / decoded_path

    service = CheckpointService(project_dir)
    frame_versions = service.get_all_frame_versions()

    # Convert to serializable format
    frames = {}
    for frame_id, versions in frame_versions.items():
        frames[frame_id] = [v.model_dump() for v in versions]

    return {"frames": frames}


@router.post("/{project_path:path}/storyboard/versions/restore")
async def restore_frame_version(project_path: str, body: dict) -> dict:
    """Restore a single frame to a previous version."""
    from urllib.parse import unquote
    from greenlight.core.checkpoints import CheckpointService

    decoded_path = unquote(project_path)
    path_obj = Path(decoded_path)
    if path_obj.is_absolute() and path_obj.exists():
        project_dir = path_obj
    else:
        project_dir = settings.projects_dir / decoded_path

    frame_id = body.get("frame_id", "")
    version_id = body.get("version_id", "")

    if not frame_id or not version_id:
        return {"success": False, "error": "frame_id and version_id are required"}

    service = CheckpointService(project_dir)
    result = service.restore_frame_version(frame_id, version_id)

    return result


@router.get("/{project_path:path}/storyboard/versions/image/{version_id}")
async def get_version_image(project_path: str, version_id: str, thumbnail: bool = False):
    """Get a version's image or thumbnail."""
    from urllib.parse import unquote
    from fastapi.responses import FileResponse
    from greenlight.core.checkpoints import CheckpointService

    decoded_path = unquote(project_path)
    path_obj = Path(decoded_path)
    if path_obj.is_absolute() and path_obj.exists():
        project_dir = path_obj
    else:
        project_dir = settings.projects_dir / decoded_path

    service = CheckpointService(project_dir)
    image_path = service.get_version_image_path(version_id, thumbnail=thumbnail)

    if not image_path or not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    media_type = "image/jpeg" if thumbnail else "image/png"
    return FileResponse(image_path, media_type=media_type)
