"""
References Pipeline - Generates single reference image per entity.

Simplified approach:
- One image per character (portrait)
- One image per location (establishing shot)
- One image per prop (product shot)

Reference images can be:
1. Auto-generated from entity description
2. Uploaded/replaced by user

Labels are added to reference images with yellow text and black outline
to clearly identify entities in the generated references.

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
# REFERENCE IMAGE LABELING
# =============================================================================

def add_label_to_image(image_path: Path, label: str, position: str = "top") -> bool:
    """
    Add a yellow text label with black outline to a reference image.

    Args:
        image_path: Path to the image file
        label: Text to display (e.g., entity name or tag)
        position: "top" or "bottom"

    Returns:
        True if successful, False otherwise
    """
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)

        # Calculate font size based on image width (roughly 5% of width)
        img_width, img_height = img.size
        font_size = max(24, int(img_width * 0.06))

        # Try to use a system font, fall back to default
        font = None
        try:
            # Try common fonts on different systems
            font_names = [
                "arial.ttf", "Arial.ttf", "Arial Bold.ttf",
                "DejaVuSans-Bold.ttf", "DejaVuSans.ttf",
                "Helvetica.ttf", "Helvetica-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/arialbd.ttf",
            ]
            for font_name in font_names:
                try:
                    font = ImageFont.truetype(font_name, font_size)
                    break
                except (OSError, IOError):
                    continue
        except Exception:
            pass

        if font is None:
            # Fall back to default font
            font = ImageFont.load_default()

        # Get text bounding box
        bbox = draw.textbbox((0, 0), label, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Calculate position (centered horizontally)
        x = (img_width - text_width) // 2
        if position == "top":
            y = 8
        else:
            y = img_height - text_height - 8

        # Draw black outline (multiple passes for thick outline)
        outline_color = "black"
        outline_width = max(3, font_size // 10)
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), label, font=font, fill=outline_color)

        # Draw yellow text on top
        draw.text((x, y), label, font=font, fill="yellow")

        # Save
        img.save(image_path)
        return True

    except Exception as e:
        logger.error(f"Failed to add label to {image_path}: {e}")
        return False


def get_display_name_from_tag(tag: str) -> str:
    """
    Convert entity tag to display name.
    E.g., "CHAR_MEI" -> "MEI", "LOC_FLORIST_SHOP" -> "FLORIST SHOP"
    """
    # Remove prefix (CHAR_, LOC_, PROP_)
    for prefix in ["CHAR_", "LOC_", "PROP_"]:
        if tag.startswith(prefix):
            name = tag[len(prefix):]
            # Replace underscores with spaces
            return name.replace("_", " ")
    return tag


def label_existing_references(refs_dir: Path, world_config: dict) -> int:
    """
    Add labels to all existing reference images that don't have labels yet.

    Returns number of images labeled.
    """
    labeled = 0

    # Process all entity types
    for entity_type in ["characters", "locations", "props"]:
        for entity in world_config.get(entity_type, []):
            tag = entity.get("tag", "")
            name = entity.get("name", tag)
            ref_path = refs_dir / f"{tag}.png"

            if ref_path.exists():
                display_name = name.upper() if name else get_display_name_from_tag(tag)
                if add_label_to_image(ref_path, display_name):
                    labeled += 1
                    logger.info(f"Labeled: {ref_path.name}")

    return labeled


# =============================================================================
# MEDIA TYPE STYLE REINFORCEMENT TEMPLATES
# These provide style-specific guidance without referencing artists
# =============================================================================

MEDIA_TYPE_STYLES = {
    "live_action": "photorealistic photograph, real human being, natural skin texture with pores and imperfections, realistic lighting, DSLR camera quality, 85mm portrait lens, real-world physics, NOT a painting, NOT 3D render, NOT CGI, NOT illustration, NOT anime, NOT digital art",
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
# REFERENCE PROMPT TEMPLATES - LIVE ACTION (Photorealistic)
# =============================================================================

CHARACTER_REF_PROMPT_LIVE_ACTION = """Photorealistic cinematic portrait photograph. Shot on 85mm lens f/2.8, professional studio with seamless grey backdrop, soft key light with fill. Real human being with natural skin texture showing pores and imperfections. NOT 3D render, NOT CGI, NOT illustration, NOT anime, NOT digital art.

