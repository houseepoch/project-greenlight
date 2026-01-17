"""
Pipelines API router.

Handles all pipeline operations: writer, director, references, storyboard.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from greenlight.core.models import PipelineStatus, PipelineStage, StageInfo

router = APIRouter()

# In-memory pipeline status storage
# In production, this could be Redis or a database
pipeline_status: dict[str, dict] = {}


class PipelineRequest(BaseModel):
    """Request to start a pipeline."""
    project_path: str
    llm: str = "claude-haiku-4.5"
    image_model: str = "flux_2_pro"
    max_frames: Optional[int] = None
    media_type: str = "standard"
    visual_style: str = "live_action"
    style_notes: str = ""
    scene_filter: Optional[list[int]] = None  # Generate only specific scenes
    entity_filter: Optional[list[str]] = None  # Generate only specific entity tags


class PipelineResponse(BaseModel):
    """Response from pipeline operations."""
    success: bool
    message: str
    pipeline_id: Optional[str] = None


# =============================================================================
# STATUS TRACKING HELPERS
# =============================================================================

def _init_status(pipeline_id: str, name: str, stages: list[str]):
    """Initialize pipeline status."""
    pipeline_status[pipeline_id] = {
        "name": name,
        "status": PipelineStage.RUNNING.value,
        "progress": 0.0,
        "message": "Starting...",
        "logs": [f"Starting {name} pipeline..."],
        "stages": [{"name": s, "status": PipelineStage.PENDING.value} for s in stages],
        "current_stage": None,
        "total_items": 0,
        "completed_items": 0,
        "current_item": None,
    }


def _add_log(pipeline_id: str, message: str):
    """Add a log message."""
    if pipeline_id in pipeline_status:
        pipeline_status[pipeline_id]["logs"].append(message)
        pipeline_status[pipeline_id]["message"] = message


def _set_stage(pipeline_id: str, stage_name: str, status: str, message: str = None):
    """Update a stage's status."""
    if pipeline_id not in pipeline_status:
        return

    ps = pipeline_status[pipeline_id]
    for stage in ps["stages"]:
        if stage["name"] == stage_name:
            stage["status"] = status
            if message:
                stage["message"] = message
            if status == PipelineStage.RUNNING.value:
                stage["started_at"] = datetime.now().isoformat()
                ps["current_stage"] = stage_name
            elif status in [PipelineStage.COMPLETE.value, PipelineStage.ERROR.value]:
                stage["completed_at"] = datetime.now().isoformat()
            break


def _set_progress(pipeline_id: str, progress: float):
    """Update progress (0.0 to 1.0)."""
    if pipeline_id in pipeline_status:
        pipeline_status[pipeline_id]["progress"] = min(1.0, max(0.0, progress))


def _complete(pipeline_id: str, success: bool = True, error: str = None):
    """Mark pipeline as complete."""
    if pipeline_id in pipeline_status:
        ps = pipeline_status[pipeline_id]
        ps["status"] = PipelineStage.COMPLETE.value if success else PipelineStage.ERROR.value
        ps["progress"] = 1.0 if success else ps["progress"]
        if error:
            ps["error"] = error


# =============================================================================
# STATUS ENDPOINTS
# =============================================================================

@router.get("/status/{pipeline_id:path}")
async def get_pipeline_status(pipeline_id: str):
    """Get status of a pipeline by ID."""
    if pipeline_id in pipeline_status:
        return pipeline_status[pipeline_id]
    return {
        "name": pipeline_id,
        "status": PipelineStage.IDLE.value,
        "progress": 0,
        "message": "",
        "logs": [],
    }


@router.post("/cancel/{pipeline_id:path}")
async def cancel_pipeline(pipeline_id: str):
    """Cancel a running pipeline."""
    if pipeline_id in pipeline_status:
        current = pipeline_status[pipeline_id].get("status", "")
        if current == PipelineStage.RUNNING.value:
            pipeline_status[pipeline_id]["status"] = PipelineStage.CANCELLED.value
            _add_log(pipeline_id, "Cancellation requested by user")
            return {"success": True, "message": "Cancellation requested"}
        return {"success": False, "message": f"Pipeline not running (status: {current})"}
    return {"success": False, "message": "Pipeline not found"}


# =============================================================================
# WRITER PIPELINE
# =============================================================================

@router.post("/writer")
async def run_writer_pipeline(
    request: PipelineRequest,
    background_tasks: BackgroundTasks
) -> PipelineResponse:
    """
    Run the Writer pipeline.

    Generates world config and script from pitch.
    """
    pipeline_id = f"writer_{request.project_path}"
    _init_status(pipeline_id, "writer", [
        "Load Pitch",
        "Extract World Config",
        "Generate Script",
        "Save Outputs"
    ])

    background_tasks.add_task(
        _execute_writer_pipeline,
        pipeline_id,
        request
    )

    return PipelineResponse(
        success=True,
        message="Writer pipeline started",
        pipeline_id=pipeline_id
    )


