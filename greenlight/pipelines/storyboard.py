"""
Storyboard Pipeline - Generates storyboard images from visual script.

Reference Image Order (per frame):
1. Location reference (establishing context)
2. Character references (in order of appearance in tags)
3. Prop references (if significant)
4. Prior frame (for scene continuity, same scene only)

Supports:
- Full generation (all scenes)
- Scene-by-scene generation (chunked)
- Single frame regeneration

TRACE: STORYBOARD-001
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from greenlight.core.image_gen import ImageGenerator, ImageRequest, ImageModel, get_media_style_prompt
from greenlight.core.models import PipelineStage

logger = logging.getLogger(__name__)


class StoryboardPipeline:
    """
    Pipeline for generating storyboard images.

    Reference images are composed in order:
    1. Location (establishing shot)
    2. Characters (in tag order)
    3. Props
    4. Prior frame (continuity)
    """

    def __init__(
        self,
        project_path: Path,
        image_model: str = "flux_2_pro",
        max_frames: Optional[int] = None,
        scene_filter: Optional[list[int]] = None,  # Generate only specific scenes
        log_callback: Optional[Callable[[str], None]] = None,
        stage_callback: Optional[Callable[[str, str, Optional[str]], None]] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
        item_callback: Optional[Callable[[int, int, Optional[str]], None]] = None,
    ):
        self.project_path = Path(project_path)
        self.image_model = self._parse_model(image_model)
        self.max_frames = max_frames
        self.scene_filter = scene_filter  # e.g., [1, 2] to generate only scenes 1 and 2

        self._log = log_callback or (lambda x: logger.info(x))
        self._stage = stage_callback or (lambda *args: None)
        self._progress = progress_callback or (lambda x: None)
        self._item = item_callback or (lambda *args: None)

        self.generator = ImageGenerator(project_path=project_path)

    def _parse_model(self, model: str) -> ImageModel:
        """Parse model string to enum."""
        model_map = {
            "seedream": ImageModel.SEEDREAM,
            "flux_2_pro": ImageModel.FLUX_2_PRO,
            "p_image_edit": ImageModel.P_IMAGE_EDIT,
            "nano_banana": ImageModel.NANO_BANANA,
            "nano_banana_pro": ImageModel.NANO_BANANA_PRO,
            "z_image_turbo": ImageModel.Z_IMAGE_TURBO,
        }
        return model_map.get(model.lower(), ImageModel.FLUX_2_PRO)

    async def run(self, check_cancelled: Callable[[], bool] = None) -> dict:
        """Execute the storyboard pipeline."""
        try:
            # Stage 1: Load Visual Script
            self._stage("Load Visual Script", PipelineStage.RUNNING.value)
            self._progress(0.02)

            frames = self._load_frames()
            if not frames:
                return {"success": False, "error": "No visual script found. Run Director pipeline first."}

            self._log(f"Loaded {len(frames)} frames")

            # Filter by scene if requested
            if self.scene_filter:
                frames = [f for f in frames if f.get("scene_number") in self.scene_filter]
                self._log(f"Filtered to scenes {self.scene_filter}: {len(frames)} frames")

            # Apply frame limit
            if self.max_frames and len(frames) > self.max_frames:
                frames = frames[:self.max_frames]
                self._log(f"Limited to {self.max_frames} frames")

            total_frames = len(frames)
            if total_frames == 0:
                return {"success": True, "completed": 0, "message": "No frames to generate"}

            self._stage("Load Visual Script", PipelineStage.COMPLETE.value)

            # Load world config for style
            world_config = self._load_world_config()
            style_suffix = self._build_style_suffix(world_config)

            # Stage 2: Prepare directories
            self._stage("Prepare References", PipelineStage.RUNNING.value)
            refs_dir = self.project_path / "references"

            # Create output directory
            output_dir = self.project_path / "storyboard_output" / "generated"
            output_dir.mkdir(parents=True, exist_ok=True)

            # Prompts log
            prompts_log = []
            prompts_log_path = self.project_path / "storyboard_output" / "prompts_log.json"

            self._stage("Prepare References", PipelineStage.COMPLETE.value)

            # Stage 3: Generate Images
            self._stage("Generate Images", PipelineStage.RUNNING.value)
            self._progress(0.1)

            completed = 0
            failed = 0
            skipped = 0
            prior_frame_path: Optional[Path] = None
            current_scene: Optional[int] = None

            for i, frame in enumerate(frames):
                # Check for cancellation
                if check_cancelled and check_cancelled():
                    self._log(f"Cancelled after {completed} frames")
                    return {
                        "success": True,
                        "cancelled": True,
                        "completed": completed,
                        "failed": failed,
                        "total": total_frames,
                    }

                frame_id = frame.get("frame_id", f"frame_{i+1}")
                prompt = frame.get("prompt", "")
                scene_num = frame.get("scene_number", 1)
                tags = frame.get("tags", {})

                # Reset prior frame on scene change
                if scene_num != current_scene:
                    prior_frame_path = None
                    current_scene = scene_num
                    self._log(f"Scene {scene_num}")

                if not prompt:
                    self._log(f"  {frame_id} - skipped (no prompt)")
                    skipped += 1
                    continue

                # Check if already exists
                clean_frame_id = frame_id.replace("[", "").replace("]", "")
                output_path = output_dir / f"{clean_frame_id}.png"

                if output_path.exists():
                    self._log(f"  {frame_id} - exists, skipping")
                    prior_frame_path = output_path  # Use as prior for next frame
                    skipped += 1
                    continue

                # Update item progress
                self._item(i, total_frames, f"Generating {frame_id}")

                # Collect reference images IN ORDER:
                # 1. Location first (establishing)
                # 2. Characters (in tag order)
                # 3. Props
                # 4. Prior frame (continuity)
                reference_images = self._collect_references(
                    tags=tags,
                    refs_dir=refs_dir,
                    prior_frame=prior_frame_path,
                )

                # Build full prompt
                full_prompt = f"{prompt} {style_suffix}"

                ref_count = len(reference_images)
                self._log(f"  {frame_id} - {ref_count} refs")

                # Generate image
                result = await self.generator.generate(ImageRequest(
                    prompt=full_prompt,
                    model=self.image_model,
                    output_path=output_path,
                    reference_images=reference_images[:8],  # Limit to 8
                    aspect_ratio="16:9",
                    prefix_type="generate",
                ))

                # Log the generation
                prompts_log.append({
                    "frame_id": clean_frame_id,
                    "scene_number": scene_num,
                    "prompt": full_prompt,
                    "reference_images": [str(p) for p in reference_images],
                    "output_path": str(output_path),
                    "success": result.success,
                    "error": result.error,
                    "timestamp": datetime.now().isoformat(),
                })

                if result.success:
                    completed += 1
                    prior_frame_path = output_path
                    self._log(f"  {frame_id} - saved")
                else:
                    failed += 1
                    self._log(f"  {frame_id} - failed: {result.error}")

                # Update progress
                self._progress(0.1 + (i + 1) / total_frames * 0.85)

                # Save prompts log incrementally
                prompts_log_path.write_text(json.dumps(prompts_log, indent=2), encoding="utf-8")

            self._stage("Generate Images", PipelineStage.COMPLETE.value)

            # Stage 4: Save Outputs
            self._stage("Save Outputs", PipelineStage.RUNNING.value)
            self._progress(0.98)

            prompts_log_path.write_text(json.dumps(prompts_log, indent=2), encoding="utf-8")
            self._log(f"Saved prompts_log.json")

            self._stage("Save Outputs", PipelineStage.COMPLETE.value)
            self._progress(1.0)

            return {
                "success": True,
                "completed": completed,
                "failed": failed,
                "skipped": skipped,
                "total": total_frames,
            }

        except Exception as e:
            logger.exception(f"Storyboard pipeline error: {e}")
            return {"success": False, "error": str(e)}

    def _collect_references(
        self,
        tags: dict,
        refs_dir: Path,
        prior_frame: Optional[Path] = None,
    ) -> list[Path]:
        """
        Collect reference images in proper order:
        1. Location (establishing shot first)
        2. Characters (in tag order)
        3. Props
        4. Prior frame (continuity)
        """
        references = []

        # 1. LOCATION FIRST (establishing context)
        for loc_tag in tags.get("locations", []):
            ref = refs_dir / f"{loc_tag}.png"
            if ref.exists():
                references.append(ref)
                break  # Only use first/primary location

        # 2. CHARACTERS (in order of appearance)
        for char_tag in tags.get("characters", []):
            ref = refs_dir / f"{char_tag}.png"
            if ref.exists():
                references.append(ref)

        # 3. PROPS (if significant)
        for prop_tag in tags.get("props", []):
            # Normalize prop tag (handle both PROP_X and lowercase)
            ref = refs_dir / f"{prop_tag}.png"
            if ref.exists():
                references.append(ref)
            else:
                # Try uppercase version
                ref_upper = refs_dir / f"{prop_tag.upper()}.png"
                if ref_upper.exists():
                    references.append(ref_upper)

        # 4. PRIOR FRAME (for scene continuity)
        if prior_frame and prior_frame.exists():
            references.append(prior_frame)

        return references

    def _load_frames(self) -> list[dict]:
        """Load frames from prompts.json or visual_script.json."""
        # Try prompts.json first (user-edited)
        prompts_path = self.project_path / "storyboard" / "prompts.json"
        if prompts_path.exists():
            prompts_data = json.loads(prompts_path.read_text(encoding="utf-8"))
            return [
                {
                    "frame_id": p.get("frame_id", ""),
                    "scene_number": p.get("scene_number", 1),
                    "prompt": p.get("prompt", ""),
                    "tags": p.get("tags", {}),
                    "location_direction": p.get("location_direction", "NORTH"),
                }
                for p in prompts_data
            ]

        # Fall back to visual_script.json
        vs_path = self.project_path / "storyboard" / "visual_script.json"
        if vs_path.exists():
            vs_data = json.loads(vs_path.read_text(encoding="utf-8"))
            frames = []
            for frame in vs_data.get("frames", []):
                frames.append({
                    "frame_id": frame.get("frame_id", ""),
                    "scene_number": frame.get("scene_number", 1),
                    "prompt": frame.get("prompt", ""),
                    "tags": frame.get("tags", {}),
                    "location_direction": frame.get("location_direction", "NORTH"),
                })
            return frames

        return []

    def _load_world_config(self) -> dict:
        """Load world config for style information."""
        wc_path = self.project_path / "world_bible" / "world_config.json"
        if wc_path.exists():
            return json.loads(wc_path.read_text(encoding="utf-8"))
        return {}

    def _build_style_suffix(self, world_config: dict) -> str:
        """Build style suffix from world config using media type templates."""
        parts = []

        visual_style = world_config.get("visual_style", "live_action")
        # Use the centralized media style prompt
        media_style = get_media_style_prompt(visual_style)
        parts.append(media_style)

        style_notes = world_config.get("style_notes", "")
        if style_notes:
            parts.append(style_notes)

        return " ".join(parts)

    async def generate_single_frame(self, frame_id: str, force: bool = False) -> dict:
        """
        Generate a single frame by ID.

        Useful for regenerating specific frames after prompt edits.
        Archives the existing frame before regeneration when force=True.
        """
        frames = self._load_frames()
        frame = next((f for f in frames if f.get("frame_id") == frame_id), None)

        if not frame:
            return {"success": False, "error": f"Frame {frame_id} not found"}

        refs_dir = self.project_path / "references"
        output_dir = self.project_path / "storyboard_output" / "generated"
        output_dir.mkdir(parents=True, exist_ok=True)

        clean_frame_id = frame_id.replace("[", "").replace("]", "")
        output_path = output_dir / f"{clean_frame_id}.png"

        # Check if exists and force not set
        if output_path.exists() and not force:
            return {"success": True, "skipped": True, "path": str(output_path)}

        # Archive existing frame before regeneration
        if output_path.exists() and force:
            try:
                from greenlight.core.checkpoints import CheckpointService
                checkpoint_service = CheckpointService(self.project_path)
                checkpoint_service.archive_frame(
                    frame_id=clean_frame_id,
                    healing_notes="Manual regeneration",
                    prompt=frame.get("prompt", ""),
                )
                self._log(f"Archived frame {clean_frame_id} before regeneration")
            except Exception as e:
                self._log(f"Warning: Failed to archive frame: {e}")
            output_path.unlink()

        # Get world config for style
        world_config = self._load_world_config()
        style_suffix = self._build_style_suffix(world_config)

        # Find prior frame in same scene for continuity
        scene_num = frame.get("scene_number", 1)
        scene_frames = [f for f in frames if f.get("scene_number") == scene_num]
        frame_idx = next((i for i, f in enumerate(scene_frames) if f.get("frame_id") == frame_id), 0)

        prior_frame = None
        if frame_idx > 0:
            prior_id = scene_frames[frame_idx - 1].get("frame_id", "").replace("[", "").replace("]", "")
            prior_path = output_dir / f"{prior_id}.png"
            if prior_path.exists():
                prior_frame = prior_path

        # Collect references
        references = self._collect_references(
            tags=frame.get("tags", {}),
            refs_dir=refs_dir,
            prior_frame=prior_frame,
        )

        # Generate
        prompt = frame.get("prompt", "")
        full_prompt = f"{prompt} {style_suffix}"

        result = await self.generator.generate(ImageRequest(
            prompt=full_prompt,
            model=self.image_model,
            output_path=output_path,
            reference_images=references[:8],
            aspect_ratio="16:9",
            prefix_type="generate",
        ))

        if result.success:
            return {"success": True, "path": str(output_path)}
        else:
            return {"success": False, "error": result.error}


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def generate_storyboard(
    project_path: Path,
    scene_filter: list[int] = None,
    max_frames: int = None,
) -> dict:
    """Quick helper to run storyboard pipeline."""
    pipeline = StoryboardPipeline(
        project_path,
        scene_filter=scene_filter,
        max_frames=max_frames,
    )
    return await pipeline.run()


async def generate_scene(project_path: Path, scene_number: int) -> dict:
    """Generate storyboard for a single scene."""
    return await generate_storyboard(project_path, scene_filter=[scene_number])


async def generate_frame(project_path: Path, frame_id: str, force: bool = False) -> dict:
    """Generate a single frame."""
    pipeline = StoryboardPipeline(project_path)
    return await pipeline.generate_single_frame(frame_id, force=force)
