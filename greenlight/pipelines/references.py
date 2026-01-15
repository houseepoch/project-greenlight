"""
References Pipeline - Generates single reference image per entity.

Simplified approach:
- One image per character (portrait)
- One image per location (establishing shot)
- One image per prop (product shot)

Reference images can be:
1. Auto-generated from entity description
2. Uploaded/replaced by user

TRACE: REFERENCES-001
"""

import json
import logging
from pathlib import Path
from typing import Callable, Optional

from greenlight.core.image_gen import ImageGenerator, ImageRequest, ImageModel
from greenlight.core.models import PipelineStage

logger = logging.getLogger(__name__)


# =============================================================================
# MEDIA TYPE STYLE REINFORCEMENT TEMPLATES
# These provide style-specific guidance without referencing artists
# =============================================================================

MEDIA_TYPE_STYLES = {
    "live_action": "Photorealistic cinematography, natural lighting, film grain texture, realistic proportions and anatomy, cinematic color grading, shallow depth of field, real-world physics",
    "anime": "Japanese animation style, expressive large eyes, dynamic line work, cel-shaded coloring, vibrant saturated colors, stylized proportions, dramatic poses, manga-inspired aesthetics",
    "animation_2d": "Traditional hand-drawn animation aesthetic, clean line art, fluid motion implied, painterly backgrounds, character design with appealing shapes, warm color palette, storybook quality",
    "animation_3d": "Modern 3D CGI rendering, smooth subsurface scattering on skin, stylized but grounded character design, ambient occlusion, global illumination, cinematic camera angles",
    "cartoon": "Stylized cartoon aesthetic, exaggerated features and expressions, bold outlines, flat colors with simple shading, playful proportions, squash and stretch implied, comedic timing",
    "claymation": "Stop-motion clay animation texture, visible fingerprint marks, tactile surface quality, slightly imperfect shapes, warm practical lighting, miniature set aesthetic, handcrafted feel",
    "mixed": "Hybrid visual style blending multiple mediums, creative compositing, artistic interpretation of reality, unique aesthetic fusion",
}

DEFAULT_MEDIA_STYLE = MEDIA_TYPE_STYLES["live_action"]


def get_media_style_prompt(visual_style: str) -> str:
    """Get the reinforcing style prompt for a media type."""
    return MEDIA_TYPE_STYLES.get(visual_style, DEFAULT_MEDIA_STYLE)


# =============================================================================
# REFERENCE PROMPT TEMPLATES
# =============================================================================

CHARACTER_REF_PROMPT = """Character reference sheet of {name} showing three views: front view, 3/4 side view, and back view arranged horizontally.

{appearance}

Costume: {clothing}

Visual Style: {media_style_prompt}
{style_notes}

Clean grey to white gradient background, professional studio lighting, character turnaround sheet quality, consistent proportions across all three views, full body visible in each view, sharp focus, no text labels."""

LOCATION_REF_PROMPT = """Establishing shot of {name}.

{description}

Visual Style: {media_style_prompt}
{style_notes}

Cinematic wide shot, atmospheric lighting, architectural reference quality, depth and atmosphere."""

PROP_REF_PROMPT = """Product photography of {name}.

{description}

Visual Style: {media_style_prompt}
{style_notes}

Clean studio lighting, neutral background, detailed product shot, sharp focus."""