async def _execute_writer_pipeline(pipeline_id: str, request: PipelineRequest):
    """Execute the writer pipeline."""
    from greenlight.pipelines.writer import WriterPipeline

    try:
        pipeline = WriterPipeline(
            project_path=Path(request.project_path),
            llm_model=request.llm,
            visual_style=request.visual_style,
            style_notes=request.style_notes,
            media_type=request.media_type,
            log_callback=lambda msg: _add_log(pipeline_id, msg),
            stage_callback=lambda name, status, msg=None: _set_stage(pipeline_id, name, status, msg),
            progress_callback=lambda p: _set_progress(pipeline_id, p),
        )

        result = await pipeline.run()

        if result["success"]:
            _complete(pipeline_id, success=True)
            _add_log(pipeline_id, "Writer pipeline complete!")
        else:
            _complete(pipeline_id, success=False, error=result.get("error", "Unknown error"))
            _add_log(pipeline_id, f"Writer pipeline failed: {result.get('error')}")

    except Exception as e:
        _complete(pipeline_id, success=False, error=str(e))
        _add_log(pipeline_id, f"Error: {str(e)}")


# =============================================================================
# DIRECTOR PIPELINE
# =============================================================================

@router.post("/director")
async def run_director_pipeline(
    request: PipelineRequest,
    background_tasks: BackgroundTasks
) -> PipelineResponse:
    """
    Run the Director pipeline.

    Transforms confirmed outline beats into visual frames with cinematic prompts.
    Each beat becomes a scene with 2-5 frames for image generation.
    """
    pipeline_id = f"director_{request.project_path}"
    _init_status(pipeline_id, "director", [
        "Load Confirmed Outline",
        "Load World Config",
        "Generate Frames",
        "Save Outputs"
    ])

    background_tasks.add_task(
        _execute_director_pipeline,
        pipeline_id,
        request
    )

    return PipelineResponse(
        success=True,
        message="Director pipeline started",
        pipeline_id=pipeline_id
    )


async def _execute_director_pipeline(pipeline_id: str, request: PipelineRequest):
    """Execute the director pipeline."""
    from greenlight.pipelines.director import DirectorPipeline

    try:
        pipeline = DirectorPipeline(
            project_path=Path(request.project_path),
            llm_model=request.llm,
            max_frames=request.max_frames,
            log_callback=lambda msg: _add_log(pipeline_id, msg),
            stage_callback=lambda name, status, msg=None: _set_stage(pipeline_id, name, status, msg),
            progress_callback=lambda p: _set_progress(pipeline_id, p),
        )

        result = await pipeline.run()

        if result["success"]:
            _complete(pipeline_id, success=True)
            _add_log(pipeline_id, f"Director complete! {result.get('total_frames', 0)} frames generated.")
        else:
            _complete(pipeline_id, success=False, error=result.get("error", "Unknown error"))
            _add_log(pipeline_id, f"Director pipeline failed: {result.get('error')}")

    except Exception as e:
        _complete(pipeline_id, success=False, error=str(e))
        _add_log(pipeline_id, f"Error: {str(e)}")


# =============================================================================
# REFERENCES PIPELINE
# =============================================================================

@router.post("/references")
async def run_references_pipeline(
    request: PipelineRequest,
    background_tasks: BackgroundTasks
) -> PipelineResponse:
    """
    Run the References pipeline.

    Generates reference images for characters, locations, and props.
    """
    pipeline_id = f"references_{request.project_path}"
    _init_status(pipeline_id, "references", [
        "Load World Config",
        "Character References",
        "Location References",
        "Prop References"
    ])

    background_tasks.add_task(
        _execute_references_pipeline,
        pipeline_id,
        request
    )

    return PipelineResponse(
        success=True,
        message="References pipeline started",
        pipeline_id=pipeline_id
    )


async def _execute_references_pipeline(pipeline_id: str, request: PipelineRequest):
    """Execute the references pipeline."""
    from greenlight.pipelines.references import ReferencesPipeline

    try:
        pipeline = ReferencesPipeline(
            project_path=Path(request.project_path),
            image_model=request.image_model,
            entity_filter=request.entity_filter,
            log_callback=lambda msg: _add_log(pipeline_id, msg),
            stage_callback=lambda name, status, msg=None: _set_stage(pipeline_id, name, status, msg),
            progress_callback=lambda p: _set_progress(pipeline_id, p),
        )

        result = await pipeline.run()

        if result["success"]:
            _complete(pipeline_id, success=True)
            _add_log(pipeline_id, f"References complete! {result.get('generated', 0)} images generated.")
        else:
            _complete(pipeline_id, success=False, error=result.get("error", "Unknown error"))
            _add_log(pipeline_id, f"References pipeline failed: {result.get('error')}")

    except Exception as e:
        _complete(pipeline_id, success=False, error=str(e))
        _add_log(pipeline_id, f"Error: {str(e)}")


# =============================================================================
# STORYBOARD PIPELINE
# =============================================================================

@router.post("/storyboard")
async def run_storyboard_pipeline(
    request: PipelineRequest,
    background_tasks: BackgroundTasks
) -> PipelineResponse:
    """
    Run the Storyboard pipeline.

    Generates storyboard images from visual script.
    """
    pipeline_id = f"storyboard_{request.project_path}"
    _init_status(pipeline_id, "storyboard", [
        "Load Visual Script",
        "Prepare Prompts",
        "Generate Images",
        "Save Outputs"
    ])

    background_tasks.add_task(
        _execute_storyboard_pipeline,
        pipeline_id,
        request
    )

    return PipelineResponse(
        success=True,
        message="Storyboard pipeline started",
        pipeline_id=pipeline_id
    )


