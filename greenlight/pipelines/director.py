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
    """Build world context string for LLM prompts."""
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

    # Characters
    if characters:
        lines.append("\nCHARACTERS:")
        for char in characters:
            name = char.get("name", "Unknown")
            appearance = char.get("appearance", "")
            clothing = char.get("clothing", "")
            desc = f"- {name}: {appearance}"
            if clothing:
                desc += f", {clothing}"
            lines.append(desc)

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

    BATCH_SIZE = 5  # Optimal batch size for consistent prompt quality

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

            self._log(f"Processing {len(batches)} batches of {self.BATCH_SIZE} scenes")

            all_scenes = []
            total_frames = 0

            for batch_idx, batch_beats in enumerate(batches):
                scene_offset = batch_idx * self.BATCH_SIZE
                start_scene = scene_offset + 1
                end_scene = scene_offset + len(batch_beats)

                self._log(f"[Batch {batch_idx + 1}/{len(batches)}] Scenes {start_scene}-{end_scene}")

                # Process batch
                batch_result = await self._process_batch(
                    batch_beats=batch_beats,
                    scene_offset=scene_offset,
                    world_context=world_context_str,
                )

                if batch_result:
                    scenes = batch_result.get("scenes", [])
                    frame_count = sum(len(s.get("frames", [])) for s in scenes)
                    all_scenes.extend(scenes)
                    total_frames += frame_count
                    self._log(f"  -> {len(scenes)} scenes, {frame_count} frames")
                else:
                    self._log(f"  -> ERROR: Batch failed")

                # Progress: 15% to 85%
                progress = 0.15 + (0.70 * (batch_idx + 1) / len(batches))
                self._progress(progress)

                # Check frame limit
                if self.max_frames and total_frames >= self.max_frames:
                    self._log(f"Reached frame limit ({self.max_frames})")
                    break

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
        """Process a batch of beats into scenes."""

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
