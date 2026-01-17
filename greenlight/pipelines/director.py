"""
CineStage Director Pipeline - Batched visual script generation.

Transforms confirmed outline beats into cinematic frames using batched
LLM calls for consistent prompt quality throughout.

Key features:
- Batched processing (5 scenes per batch) for consistent 200-300 word prompts
- Single-pass staging per batch instead of one LLM call per beat
- Camera notation: [scene.frame.camera] e.g., [3.2.cB]
- Output format designed for card-based UI (text until generated, then image)

Flow:
1. Load confirmed_outline.json (beats from user-confirmed outline)
2. Load world_config.json (world context + enriched entities)
3. Split beats into batches of 5
4. For each batch: generate scene graph with frames
5. Merge batches and save outputs

TRACE: CINESTAGE-001
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Callable, Optional
from datetime import datetime

from greenlight.core.llm import LLMClient
from greenlight.core.models import PipelineStage
from greenlight.pipelines.prompts import CINESTAGE_SYSTEM_PROMPT, BATCH_USER_TEMPLATE

logger = logging.getLogger(__name__)


# =============================================================================
# CAMERA NOTATION REFERENCE
# =============================================================================

CAMERA_NOTATIONS = {
    "EWS": "Extreme Wide Shot - Establishes vast environment",
    "WS": "Wide Shot - Full body, environment context",
    "MS": "Medium Shot - Waist up, conversation framing",
    "MCU": "Medium Close-Up - Chest up, emotional clarity",
    "CU": "Close-Up - Face only, intimate emotion",
    "ECU": "Extreme Close-Up - Eyes/detail, intense focus",
    "OTS": "Over The Shoulder - Conversation, perspective",
    "INS": "Insert Shot - Detail/prop focus",
}


# =============================================================================
# WORLD CONTEXT BUILDER
# =============================================================================


def _build_visual_id(name: str, appearance: str, clothing: str) -> str:
    """Build a short-form visual ID string for character consistency.

    Uses pattern-based extraction to identify:
    - Build/body type
    - Age range
    - Primary garment (color + type)
    - Secondary garment (belt/sash)
    - Skin tone
    - Hair description
    - Distinctive features (scars, marks, etc.)

    Returns format: "Name: build age, garment + accessory, skin, hair, feature"
    """
    import re

    parts = [name]
    appearance_lower = appearance.lower()
    clothing_lower = clothing.lower()

    # --- BUILD/BODY TYPE (pattern-based) ---
    # Must be careful not to match "plump lips" as "plump" body type
    build_patterns = [
        r'\b(slender|slim|lithe|petite|thin)\s+(and\s+)?(graceful|build|frame|figure|form|body)?\b',
        r'\b(portly|stout|heavyset|rotund)\s+(build|frame|figure|form|body)?\b',
        r'\b(plump|chubby)\s+(build|frame|figure|form|body)\b',  # Require "build" to avoid "plump lips"
        r'\b(voluptuous|curvy|full[- ]?figured)\s*(build|frame|figure|form|body)?\b',
        r'\b(broad[- ]?shouldered|muscular|athletic|stocky)\s*(build|frame|figure|form|body)?\b',
        r'\b(tall|short)\s+(and\s+)?(broad|slender|thin|build|stature)?\b',
        r'\b(average height|medium height|imposing stature)\b',
    ]
    builds = []
    for pattern in build_patterns:
        match = re.search(pattern, appearance_lower)
        if match:
            # Extract just the key descriptor
            descriptor = match.group(1) if match.group(1) else match.group(0)
            descriptor = descriptor.replace('-', ' ').strip()
            if descriptor and descriptor not in builds:
                builds.append(descriptor)

    # --- AGE (pattern-based) ---
    age_match = re.search(r'\b(early|mid|late)[- ]?(\d+)s\b', appearance_lower)
    if age_match:
        builds.append(f"{age_match.group(1)}-{age_match.group(2)}s")
    else:
        # Try alternate patterns like "in her 20s" or "teenager"
        alt_age = re.search(r'\b(teenager|teen|young|elderly|middle[- ]?aged)\b', appearance_lower)
        if alt_age:
            builds.append(alt_age.group(1))

    if builds:
        parts.append(" ".join(builds[:3]))  # Max 3 build/age descriptors

    # --- PRIMARY GARMENT (color + fabric + type) ---
    # Generic pattern: [color] [fabric]? [garment]
    # Or: [garment] in [color]
    garment_types = r'(kimono|robe|dress|gown|suit|coat|jacket|shirt|blouse|tunic|changshan|surcoat|uniform|armor|cloak)'
    fabric_types = r'(silk|cotton|linen|wool|velvet|leather|satin|brocade)?'
    colors = r'(red|blue|green|yellow|orange|purple|pink|black|white|grey|gray|brown|gold|silver|crimson|scarlet|navy|teal|emerald|amber|ivory|cream|burgundy|maroon|indigo|violet|turquoise|coral|tan|beige|earthy green|soft earthy green|deep crimson|muted blue|dark blue|light blue|forest green|olive)'

    clothing_parts = []

    # Pattern 1: color [fabric] garment (e.g., "blue silk kimono")
    pattern1 = rf'\b({colors})\s+{fabric_types}\s*{garment_types}\b'
    match = re.search(pattern1, clothing_lower)
    if match:
        clothing_parts.append(match.group(0).strip())

    # Pattern 2: garment in color (e.g., "robe in soft earthy green")
    pattern2 = rf'\b{fabric_types}\s*{garment_types}\s+in\s+({colors})\b'
    match = re.search(pattern2, clothing_lower)
    if match:
        # Normalize to "color garment" format
        full_match = match.group(0)
        parts_split = full_match.split(' in ')
        if len(parts_split) == 2:
            garment = parts_split[0].strip()
            color = parts_split[1].strip()
            clothing_parts.append(f"{color} {garment}")

    # --- SECONDARY GARMENT (belt/sash/accessory) ---
    accessory_pattern = rf'\b({colors})\s+(obi|sash|belt|scarf|cape|cloak|vest|waistcoat)\b'
    match = re.search(accessory_pattern, clothing_lower)
    if match:
        clothing_parts.append(match.group(0).strip())

    # Also check for "military surcoat" or similar compound garments
    compound_pattern = rf'\b({colors})\s+(military\s+)?{garment_types}\b'
    match = re.search(compound_pattern, clothing_lower)
    if match and match.group(0) not in clothing_parts:
        clothing_parts.append(match.group(0).strip())

    if clothing_parts:
        # Deduplicate and limit
        unique_clothing = list(dict.fromkeys(clothing_parts))[:2]
        parts.append(" + ".join(unique_clothing))

    # --- SKIN TONE (pattern-based) ---
    # Must explicitly include "skin" to avoid false positives like "dark eyes"
    skin_patterns = [
        r'\b(porcelain|pale|fair|light|dark|tan|tanned|olive|brown|ebony|copper|bronze|golden|ivory|alabaster)[- ]?(fair[- ]?)?(skin|skinned|complexion)\b',
        r'\b(porcelain|ivory|alabaster|fair|pale)[- ]?fair\b',  # e.g., "porcelain-fair"
    ]
    for pattern in skin_patterns:
        match = re.search(pattern, appearance_lower)
        if match:
            skin_desc = match.group(0).strip()
            if 'skin' not in skin_desc:
                skin_desc += ' skin'
            parts.append(skin_desc)
            break

    # --- HAIR (color + style/length) ---
    hair_colors = r'(black|brown|blonde|red|auburn|grey|gray|white|silver|golden|dark|light|raven|chestnut)'
    hair_styles = r'(hair|topknot|bun|chignon|braid|braids|ponytail|pigtails|curls|waves|locks)'
    hair_lengths = r'(long|short|shoulder[- ]?length|waist[- ]?length|to waist|cropped|shaved)?'

    hair_match = re.search(rf'\b{hair_colors}\s+{hair_lengths}\s*{hair_styles}\b', appearance_lower)
    if hair_match:
        parts.append(hair_match.group(0).strip())
    else:
        # Try simpler pattern
        simple_hair = re.search(rf'\b{hair_colors}\s+{hair_styles}\b', appearance_lower)
        if simple_hair:
            parts.append(simple_hair.group(0).strip())

    # --- DISTINCTIVE FEATURES (scars, marks, etc.) ---
    # Be specific to avoid matching "piercing gaze" as just "piercing"
    feature_patterns = [
        r'\b(jawline scar|facial scar|scar on \w+|scarred \w+)\b',
        r'\b(beauty mark|birthmark|mole) on (cheek|face|chin|lip)\b',
        r'\b(beauty mark|birthmark|mole) on (his|her) (cheek|face|chin|lip)\b',
        r'\b(tattoo|freckles|glasses|spectacles|eyepatch)\b',
        r'\b(calloused hands|rough hands|scarred hands|gentle calloused hands)\b',
        r'\b(body piercing|ear piercing|nose piercing)\b',  # Avoid "piercing gaze"
    ]
    features = []
    for pattern in feature_patterns:
        match = re.search(pattern, appearance_lower)
        if match:
            feature_text = match.group(0).strip()
            # Clean up "on his/her" patterns
            feature_text = re.sub(r' on (his|her) ', ' on ', feature_text)
            features.append(feature_text)

    if features:
        parts.append(", ".join(features[:2]))  # Max 2 features

    # Build final string
    if len(parts) > 1:
        return f"{parts[0]}: {', '.join(parts[1:])}"
    return name


def build_entity_lookups(world_config: dict) -> dict:
    """Build lookup tables for mapping names to entity tags.

    Handles spelling variations by adding multiple lookup keys:
    - Full name (e.g., "Madame Chou")
    - Individual words (e.g., "madame", "chou")
    - Tag-derived name (e.g., "CHAR_MEI" -> "mei")
    """
    lookups = {
        "characters": {},  # name -> tag (e.g., "Mei" -> "CHAR_MEI")
        "locations": {},   # name -> tag (e.g., "Lu Xian" -> "LOC_LU_XIAN")
        "props": {},       # name -> tag
    }

    for char in world_config.get("characters", []):
        name = char.get("name", "").lower()
        tag = char.get("tag", "")
        if name and tag:
            # Add full name
            lookups["characters"][name] = tag
            # Add individual words for partial matching
            for word in name.split():
                if len(word) > 2:  # Skip short words like "a", "of"
                    lookups["characters"][word] = tag
            # Add tag-derived name (e.g., CHAR_MEI -> mei)
            tag_name = tag.replace("CHAR_", "").replace("_", " ").lower()
            lookups["characters"][tag_name] = tag

    for loc in world_config.get("locations", []):
        name = loc.get("name", "").lower()
        tag = loc.get("tag", "")
        if name and tag:
            lookups["locations"][name] = tag
            # Add tag-derived name
            tag_name = tag.replace("LOC_", "").replace("_", " ").lower()
            lookups["locations"][tag_name] = tag

    for prop in world_config.get("props", []):
        name = prop.get("name", "").lower()
        tag = prop.get("tag", "")
        if name and tag:
            lookups["props"][name] = tag
            # Add tag-derived name
            tag_name = tag.replace("PROP_", "").replace("_", " ").lower()
            lookups["props"][tag_name] = tag

    return lookups


def build_world_context(world_config: dict) -> str:
    """Build world context string for LLM prompts.

    Character descriptions are formatted prominently with clear sections
    to reinforce visual consistency in generated prompts.
    """
    world_context = world_config.get("world_context", {})
    characters = world_config.get("characters", [])
    locations = world_config.get("locations", [])

    lines = ["WORLD CONTEXT:"]

    # Time period and setting
    if world_context.get("time_period"):
        lines.append(f"Period: {world_context['time_period']}")
    if world_context.get("clothing_norms"):
        lines.append(f"Clothing: {world_context['clothing_norms']}")
    if world_context.get("architecture_style"):
        lines.append(f"Architecture: {world_context['architecture_style']}")
    if world_context.get("lighting_style"):
        lines.append(f"Lighting: {world_context['lighting_style']}")
    if world_context.get("color_palette"):
        lines.append(f"Color Palette: {world_context['color_palette']}")

    # Characters - formatted with clear visual anchors
    if characters:
        lines.append("\n" + "="*50)
        lines.append("CHARACTERS (USE EXACT DESCRIPTIONS - DO NOT DEVIATE)")
        lines.append("="*50)
        for char in characters:
            name = char.get("name", "Unknown")
            appearance = char.get("appearance", "")
            clothing = char.get("clothing", "")

            lines.append(f"\n[{name.upper()}]")
            if appearance:
                lines.append(f"  APPEARANCE: {appearance}")
            if clothing:
                lines.append(f"  CLOTHING: {clothing}")

    # Locations
    if locations:
        lines.append("\nLOCATIONS:")
        for loc in locations:
            name = loc.get("name", "Unknown")
            desc = loc.get("description", "")
            lines.append(f"- {name}: {desc}")

    return "\n".join(lines)


# =============================================================================
# CINESTAGE DIRECTOR PIPELINE
# =============================================================================

class DirectorPipeline:
    """
    CineStage Director Pipeline - Batched visual script generation.

    Processes story beats in batches of 5 for consistent prompt quality.
    Each beat becomes a scene with 2-4 frames for image generation.

    Output format supports card-based UI:
    - prompts.json with generated: false, image_url: null
    - Cards show text until image is generated, then can flip to show image
    """

    BATCH_SIZE = 1  # One scene per batch for maximum prompt quality (340-555 words)

    def __init__(
        self,
        project_path: Path,
        max_frames: Optional[int] = None,
        llm_model: str = "grok-4-1-fast",
        log_callback: Optional[Callable[[str], None]] = None,
        stage_callback: Optional[Callable[[str, str, Optional[str]], None]] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
    ):
        self.project_path = Path(project_path)
        self.max_frames = max_frames
        self.llm_model = llm_model

        self._log = log_callback or (lambda x: logger.info(x))
        self._stage = stage_callback or (lambda *args: None)
        self._progress = progress_callback or (lambda x: None)

        self.llm = LLMClient()

    async def run(self) -> dict:
        """Execute the CineStage director pipeline."""
        try:
            # Stage 1: Load Confirmed Outline
            self._stage("Load Confirmed Outline", PipelineStage.RUNNING.value)
            self._progress(0.05)

            outline_path = self.project_path / "outlines" / "confirmed_outline.json"
            if not outline_path.exists():
                # Fallback to old format
                outline_path = self.project_path / "story_outline.json"
                if not outline_path.exists():
                    return {"success": False, "error": "No confirmed outline found. Run Outline Generator first."}

            outline_data = json.loads(outline_path.read_text(encoding="utf-8"))

            # Handle both formats
            if "beats" in outline_data:
                beats = outline_data.get("beats", [])
            else:
                beats = []
                for scene in outline_data.get("scenes", []):
                    for beat in scene.get("beats", []):
                        beats.append(beat.get("description", ""))
                    if not scene.get("beats") and scene.get("summary"):
                        beats.append(scene.get("summary"))

            if not beats:
                return {"success": False, "error": "No beats found in outline."}

            self._log(f"Loaded outline: {len(beats)} beats")
            self._stage("Load Confirmed Outline", PipelineStage.COMPLETE.value)

            # Stage 2: Load World Config
            self._stage("Load World Config", PipelineStage.RUNNING.value)
            self._progress(0.10)

            world_config_path = self.project_path / "world_bible" / "world_config.json"
            if not world_config_path.exists():
                return {"success": False, "error": "No world_config.json found. Run World Builder first."}

            world_config = json.loads(world_config_path.read_text(encoding="utf-8"))
            world_context_str = build_world_context(world_config)

            self._log(f"World: {world_config.get('world_context', {}).get('time_period', 'Unknown')}")
            self._stage("Load World Config", PipelineStage.COMPLETE.value)

            # Stage 3: Generate Frames (Batched)
            self._stage("Generate Frames", PipelineStage.RUNNING.value)
            self._progress(0.15)

            # Split into batches
            batches = [
                beats[i:i + self.BATCH_SIZE]
                for i in range(0, len(beats), self.BATCH_SIZE)
            ]

            self._log(f"Processing {len(batches)} scenes in parallel")

            # Create tasks for parallel processing
            async def process_scene(batch_idx: int, batch_beats: list[str]) -> tuple[int, Optional[dict]]:
                """Process a single scene and return (index, result)."""
                scene_offset = batch_idx * self.BATCH_SIZE
                result = await self._process_batch(
                    batch_beats=batch_beats,
                    scene_offset=scene_offset,
                    world_context=world_context_str,
                )
                return batch_idx, result

            # Launch all scenes in parallel
            tasks = [
                process_scene(batch_idx, batch_beats)
                for batch_idx, batch_beats in enumerate(batches)
            ]

            self._log(f"Launched {len(tasks)} parallel scene generation tasks...")

            # Gather results (preserves order via batch_idx)
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results in order
            all_scenes = []
            total_frames = 0
            completed = 0
            failed = 0

            for batch_idx, result in results:
                if isinstance(result, Exception):
                    self._log(f"  Scene {batch_idx + 1}: ERROR - {result}")
                    failed += 1
                elif result:
                    scenes = result.get("scenes", [])
                    frame_count = sum(len(s.get("frames", [])) for s in scenes)
                    all_scenes.extend(scenes)
                    total_frames += frame_count
                    completed += 1
                    self._log(f"  Scene {batch_idx + 1}: {frame_count} frames")
                else:
                    self._log(f"  Scene {batch_idx + 1}: ERROR - No result")
                    failed += 1

            self._log(f"Parallel generation complete: {completed} succeeded, {failed} failed")
            self._progress(0.85)

            self._stage("Generate Frames", PipelineStage.COMPLETE.value)
            self._progress(0.90)

            # Stage 4: Save Outputs
            self._stage("Save Outputs", PipelineStage.RUNNING.value)

            # Build visual script
            visual_script = {
                "title": world_config.get("title", outline_data.get("title", "Untitled")),
                "created_at": datetime.now().isoformat(),
                "pipeline": "cinestage-batched",
                "batch_size": self.BATCH_SIZE,
                "total_scenes": len(all_scenes),
                "total_frames": total_frames,
                "visual_style": world_config.get("visual_style", "live_action"),
                "scenes": all_scenes,
            }

            # Save outputs
            storyboard_dir = self.project_path / "storyboard"
            storyboard_dir.mkdir(parents=True, exist_ok=True)

            # visual_script.json
            vs_path = storyboard_dir / "visual_script.json"
            vs_path.write_text(json.dumps(visual_script, indent=2), encoding="utf-8")
            self._log("Saved visual_script.json")

            # prompts.json - for card UI (text → flip → image)
            # Build entity lookups for tag resolution
            entity_lookups = build_entity_lookups(world_config)
            prompts = self._extract_prompts(all_scenes, entity_lookups)
            prompts_path = storyboard_dir / "prompts.json"
            prompts_path.write_text(json.dumps(prompts, indent=2), encoding="utf-8")
            self._log(f"Saved prompts.json ({len(prompts)} cards)")

            # visual_script.md - readable version
            md_content = self._to_markdown(visual_script)
            md_path = storyboard_dir / "visual_script.md"
            md_path.write_text(md_content, encoding="utf-8")
            self._log("Saved visual_script.md")

            self._stage("Save Outputs", PipelineStage.COMPLETE.value)
            self._progress(1.0)

            return {
                "success": True,
                "visual_script_path": str(vs_path),
                "total_scenes": len(all_scenes),
                "total_frames": total_frames,
            }

        except Exception as e:
            logger.exception(f"CineStage pipeline error: {e}")
            return {"success": False, "error": str(e)}

    async def _process_batch(
        self,
        batch_beats: list[str],
        scene_offset: int,
        world_context: str,
    ) -> Optional[dict]:
        """Process a batch of beats into scenes.

        Args:
            batch_beats: List of beat texts to process
            scene_offset: Starting scene number offset
            world_context: World context string

        Note: Scenes are processed in parallel, so no sequential continuity
        context is passed. Character consistency is maintained via world_context.
        """

        # Build numbered beats text
        beats_text = "\n".join([
            f"{scene_offset + i + 1:02d}. {beat}"
            for i, beat in enumerate(batch_beats)
        ])

        # Build user prompt
        user_prompt = BATCH_USER_TEMPLATE.format(
            batch_size=len(batch_beats),
            start_scene=scene_offset + 1,
            end_scene=scene_offset + len(batch_beats),
            world_context=world_context,
            beats_text=beats_text,
        )

        try:
            response = await self.llm.generate(
                prompt=user_prompt,
                system_prompt=CINESTAGE_SYSTEM_PROMPT,
                max_tokens=16000,
                temperature=0.7,
            )

            # Parse JSON from response
            result = self._extract_json(response)

            if result:
                # Validate and fix scene numbers
                for scene in result.get("scenes", []):
                    scene_num = scene.get("scene_number", 0)
                    for j, frame in enumerate(scene.get("frames", [])):
                        # Ensure frame_id format is correct
                        frame_id = frame.get("frame_id", "")
                        if not frame_id.startswith(f"[{scene_num}."):
                            # Generate proper frame_id
                            camera = chr(ord('A') + (j % 2))  # Alternate A/B
                            frame_num = (j // 2) + 1
                            frame["frame_id"] = f"[{scene_num}.{frame_num}.c{camera}]"

                        # Ensure scene_number is set
                        frame["scene_number"] = scene_num

            return result

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return None

    def _extract_json(self, text: str) -> Optional[dict]:
        """Extract JSON from LLM response."""
        if not text:
            return None

        # Try JSON block
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                try:
                    return json.loads(text[start:end].strip())
                except json.JSONDecodeError:
                    pass

        # Try raw JSON
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

        return None

    def _extract_prompts(self, scenes: list[dict], entity_lookups: dict) -> list[dict]:
        """Extract prompts for card UI with proper entity tags for reference images."""
        prompts = []

        for scene in scenes:
            scene_num = scene.get("scene_number", 0)
            beat = scene.get("beat", "")
            location_name = scene.get("location", "")

            # Resolve location to tag
            location_tag = None
            if location_name:
                loc_key = location_name.lower()
                location_tag = entity_lookups["locations"].get(loc_key)
                # Try partial match if exact not found
                if not location_tag:
                    for name, tag in entity_lookups["locations"].items():
                        if name in loc_key or loc_key in name:
                            location_tag = tag
                            break

            for frame in scene.get("frames", []):
                prompt_text = frame.get("prompt", "")
                character_names = frame.get("characters", [])

                # Resolve character names to tags
                character_tags = []
                for char_name in character_names:
                    char_key = char_name.lower()
                    tag = entity_lookups["characters"].get(char_key)
                    if tag:
                        character_tags.append(tag)

                # Build tags dict for storyboard pipeline
                tags = {
                    "characters": character_tags,
                    "locations": [location_tag] if location_tag else [],
                    "props": [],  # Could be extracted from prompt in future
                }

                prompts.append({
                    "frame_id": frame.get("frame_id", ""),
                    "scene_number": scene_num,
                    "beat": beat[:50] + "..." if len(beat) > 50 else beat,
                    "shot_type": frame.get("shot_type", ""),
                    "camera_position": frame.get("camera_position", ""),
                    "prompt": prompt_text,
                    "characters": character_names,  # Keep names for display
                    "tags": tags,  # Entity tags for reference images
                    "word_count": len(prompt_text.split()),
                    "duration": frame.get("duration", 3.0),
                    # Card UI state
                    "generated": False,
                    "image_url": None,
                })

        return prompts

    def _to_markdown(self, visual_script: dict) -> str:
        """Convert visual script to readable markdown."""
        lines = [f"# {visual_script.get('title', 'Visual Script')}\n"]
        lines.append(f"**Generated:** {visual_script.get('created_at', 'Unknown')}")
        lines.append(f"**Pipeline:** {visual_script.get('pipeline', 'cinestage')}")
        lines.append(f"**Total Scenes:** {visual_script.get('total_scenes', 0)}")
        lines.append(f"**Total Frames:** {visual_script.get('total_frames', 0)}")
        lines.append(f"**Visual Style:** {visual_script.get('visual_style', 'live_action')}\n")
        lines.append("---\n")

        for scene in visual_script.get("scenes", []):
            scene_num = scene.get("scene_number", "?")
            lines.append(f"\n## Scene {scene_num}")
            lines.append(f"*{scene.get('beat', '')}*\n")
            lines.append(f"**Location:** {scene.get('location', 'Unknown')} | **Time:** {scene.get('time_of_day', 'day')}\n")

            for frame in scene.get("frames", []):
                frame_id = frame.get("frame_id", "?")
                shot = frame.get("shot_type", "MS")
                lines.append(f"### {frame_id} [{shot}]")
                lines.append(f"*Camera: {frame.get('camera_position', 'N/A')}*\n")

                prompt = frame.get("prompt", "")
                # Show first 300 chars as preview
                preview = prompt[:300] + "..." if len(prompt) > 300 else prompt
                lines.append(f"> {preview}\n")
                lines.append(f"**Words:** {len(prompt.split())} | **Characters:** {', '.join(frame.get('characters', []))}\n")

        return "\n".join(lines)


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def direct(project_path: Path, max_frames: int = None) -> dict:
    """Quick helper to run director pipeline."""
    pipeline = DirectorPipeline(project_path, max_frames=max_frames)
    return await pipeline.run()