async def _execute_storyboard_pipeline(pipeline_id: str, request: PipelineRequest):
    """Execute the storyboard pipeline."""
    from greenlight.pipelines.storyboard import StoryboardPipeline

    try:
        # Update status tracking for item progress
        def update_item_progress(completed: int, total: int, current: str = None):
            if pipeline_id in pipeline_status:
                ps = pipeline_status[pipeline_id]
                ps["completed_items"] = completed
                ps["total_items"] = total
                if current:
                    ps["current_item"] = current
                # Auto-calculate progress
                if total > 0:
                    ps["progress"] = 0.1 + (completed / total) * 0.85

        pipeline = StoryboardPipeline(
            project_path=Path(request.project_path),
            image_model=request.image_model,
            max_frames=request.max_frames,
            scene_filter=request.scene_filter,
            log_callback=lambda msg: _add_log(pipeline_id, msg),
            stage_callback=lambda name, status, msg=None: _set_stage(pipeline_id, name, status, msg),
            progress_callback=lambda p: _set_progress(pipeline_id, p),
            item_callback=update_item_progress,
        )

        # Check for cancellation during execution
        def check_cancelled():
            return pipeline_status.get(pipeline_id, {}).get("status") == PipelineStage.CANCELLED.value

        result = await pipeline.run(check_cancelled=check_cancelled)

        if result.get("cancelled"):
            _add_log(pipeline_id, f"Storyboard cancelled after {result.get('completed', 0)} frames.")
        elif result["success"]:
            _complete(pipeline_id, success=True)
            _add_log(pipeline_id, f"Storyboard complete! {result.get('completed', 0)}/{result.get('total', 0)} frames generated.")
        else:
            _complete(pipeline_id, success=False, error=result.get("error", "Unknown error"))
            _add_log(pipeline_id, f"Storyboard pipeline failed: {result.get('error')}")

    except Exception as e:
        _complete(pipeline_id, success=False, error=str(e))
        _add_log(pipeline_id, f"Error: {str(e)}")


# =============================================================================
# OUTLINE GENERATOR PIPELINE
# =============================================================================

@router.post("/outline-generator")
async def run_outline_generator(
    request: PipelineRequest,
    background_tasks: BackgroundTasks
) -> PipelineResponse:
    """
    Generate 3 story outline variants from world_config.json.

    Each variant uses a different narrative approach:
    - Dramatic Arc: Classic three-act structure
    - Mystery Unfolding: Revelation-based progression
    - Character Journey: Internal transformation focus

    Requires: world_config.json from World Builder phase.
    Outputs: outline_variants.json with 3 variants for user selection.
    """
    pipeline_id = f"outline_generator_{request.project_path}"
    _init_status(pipeline_id, "outline_generator", [
        "Load World Config",
        "Generate Dramatic Arc",
        "Generate Mystery Unfolding",
        "Generate Character Journey",
        "Save Variants"
    ])

    background_tasks.add_task(
        _execute_outline_generator,
        pipeline_id,
        request
    )

    return PipelineResponse(
        success=True,
        message="Outline Generator started",
        pipeline_id=pipeline_id
    )


async def _execute_outline_generator(pipeline_id: str, request: PipelineRequest):
    """Execute the outline generator pipeline."""
    from greenlight.pipelines.outline_generator import OutlineGeneratorPipeline

    try:
        # Track variant completion
        def variant_callback(name: str, description: str, beats: list):
            _add_log(pipeline_id, f"[OK] {name}: {len(beats)} beats")

        pipeline = OutlineGeneratorPipeline(
            project_path=Path(request.project_path),
            log_callback=lambda msg: _add_log(pipeline_id, msg),
            progress_callback=lambda p: _set_progress(pipeline_id, p),
            variant_callback=variant_callback,
        )

        _set_stage(pipeline_id, "Load World Config", PipelineStage.RUNNING.value)

        result = await pipeline.run()

        if result["success"]:
            _complete(pipeline_id, success=True)
            variants_info = result.get("variants", {})
            total_beats = sum(v.get("beat_count", 0) for v in variants_info.values())
            _add_log(pipeline_id, f"Generated 3 variants with {total_beats} total beats")
            # Store variants info
            pipeline_status[pipeline_id]["variants"] = variants_info
        else:
            _complete(pipeline_id, success=False, error=result.get("error", "Unknown error"))
            _add_log(pipeline_id, f"Outline generation failed: {result.get('error')}")

    except Exception as e:
        _complete(pipeline_id, success=False, error=str(e))
        _add_log(pipeline_id, f"Error: {str(e)}")