class ReferencesPipeline:
    """
    Pipeline for generating single reference image per entity.

    Simplified from multi-angle sheets to single reference images
    that can be auto-generated or user-uploaded.
    """

    def __init__(
        self,
        project_path: Path,
        image_model: str = "flux_2_pro",
        entity_filter: Optional[list[str]] = None,  # Generate only specific tags
        log_callback: Optional[Callable[[str], None]] = None,
        stage_callback: Optional[Callable[[str, str, Optional[str]], None]] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
    ):
        self.project_path = Path(project_path)
        self.image_model = self._parse_model(image_model)
        self.entity_filter = entity_filter  # If set, only generate these tags

        self._log = log_callback or (lambda x: logger.info(x))
        self._stage = stage_callback or (lambda *args: None)
        self._progress = progress_callback or (lambda x: None)

        self.generator = ImageGenerator(project_path=project_path)

    def _parse_model(self, model: str) -> ImageModel:
        """Parse model string to enum."""
        model_map = {
            "seedream": ImageModel.SEEDREAM,
            "flux_2_pro": ImageModel.FLUX_2_PRO,
            "p_image_edit": ImageModel.P_IMAGE_EDIT,
            "nano_banana": ImageModel.NANO_BANANA,
            "nano_banana_pro": ImageModel.NANO_BANANA_PRO,
        }
        return model_map.get(model.lower(), ImageModel.FLUX_2_PRO)

    async def run(self) -> dict:
        """Execute the references pipeline."""
        try:
            # Stage 1: Load World Config
            self._stage("Load World Config", PipelineStage.RUNNING.value)
            self._progress(0.05)

            world_config_path = self.project_path / "world_bible" / "world_config.json"
            if not world_config_path.exists():
                return {"success": False, "error": "No world_config.json found. Run World Builder first."}

            world_config = json.loads(world_config_path.read_text(encoding="utf-8"))
            self._log("Loaded world config")

            characters = world_config.get("characters", [])
            locations = world_config.get("locations", [])
            props = world_config.get("props", [])

            # Filter if specific tags requested
            if self.entity_filter:
                characters = [c for c in characters if c.get("tag") in self.entity_filter]
                locations = [l for l in locations if l.get("tag") in self.entity_filter]
                props = [p for p in props if p.get("tag") in self.entity_filter]

            total_entities = len(characters) + len(locations) + len(props)
            if total_entities == 0:
                self._log("No entities to generate references for")
                return {"success": True, "generated": 0}

            self._log(f"Generating references: {len(characters)} characters, {len(locations)} locations, {len(props)} props")
            self._stage("Load World Config", PipelineStage.COMPLETE.value)

            # Create references directory
            refs_dir = self.project_path / "references"
            refs_dir.mkdir(parents=True, exist_ok=True)

            visual_style = world_config.get("visual_style", "live_action")
            style_notes = world_config.get("style_notes", "")
            media_style_prompt = get_media_style_prompt(visual_style)

            generated = 0
            skipped = 0
            failed = 0
            processed = 0

            # Stage 2: Generate Character References
            if characters:
                self._stage("Character References", PipelineStage.RUNNING.value)

                for char in characters:
                    tag = char.get("tag", "")
                    name = char.get("name", tag)

                    # Single reference image per character
                    ref_path = refs_dir / f"{tag}.png"

                    # Skip if exists (user may have uploaded custom)
                    if ref_path.exists():
                        self._log(f"  {name} - exists, skipping")
                        skipped += 1
                        processed += 1
                        continue

                    self._log(f"  Generating {name}...")

                    prompt = CHARACTER_REF_PROMPT.format(
                        name=name,
                        appearance=char.get("appearance", char.get("description", "")),
                        clothing=char.get("clothing", "period-appropriate attire"),
                        media_style_prompt=media_style_prompt,
                        style_notes=style_notes,
                    )

                    result = await self.generator.generate(ImageRequest(
                        prompt=prompt,
                        model=self.image_model,
                        output_path=ref_path,
                        aspect_ratio="1:1",
                        prefix_type="generate",
                    ))

                    if result.success:
                        generated += 1
                        self._log(f"  {name} - saved")
                    else:
                        failed += 1
                        self._log(f"  {name} - failed: {result.error}")

                    processed += 1
                    self._progress(0.1 + (processed / total_entities) * 0.85)

                self._stage("Character References", PipelineStage.COMPLETE.value)

            # Stage 3: Generate Location References
            if locations:
                self._stage("Location References", PipelineStage.RUNNING.value)

                for loc in locations:
                    tag = loc.get("tag", "")
                    name = loc.get("name", tag)

                    # Single reference image per location
                    ref_path = refs_dir / f"{tag}.png"

                    if ref_path.exists():
                        self._log(f"  {name} - exists, skipping")
                        skipped += 1
                        processed += 1
                        continue

                    self._log(f"  Generating {name}...")

                    prompt = LOCATION_REF_PROMPT.format(
                        name=name,
                        description=loc.get("description", ""),
                        media_style_prompt=media_style_prompt,
                        style_notes=style_notes,
                    )

                    result = await self.generator.generate(ImageRequest(
                        prompt=prompt,
                        model=self.image_model,
                        output_path=ref_path,
                        aspect_ratio="16:9",
                        prefix_type="generate",
                    ))

                    if result.success:
                        generated += 1
                        self._log(f"  {name} - saved")
                    else:
                        failed += 1
                        self._log(f"  {name} - failed: {result.error}")

                    processed += 1
                    self._progress(0.1 + (processed / total_entities) * 0.85)

                self._stage("Location References", PipelineStage.COMPLETE.value)

            # Stage 4: Generate Prop References
            if props:
                self._stage("Prop References", PipelineStage.RUNNING.value)

                for prop in props:
                    tag = prop.get("tag", "")
                    name = prop.get("name", tag)

                    # Single reference image per prop
                    ref_path = refs_dir / f"{tag}.png"

                    if ref_path.exists():
                        self._log(f"  {name} - exists, skipping")
                        skipped += 1
                        processed += 1
                        continue

                    self._log(f"  Generating {name}...")

                    prompt = PROP_REF_PROMPT.format(
                        name=name,
                        description=prop.get("description", ""),
                        media_style_prompt=media_style_prompt,
                        style_notes=style_notes,
                    )

                    result = await self.generator.generate(ImageRequest(
                        prompt=prompt,
                        model=self.image_model,
                        output_path=ref_path,
                        aspect_ratio="1:1",
                        prefix_type="generate",
                    ))

                    if result.success:
                        generated += 1
                        self._log(f"  {name} - saved")
                    else:
                        failed += 1
                        self._log(f"  {name} - failed: {result.error}")

                    processed += 1
                    self._progress(0.1 + (processed / total_entities) * 0.85)

                self._stage("Prop References", PipelineStage.COMPLETE.value)

            self._progress(1.0)

            return {
                "success": True,
                "generated": generated,
                "skipped": skipped,
                "failed": failed,
                "total_entities": total_entities,
            }

        except Exception as e:
            logger.exception(f"References pipeline error: {e}")
            return {"success": False, "error": str(e)}

    async def generate_single(self, entity_type: str, tag: str) -> dict:
        """
        Generate reference for a single entity.

        Useful for regenerating one entity's reference after editing.
        """
        world_config_path = self.project_path / "world_bible" / "world_config.json"
        if not world_config_path.exists():
            return {"success": False, "error": "No world_config.json found."}

        world_config = json.loads(world_config_path.read_text(encoding="utf-8"))
        visual_style = world_config.get("visual_style", "live_action")
        style_notes = world_config.get("style_notes", "")
        media_style_prompt = get_media_style_prompt(visual_style)

        refs_dir = self.project_path / "references"
        refs_dir.mkdir(parents=True, exist_ok=True)

        # Find entity
        entity = None
        entities = world_config.get(f"{entity_type}s", [])  # characters, locations, props
        for e in entities:
            if e.get("tag") == tag:
                entity = e
                break

        if not entity:
            return {"success": False, "error": f"Entity {tag} not found."}

        name = entity.get("name", tag)
        ref_path = refs_dir / f"{tag}.png"

        # Delete existing if present (force regenerate)
        if ref_path.exists():
            ref_path.unlink()

        # Build prompt based on type
        if entity_type == "character":
            prompt = CHARACTER_REF_PROMPT.format(
                name=name,
                appearance=entity.get("appearance", entity.get("description", "")),
                clothing=entity.get("clothing", "period-appropriate attire"),
                media_style_prompt=media_style_prompt,
                style_notes=style_notes,
            )
            aspect = "1:1"
        elif entity_type == "location":
            prompt = LOCATION_REF_PROMPT.format(
                name=name,
                description=entity.get("description", ""),
                media_style_prompt=media_style_prompt,
                style_notes=style_notes,
            )
            aspect = "16:9"
        else:  # prop
            prompt = PROP_REF_PROMPT.format(
                name=name,
                description=entity.get("description", ""),
                media_style_prompt=media_style_prompt,
                style_notes=style_notes,
            )
            aspect = "1:1"

        result = await self.generator.generate(ImageRequest(
            prompt=prompt,
            model=self.image_model,
            output_path=ref_path,
            aspect_ratio=aspect,
            prefix_type="generate",
        ))

        if result.success:
            return {"success": True, "path": str(ref_path)}
        else:
            return {"success": False, "error": result.error}


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def generate_references(project_path: Path, entity_filter: list[str] = None) -> dict:
    """Quick helper to run references pipeline."""
    pipeline = ReferencesPipeline(project_path, entity_filter=entity_filter)
    return await pipeline.run()