Subject: {name}

EXACT APPEARANCE REQUIRED: {appearance}

COSTUME DETAILS: {clothing}

{style_notes}

Absolutely no text, no labels, no watermarks, no borders, no decorative elements."""

# =============================================================================
# REFERENCE PROMPT TEMPLATES - STYLIZED (Animation/Anime/etc)
# =============================================================================

CHARACTER_REF_PROMPT_STYLIZED = """Character design sheet of {name} showing three views: front view, 3/4 side view, and back view arranged horizontally.

Character appearance: {appearance}

Costume: {clothing}

Visual Style: {media_style_prompt}
{style_notes}

Clean gradient background, professional character design quality, consistent proportions across all three views, full body visible in each view, sharp details, no text labels."""

# =============================================================================
# LOCATION AND PROP TEMPLATES
# =============================================================================

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


def get_character_prompt_template(visual_style: str) -> str:
    """Get the appropriate character prompt template based on visual style."""
    if visual_style == "live_action":
        return CHARACTER_REF_PROMPT_LIVE_ACTION
    else:
        return CHARACTER_REF_PROMPT_STYLIZED


class ReferencesPipeline:
    """
    Pipeline for generating single reference image per entity.

    Simplified from multi-angle sheets to single reference images
    that can be auto-generated or user-uploaded.
    """

    def __init__(
        self,
        project_path: Path,
        image_model: str = "z_image_turbo",
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
            "z_image_turbo": ImageModel.Z_IMAGE_TURBO,
            "nano_banana": ImageModel.NANO_BANANA,
            "nano_banana_pro": ImageModel.NANO_BANANA_PRO,
        }
        return model_map.get(model.lower(), ImageModel.Z_IMAGE_TURBO)

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

                    # Use appropriate template based on visual style
                    char_template = get_character_prompt_template(visual_style)
                    appearance = char.get("appearance", char.get("description", ""))
                    clothing = char.get("clothing", "period-appropriate attire")

                    prompt = char_template.format(
                        name=name,
                        appearance=appearance,
                        clothing=clothing,
                        media_style_prompt=media_style_prompt,
                        style_notes=style_notes,
                    )

                    result = await self.generator.generate(ImageRequest(
                        prompt=prompt,
                        model=self.image_model,
                        output_path=ref_path,
                        aspect_ratio="1:1",
                        prefix_type="none",
                    ))

                    if result.success:
                        # Add label to the generated image
                        display_name = name.upper()
                        add_label_to_image(ref_path, display_name)
                        generated += 1
                        self._log(f"  {name} - saved with label")
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
                        prefix_type="none",
                    ))

                    if result.success:
                        # Add label to the generated image
                        display_name = get_display_name_from_tag(tag)
                        add_label_to_image(ref_path, display_name)
                        generated += 1
                        self._log(f"  {name} - saved with label")
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
                        prefix_type="none",
                    ))

                    if result.success:
                        # Add label to the generated image
                        display_name = get_display_name_from_tag(tag)
                        add_label_to_image(ref_path, display_name)
                        generated += 1
                        self._log(f"  {name} - saved with label")
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
            char_template = get_character_prompt_template(visual_style)
            appearance = entity.get("appearance", entity.get("description", ""))

            prompt = char_template.format(
                name=name,
                appearance=appearance,
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
            prefix_type="none",
        ))

        if result.success:
            # Add label to the generated image
            display_name = get_display_name_from_tag(tag)
            add_label_to_image(ref_path, display_name)
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