# =============================================================================
# OUTLINE MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/outlines/{project_path:path}")
async def get_outline_variants(project_path: str):
    """Get the generated outline variants for selection."""
    import json

    project_dir = Path(project_path)
    outlines_path = project_dir / "outlines" / "outline_variants.json"

    if not outlines_path.exists():
        return {
            "success": False,
            "error": "No outlines found. Run outline generator first.",
        }

    try:
        data = json.loads(outlines_path.read_text(encoding="utf-8"))
        return {
            "success": True,
            "data": data,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


class SelectVariantRequest(BaseModel):
    """Request to select an outline variant."""
    project_path: str
    variant_key: str


@router.post("/outlines/select")
async def select_outline_variant(request: SelectVariantRequest):
    """Select a variant as the starting point for editing."""
    import json

    project_dir = Path(request.project_path)
    variant_key = request.variant_key
    outlines_path = project_dir / "outlines" / "outline_variants.json"

    if not outlines_path.exists():
        return {"success": False, "error": "No outlines found"}

    try:
        data = json.loads(outlines_path.read_text(encoding="utf-8"))

        if variant_key not in data.get("variants", {}):
            return {"success": False, "error": f"Unknown variant: {variant_key}"}

        # Set selected variant and copy beats to confirmed_beats
        data["selected_variant"] = variant_key
        data["confirmed_beats"] = data["variants"][variant_key]["beats"].copy()
        data["status"] = "editing"

        outlines_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        return {
            "success": True,
            "message": f"Selected {variant_key} variant",
            "beats": data["confirmed_beats"],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


class UpdateBeatsRequest(BaseModel):
    """Request to update outline beats."""
    project_path: str
    beats: list[str] = []


@router.post("/outlines/update-beats")
async def update_outline_beats(request: UpdateBeatsRequest):
    """Update the confirmed beats (after user editing)."""
    import json

    project_dir = Path(request.project_path)
    beats = request.beats
    outlines_path = project_dir / "outlines" / "outline_variants.json"

    if not outlines_path.exists():
        return {"success": False, "error": "No outlines found"}

    try:
        data = json.loads(outlines_path.read_text(encoding="utf-8"))
        data["confirmed_beats"] = beats
        data["status"] = "editing"

        outlines_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        return {
            "success": True,
            "message": f"Updated {len(beats)} beats",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


class ConfirmOutlineRequest(BaseModel):
    """Request to confirm an outline."""
    project_path: str


@router.post("/outlines/confirm")
async def confirm_outline(request: ConfirmOutlineRequest):
    """Confirm the outline and prepare for Director pipeline."""
    import json
    from datetime import datetime

    project_dir = Path(request.project_path)
    outlines_path = project_dir / "outlines" / "outline_variants.json"

    if not outlines_path.exists():
        return {"success": False, "error": "No outlines found"}

    try:
        data = json.loads(outlines_path.read_text(encoding="utf-8"))

        if not data.get("confirmed_beats"):
            return {"success": False, "error": "No beats to confirm. Select a variant first."}

        # Mark as confirmed
        data["status"] = "confirmed"
        data["confirmed_at"] = datetime.now().isoformat()

        outlines_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        # Save a clean confirmed_outline.json for Director
        confirmed_path = project_dir / "outlines" / "confirmed_outline.json"
        confirmed_path.write_text(json.dumps({
            "title": data.get("title", "Untitled"),
            "beats": data["confirmed_beats"],
            "confirmed_at": data["confirmed_at"],
        }, indent=2), encoding="utf-8")

        return {
            "success": True,
            "message": f"Outline confirmed with {len(data['confirmed_beats'])} beats",
            "confirmed_path": str(confirmed_path),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# WORLD BUILDER PIPELINE
# =============================================================================

@router.post("/world-builder")
async def run_world_builder_pipeline(
    request: PipelineRequest,
    background_tasks: BackgroundTasks
) -> PipelineResponse:
    """
    Run the World Builder pipeline.

    Takes confirmed entities from ingestion and generates the complete
    world bible with progressive field population.

    Requires: confirmed_entities.json from ingestion phase.
    Outputs: world_config.json in world_bible directory.
    """
    pipeline_id = f"world_builder_{request.project_path}"
    _init_status(pipeline_id, "world_builder", [
        "Load Confirmed Entities",
        "Generate World Context",
        "Generate Character Descriptions",
        "Generate Location Descriptions",
        "Generate Prop Descriptions",
        "Save World Config"
    ])

    background_tasks.add_task(
        _execute_world_builder_pipeline,
        pipeline_id,
        request
    )

    return PipelineResponse(
        success=True,
        message="World Builder pipeline started",
        pipeline_id=pipeline_id
    )


async def _execute_world_builder_pipeline(pipeline_id: str, request: PipelineRequest):
    """Execute the world builder pipeline."""
    from greenlight.pipelines.world_builder import WorldBuilderPipeline

    try:
        # Track field updates for real-time UI
        field_updates = []

        def field_callback(field_name: str, value: str, status: str):
            field_updates.append({
                "field": field_name,
                "value": value[:100] + "..." if len(value) > 100 else value,
                "status": status,
            })
            # Update message with latest field
            _add_log(pipeline_id, f"[OK] {field_name}")

        pipeline = WorldBuilderPipeline(
            project_path=Path(request.project_path),
            visual_style=request.visual_style,
            log_callback=lambda msg: _add_log(pipeline_id, msg),
            progress_callback=lambda p: _set_progress(pipeline_id, p),
            field_callback=field_callback,
        )

        # Stage progression
        _set_stage(pipeline_id, "Load Confirmed Entities", PipelineStage.RUNNING.value)

        result = await pipeline.run()

        if result["success"]:
            _complete(pipeline_id, success=True)
            _add_log(pipeline_id, f"World Bible complete! "
                    f"{result.get('characters', 0)} characters, "
                    f"{result.get('locations', 0)} locations, "
                    f"{result.get('props', 0)} props")
            # Store field updates in result
            pipeline_status[pipeline_id]["field_updates"] = field_updates

            # Auto-start reference image generation in background
            _add_log(pipeline_id, "Starting automatic reference image generation...")
            asyncio.create_task(_auto_generate_references(
                project_path=request.project_path,
                visual_style=request.visual_style,
                image_model=request.image_model or "z_image_turbo"
            ))
        else:
            _complete(pipeline_id, success=False, error=result.get("error", "Unknown error"))
            _add_log(pipeline_id, f"World Builder failed: {result.get('error')}")

    except Exception as e:
        _complete(pipeline_id, success=False, error=str(e))
        _add_log(pipeline_id, f"Error: {str(e)}")


async def _auto_generate_references(project_path: str, visual_style: str, image_model: str):
    """Auto-generate reference images after world builder completes."""
    from greenlight.pipelines.references import ReferencesPipeline

    try:
        # Create a separate pipeline ID for reference generation
        ref_pipeline_id = f"auto_references_{project_path}"
        _init_status(ref_pipeline_id, "auto_references", [
            "Character References",
            "Location References",
            "Prop References"
        ])

        def log_callback(msg: str):
            _add_log(ref_pipeline_id, msg)

        pipeline = ReferencesPipeline(
            project_path=Path(project_path),
            image_model=image_model,
            log_callback=log_callback,
        )

        # Set visual style
        pipeline.visual_style = visual_style

        _add_log(ref_pipeline_id, "Starting automatic reference generation...")

        # Run the references pipeline
        result = await pipeline.run()

        if result.get("success"):
            _complete(ref_pipeline_id, success=True)
            _add_log(ref_pipeline_id, f"References complete! "
                    f"{result.get('characters', 0)} characters, "
                    f"{result.get('locations', 0)} locations, "
                    f"{result.get('props', 0)} props")
        else:
            _complete(ref_pipeline_id, success=False, error=result.get("error", "Unknown error"))
            _add_log(ref_pipeline_id, f"References failed: {result.get('error')}")

    except Exception as e:
        _add_log(ref_pipeline_id, f"Auto-reference error: {str(e)}")


# =============================================================================
# STORYBOARD SCENE/FRAME ENDPOINTS
# =============================================================================

@router.post("/storyboard/scene/{scene_number}")
async def run_storyboard_scene(
    scene_number: int,
    request: PipelineRequest,
    background_tasks: BackgroundTasks
) -> PipelineResponse:
    """
    Generate storyboard for a single scene.

    Useful for chunked generation - generate one scene at a time.
    """
    # Override scene_filter to target specific scene
    request.scene_filter = [scene_number]

    pipeline_id = f"storyboard_scene_{scene_number}_{request.project_path}"
    _init_status(pipeline_id, f"storyboard_scene_{scene_number}", [
        "Load Visual Script",
        "Prepare References",
        "Generate Images",
        "Save Outputs"
    ])

    background_tasks.add_task(
        _execute_storyboard_pipeline,
        pipeline_id,
        request
    )

    return PipelineResponse(
        success=True,
        message=f"Storyboard generation started for scene {scene_number}",
        pipeline_id=pipeline_id
    )


@router.post("/storyboard/frame/{frame_id}")
async def regenerate_storyboard_frame(
    frame_id: str,
    project_path: str = "",
    image_model: str = "flux_2_pro",
    force: bool = True,
):
    """
    Regenerate a single storyboard frame.

    Useful for regenerating specific frames after prompt edits.
    Set force=True to regenerate even if image exists.
    """
    from greenlight.pipelines.storyboard import StoryboardPipeline

    if not project_path:
        return {"success": False, "error": "project_path is required"}

    try:
        pipeline = StoryboardPipeline(
            project_path=Path(project_path),
            image_model=image_model,
        )

        result = await pipeline.generate_single_frame(frame_id, force=force)

        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# PROMPT EDITING ENDPOINTS
# =============================================================================

@router.get("/prompts/{project_path:path}")
async def get_prompts(project_path: str):
    """
    Get frame prompts for editing.

    Returns prompts from prompts.json if it exists,
    otherwise generates from visual_script.json.
    """
    import json

    project_dir = Path(project_path)
    storyboard_dir = project_dir / "storyboard"

    # Try prompts.json first (user-edited version)
    prompts_path = storyboard_dir / "prompts.json"
    if prompts_path.exists():
        try:
            data = json.loads(prompts_path.read_text(encoding="utf-8"))
            return {
                "success": True,
                "source": "prompts.json",
                "prompts": data,
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to load prompts.json: {e}"}

    # Fall back to visual_script.json
    vs_path = storyboard_dir / "visual_script.json"
    if vs_path.exists():
        try:
            vs_data = json.loads(vs_path.read_text(encoding="utf-8"))
            frames = vs_data.get("frames", [])

            # Extract prompt data for editing
            prompts = [
                {
                    "frame_id": f.get("frame_id", ""),
                    "scene_number": f.get("scene_number", 1),
                    "prompt": f.get("prompt", ""),
                    "visual_description": f.get("visual_description", ""),
                    "camera_notation": f.get("camera_notation", ""),
                    "tags": f.get("tags", {}),
                    "location_direction": f.get("location_direction", "NORTH"),
                }
                for f in frames
            ]

            return {
                "success": True,
                "source": "visual_script.json",
                "prompts": prompts,
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to load visual_script.json: {e}"}

    return {
        "success": False,
        "error": "No visual script found. Run Director pipeline first.",
    }


@router.put("/prompts/{project_path:path}")
async def save_prompts(project_path: str, body: dict):
    """
    Save edited prompts.

    Saves to prompts.json which takes priority over visual_script.json
    for storyboard generation.
    """
    import json

    project_dir = Path(project_path)
    storyboard_dir = project_dir / "storyboard"
    storyboard_dir.mkdir(parents=True, exist_ok=True)

    prompts = body.get("prompts", [])
    if not prompts:
        return {"success": False, "error": "No prompts provided"}

    prompts_path = storyboard_dir / "prompts.json"

    try:
        prompts_path.write_text(
            json.dumps(prompts, indent=2),
            encoding="utf-8"
        )

        return {
            "success": True,
            "message": f"Saved {len(prompts)} prompts",
            "path": str(prompts_path),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.put("/prompts/{project_path:path}/frame/{frame_id}")
async def update_single_prompt(
    project_path: str,
    frame_id: str,
    body: dict,
):
    """
    Update a single frame's prompt.

    Updates the prompt in prompts.json (creates if doesn't exist).
    """
    import json

    project_dir = Path(project_path)
    storyboard_dir = project_dir / "storyboard"
    storyboard_dir.mkdir(parents=True, exist_ok=True)

    prompts_path = storyboard_dir / "prompts.json"

    # Load existing prompts or create from visual_script
    if prompts_path.exists():
        prompts = json.loads(prompts_path.read_text(encoding="utf-8"))
    else:
        vs_path = storyboard_dir / "visual_script.json"
        if vs_path.exists():
            vs_data = json.loads(vs_path.read_text(encoding="utf-8"))
            prompts = [
                {
                    "frame_id": f.get("frame_id", ""),
                    "scene_number": f.get("scene_number", 1),
                    "prompt": f.get("prompt", ""),
                    "tags": f.get("tags", {}),
                    "location_direction": f.get("location_direction", "NORTH"),
                }
                for f in vs_data.get("frames", [])
            ]
        else:
            return {"success": False, "error": "No prompts or visual_script found"}

    # Find and update the frame
    updated = False
    for prompt in prompts:
        if prompt.get("frame_id") == frame_id:
            if "prompt" in body:
                prompt["prompt"] = body["prompt"]
            if "tags" in body:
                prompt["tags"] = body["tags"]
            updated = True
            break

    if not updated:
        return {"success": False, "error": f"Frame {frame_id} not found"}

    # Save updated prompts
    prompts_path.write_text(json.dumps(prompts, indent=2), encoding="utf-8")

    return {
        "success": True,
        "message": f"Updated prompt for {frame_id}",
    }


# =============================================================================
# REFERENCE IMAGE MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/references/{project_path:path}")
async def list_references(project_path: str):
    """
    List all reference images in a project.

    Returns list of entity tags with their reference image status.
    """
    import json

    project_dir = Path(project_path)
    refs_dir = project_dir / "references"
    world_config_path = project_dir / "world_bible" / "world_config.json"

    if not world_config_path.exists():
        return {"success": False, "error": "No world_config.json found"}

    world_config = json.loads(world_config_path.read_text(encoding="utf-8"))

    references = []

    # Check characters
    for char in world_config.get("characters", []):
        tag = char.get("tag", "")
        ref_path = refs_dir / f"{tag}.png"
        references.append({
            "tag": tag,
            "name": char.get("name", ""),
            "type": "character",
            "has_reference": ref_path.exists(),
            "path": str(ref_path) if ref_path.exists() else None,
        })

    # Check locations
    for loc in world_config.get("locations", []):
        tag = loc.get("tag", "")
        ref_path = refs_dir / f"{tag}.png"
        references.append({
            "tag": tag,
            "name": loc.get("name", ""),
            "type": "location",
            "has_reference": ref_path.exists(),
            "path": str(ref_path) if ref_path.exists() else None,
        })

    # Check props
    for prop in world_config.get("props", []):
        tag = prop.get("tag", "")
        ref_path = refs_dir / f"{tag}.png"
        references.append({
            "tag": tag,
            "name": prop.get("name", ""),
            "type": "prop",
            "has_reference": ref_path.exists(),
            "path": str(ref_path) if ref_path.exists() else None,
        })

    return {
        "success": True,
        "references": references,
        "total": len(references),
        "generated": sum(1 for r in references if r["has_reference"]),
    }


@router.post("/references/{project_path:path}/regenerate/{tag}")
async def regenerate_reference(
    project_path: str,
    tag: str,
    image_model: str = "z_image_turbo",
):
    """
    Regenerate a single entity's reference image.

    Deletes existing reference and generates a new one.
    """
    import json
    from greenlight.pipelines.references import ReferencesPipeline

    project_dir = Path(project_path)
    world_config_path = project_dir / "world_bible" / "world_config.json"

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

    try:
        pipeline = ReferencesPipeline(
            project_path=project_dir,
            image_model=image_model,
        )

        result = await pipeline.generate_single(entity_type, tag)
        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/references/{project_path:path}/generate")
async def generate_single_reference(
    project_path: str,
    body: dict,
):
    """
    Generate a single entity's reference image.

    Body should contain:
    - tag: entity tag (e.g., CHAR_MARCUS)
    - model: image model to use (default: z_image_turbo)
    - overwrite: whether to overwrite existing (default: false)
    """
    import json
    from greenlight.pipelines.references import ReferencesPipeline

    project_dir = Path(project_path)
    world_config_path = project_dir / "world_bible" / "world_config.json"

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
    refs_dir = project_dir / "references"
    ref_path = refs_dir / f"{tag}.png"

    if ref_path.exists() and not overwrite:
        return {"success": True, "message": "Reference already exists", "path": str(ref_path)}

    try:
        pipeline = ReferencesPipeline(
            project_path=project_dir,
            image_model=model,
        )

        result = await pipeline.generate_single(entity_type, tag)
        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


@router.delete("/references/{project_path:path}/{tag}")
async def delete_reference(project_path: str, tag: str):
    """
    Delete a reference image.

    This allows regeneration on next pipeline run.
    """
    project_dir = Path(project_path)
    refs_dir = project_dir / "references"
    ref_path = refs_dir / f"{tag}.png"

    if not ref_path.exists():
        return {"success": False, "error": f"Reference for {tag} not found"}

    try:
        ref_path.unlink()
        return {
            "success": True,
            "message": f"Deleted reference for {tag}",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# STORYBOARD IMAGE GENERATION (NANO BANANA PRO)
# =============================================================================

class GenerateImageRequest(BaseModel):
    """Request to generate a single storyboard image."""
    project_path: str
    frame_id: str
    prompt: str
    model: str = "nano_banana_pro"  # nano_banana, nano_banana_pro, flux_2_pro
    aspect_ratio: str = "16:9"
    resolution: str = "2K"  # 1K, 2K, 4K (for Nano Banana Pro)
    reference_tags: list[str] = []  # Entity tags to include as references
    style_suffix: str = ""  # Additional style instructions


class EditImageRequest(BaseModel):
    """Request to edit/correct an existing storyboard image."""
    project_path: str
    frame_id: str
    edit_instruction: str  # What to change (semantic masking)
    model: str = "nano_banana_pro"
    additional_references: list[str] = []  # Extra reference images for the edit


@router.post("/generate-image")
async def generate_storyboard_image(request: GenerateImageRequest):
    """
    Generate a single storyboard image using Nano Banana Pro.

    Uses Gemini's native image generation for high-quality storyboard frames.
    Supports up to 14 reference images for character/location consistency.

    Features:
    - High-resolution output (1K, 2K, 4K)
    - Reference image injection for consistency
    - Style suffix for visual customization
    """
    import json
    from greenlight.core.image_gen import ImageGenerator, ImageRequest, ImageModel

    project_dir = Path(request.project_path)

    if not project_dir.exists():
        return {"success": False, "error": "Project not found"}

    # Gather reference images based on tags
    refs_dir = project_dir / "references"
    reference_images = []

    for tag in request.reference_tags:
        ref_path = refs_dir / f"{tag}.png"
        if ref_path.exists():
            reference_images.append(ref_path)

    # Map model name to enum
    model_map = {
        "nano_banana": ImageModel.NANO_BANANA,
        "nano_banana_pro": ImageModel.NANO_BANANA_PRO,
        "flux_2_pro": ImageModel.FLUX_2_PRO,
        "seedream": ImageModel.SEEDREAM,
    }
    model = model_map.get(request.model, ImageModel.NANO_BANANA_PRO)

    # Prepare output path
    output_dir = project_dir / "storyboard_output" / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{request.frame_id}.png"

    try:
        generator = ImageGenerator(project_path=project_dir)

        img_request = ImageRequest(
            prompt=request.prompt,
            model=model,
            aspect_ratio=request.aspect_ratio,
            reference_images=reference_images,
            output_path=output_path,
            tag=request.frame_id,
            prefix_type="generate",
            add_clean_suffix=True,
            style_suffix=request.style_suffix,
            resolution=request.resolution,
        )

        result = await generator.generate(img_request)

        if result.success:
            return {
                "success": True,
                "frame_id": request.frame_id,
                "image_path": str(result.image_path),
                "model_used": result.model_used,
                "generation_time_ms": result.generation_time_ms,
                "references_used": len(reference_images),
            }
        else:
            return {
                "success": False,
                "error": result.error,
                "frame_id": request.frame_id,
            }

    except Exception as e:
        return {"success": False, "error": str(e), "frame_id": request.frame_id}


@router.post("/edit-image")
async def edit_storyboard_image(request: EditImageRequest):
    """
    Edit/correct an existing storyboard image using Nano Banana Pro.

    Uses Gemini's semantic masking to edit specific parts of an image
    while preserving the rest. Ideal for:
    - Fixing character appearance issues
    - Adjusting lighting/mood
    - Adding/removing elements
    - Style corrections
    - Color grading changes

    The model understands natural language instructions like:
    - "Change the sky to sunset colors"
    - "Make the character's hair darker"
    - "Remove the car in the background"
    - "Add a sword to the character's hand"
    """
    import json
    from greenlight.core.image_gen import ImageGenerator, ImageRequest, ImageModel

    project_dir = Path(request.project_path)

    if not project_dir.exists():
        return {"success": False, "error": "Project not found"}

    # Find the source image
    output_dir = project_dir / "storyboard_output" / "generated"
    source_path = output_dir / f"{request.frame_id}.png"

    if not source_path.exists():
        return {
            "success": False,
            "error": f"Source image not found: {request.frame_id}",
            "hint": "Generate the image first using /generate-image"
        }

    # Gather additional reference images
    refs_dir = project_dir / "references"
    reference_images = []

    for tag in request.additional_references:
        ref_path = refs_dir / f"{tag}.png"
        if ref_path.exists():
            reference_images.append(ref_path)

    # Create backup of original
    backup_dir = output_dir / "backups"
    backup_dir.mkdir(exist_ok=True)
    import shutil
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{request.frame_id}_{timestamp}.png"
    shutil.copy2(source_path, backup_path)

    try:
        generator = ImageGenerator(project_path=project_dir)

        img_request = ImageRequest(
            prompt=request.edit_instruction,
            model=ImageModel.NANO_BANANA_PRO,  # Always use Pro for edits
            source_image=source_path,
            edit_instruction=request.edit_instruction,
            output_path=source_path,  # Overwrite the original
            reference_images=reference_images,
            prefix_type="edit",
        )

        result = await generator.edit_image(img_request)

        if result.success:
            return {
                "success": True,
                "frame_id": request.frame_id,
                "image_path": str(result.image_path),
                "backup_path": str(backup_path),
                "model_used": result.model_used,
                "generation_time_ms": result.generation_time_ms,
                "edit_instruction": request.edit_instruction,
            }
        else:
            return {
                "success": False,
                "error": result.error,
                "frame_id": request.frame_id,
                "backup_path": str(backup_path),  # Still have backup
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "frame_id": request.frame_id,
            "backup_path": str(backup_path),
        }


@router.post("/restore-image")
async def restore_image_from_backup(
    project_path: str,
    frame_id: str,
    backup_filename: Optional[str] = None,
):
    """
    Restore an image from its backup.

    If backup_filename is not provided, restores the most recent backup.
    """
    import shutil

    project_dir = Path(project_path)
    output_dir = project_dir / "storyboard_output" / "generated"
    backup_dir = output_dir / "backups"

    if not backup_dir.exists():
        return {"success": False, "error": "No backups found"}

    # Find the backup file
    if backup_filename:
        backup_path = backup_dir / backup_filename
    else:
        # Find most recent backup for this frame
        backups = sorted(
            backup_dir.glob(f"{frame_id}_*.png"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        if not backups:
            return {"success": False, "error": f"No backups found for {frame_id}"}
        backup_path = backups[0]

    if not backup_path.exists():
        return {"success": False, "error": f"Backup not found: {backup_path.name}"}

    try:
        target_path = output_dir / f"{frame_id}.png"
        shutil.copy2(backup_path, target_path)

        return {
            "success": True,
            "message": f"Restored from {backup_path.name}",
            "image_path": str(target_path),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/image-backups/{project_path:path}/{frame_id}")
async def list_image_backups(project_path: str, frame_id: str):
    """List all backups for a specific frame."""
    project_dir = Path(project_path)
    backup_dir = project_dir / "storyboard_output" / "generated" / "backups"

    if not backup_dir.exists():
        return {"success": True, "backups": []}

    backups = []
    for backup_path in sorted(
        backup_dir.glob(f"{frame_id}_*.png"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    ):
        backups.append({
            "filename": backup_path.name,
            "path": str(backup_path),
            "timestamp": backup_path.stat().st_mtime,
        })

    return {
        "success": True,
        "frame_id": frame_id,
        "backups": backups,
        "total": len(backups),
    }


# =============================================================================
# PIPELINE VALIDATION ENDPOINT
# =============================================================================

@router.get("/validate/{project_path:path}")
async def validate_pipeline_readiness(project_path: str):
    """
    Validate what pipelines can be run based on current project state.

    Returns which pipelines are ready and which have missing prerequisites.
    """
    import json

    project_dir = Path(project_path)

    status = {
        "project_exists": project_dir.exists(),
        "pipelines": {},
    }

    if not project_dir.exists():
        return status

    # Check each pipeline's prerequisites
    pipelines = {
        "writer": {
            "requires": ["world_bible/pitch.md"],
            "produces": ["world_bible/world_config.json", "story_outline.json"],
        },
        "ingestion": {
            "requires": ["uploads/"],
            "produces": ["ingestion/chunks.json", "ingestion/extracted_entities.json"],
        },
        "world_builder": {
            "requires": ["ingestion/confirmed_entities.json"],
            "produces": ["world_bible/world_config.json"],
        },
        "outline_generator": {
            "requires": ["world_bible/world_config.json"],
            "produces": ["outlines/outline_variants.json"],
        },
        "director": {
            "requires": ["outlines/confirmed_outline.json", "world_bible/world_config.json"],
            "produces": ["storyboard/visual_script.json"],
        },
        "references": {
            "requires": ["world_bible/world_config.json"],
            "produces": ["references/"],
        },
        "storyboard": {
            "requires": ["storyboard/visual_script.json", "references/"],
            "produces": ["storyboard_output/generated/"],
        },
    }

    for pipeline_name, config in pipelines.items():
        missing = []
        for req in config["requires"]:
            req_path = project_dir / req
            if req.endswith("/"):
                # Directory check
                if not req_path.exists() or not any(req_path.iterdir()) if req_path.exists() else True:
                    missing.append(req)
            else:
                # File check
                if not req_path.exists():
                    missing.append(req)

        outputs_exist = []
        for prod in config["produces"]:
            prod_path = project_dir / prod
            if prod.endswith("/"):
                if prod_path.exists() and any(prod_path.iterdir()):
                    outputs_exist.append(prod)
            else:
                if prod_path.exists():
                    outputs_exist.append(prod)

        status["pipelines"][pipeline_name] = {
            "ready": len(missing) == 0,
            "missing_requirements": missing,
            "outputs_exist": outputs_exist,
            "complete": len(outputs_exist) == len(config["produces"]),
        }

    return status
