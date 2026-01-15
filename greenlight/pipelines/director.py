"""
Director Pipeline - Transforms confirmed outline beats into cinematic frames.

Flow:
1. Load confirmed_outline.json (beats from user-confirmed outline)
2. Load world_config.json (world context + enriched entities)
3. For each beat: generate scene breakdown with frames
4. Apply camera coverage logic (reactions, dialogue, action)
5. Output visual_script.json with parsable frame/camera structure

Structure:
- Each outline beat = 1 Scene
- Each scene = multiple Frames (visual moments)
- Each frame = 1+ Cameras (for coverage: reactions, OTS, etc.)

Frame ID format: {scene}.{frame}.c{camera}
- scene: beat number from outline (1-indexed)
- frame: shot number within scene (1-indexed)
- camera: A, B, C... for multi-camera coverage

Camera Coverage Rules:
- Dialogue: Speaker (cA) + Listener reaction (cB)
- Action with reaction: Action (cA) + Reaction shot (cB)
- Establishing: Single camera (cA)
- Emotional beats: CU/ECU single camera (cA)

TRACE: DIRECTOR-001
"""

import json
import logging
from pathlib import Path
from typing import Callable, Optional
from datetime import datetime

from greenlight.core.llm import LLMClient, generate_parallel
from greenlight.core.models import PipelineStage

logger = logging.getLogger(__name__)


# =============================================================================
# CAMERA NOTATION REFERENCE
# =============================================================================

CAMERA_NOTATIONS = {
    "EWS": "Extreme Wide Shot - Establishes vast environment",
    "WS": "Wide Shot - Full body, environment context",
    "MWS": "Medium Wide Shot - Knee up, some environment",
    "MS": "Medium Shot - Waist up, conversation framing",
    "MCU": "Medium Close-Up - Chest up, emotional clarity",
    "CU": "Close-Up - Face only, intimate emotion",
    "ECU": "Extreme Close-Up - Eyes/detail, intense focus",
    "OTS": "Over The Shoulder - Conversation, perspective",
    "POV": "Point of View - Character's exact viewpoint",
    "2S": "Two Shot - Two characters in frame",
    "3S": "Three Shot - Three characters in frame",
    "INSERT": "Insert Shot - Detail/prop focus",
}


# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

DIRECTOR_SYSTEM = """You are a cinematic director breaking down story beats into visual frames.

Your job is to take a single story beat and create 2-5 frames that visually tell that moment.
Each frame is a specific camera shot with a DETAILED image generation prompt.

CRITICAL PROMPT REQUIREMENTS:
- Each prompt MUST be 250-350 words (this is MANDATORY)
- Write rich, cinematic descriptions that paint the complete visual
- Include: lighting quality, atmosphere, textures, materials, colors, mood
- Describe character poses, expressions, body language in detail
- Specify camera angle, depth of field, foreground/background elements
- Reference the exact period costume details, architectural elements
- Create prompts suitable for high-quality AI image generation

CAMERA COVERAGE RULES:
1. DIALOGUE scenes need at least 2 cameras:
   - cA: Speaker (usually MS or MCU)
   - cB: Listener reaction (CU or MCU)

2. ACTION with REACTION needs 2 cameras:
   - cA: The action happening
   - cB: Character(s) reacting to the action

3. ESTABLISHING shots use single camera (cA):
   - WS or EWS to set the scene

4. EMOTIONAL beats may use single camera:
   - CU or ECU for intimate moments

5. IMPORTANT PROPS get INSERT shots:
   - Close detail of significant objects

WORLD CONTEXT RULES (MUST follow):
- Clothing MUST match world_context.clothing_norms exactly
- Architecture MUST match world_context.architecture_style
- Lighting MUST match world_context.lighting_style
- Props MUST be period-appropriate
- Color palette MUST be consistent with world_context

OUTPUT FORMAT:
Return a JSON object with frames array. Each frame needs:
- frame_id: "{scene}.{frame}.c{camera}" format
- prompt: DETAILED 250-350 word image generation prompt (REQUIRED LENGTH)
- visual_description: Brief 15-25 word shot description
- camera_notation: One of EWS, WS, MWS, MS, MCU, CU, ECU, OTS, POV, 2S, 3S, INSERT
- tags: {characters: [], locations: [], props: []}
- location_direction: NORTH, EAST, SOUTH, or WEST

Output ONLY valid JSON."""


BEAT_TO_FRAMES_TEMPLATE = """Break down this story beat into 2-5 cinematic frames.

SCENE {scene_number}
BEAT: {beat_text}

LOCATION: {location_name}
TIME OF DAY: {time_of_day}
CHARACTERS IN SCENE: {characters}

WORLD CONTEXT (ALL visuals MUST match exactly):
- Time Period: {time_period}
- Clothing: {clothing_norms}
- Architecture: {architecture_style}
- Lighting: {lighting_style}
- Color Palette: {color_palette}
- Mood: {mood}

CHARACTER APPEARANCES:
{character_details}

LOCATION DETAILS:
{location_details}

COVERAGE GUIDANCE:
{coverage_guidance}

CRITICAL: Each prompt MUST be 250-350 words. Include:
- Complete character descriptions (age, features, expression, pose, costume details)
- Exact camera framing and angle
- Lighting quality, direction, color temperature
- Background/foreground elements with depth
- Atmospheric details (dust motes, smoke, haze)
- Material textures (silk sheen, wood grain, stone)
- Emotional mood and tension
- Period-accurate props and architecture

Generate frames as JSON:
{{
    "scene_number": {scene_number},
    "beat": "{beat_text_escaped}",
    "location": "{location_name}",
    "time_of_day": "{time_of_day}",
    "frames": [
        {{
            "frame_id": "{scene_number}.1.cA",
            "prompt": "A 250-350 word detailed cinematic prompt describing the complete visual scene for AI image generation. Include character appearances, costume details, lighting, atmosphere, camera angle, depth of field, foreground and background elements, textures, materials, colors, mood, and period-accurate details...",
            "visual_description": "Brief 15-25 word shot description",
            "camera_notation": "MS",
            "tags": {{
                "characters": ["CHAR_TAG"],
                "locations": ["LOC_TAG"],
                "props": []
            }},
            "location_direction": "NORTH"
        }}
    ]
}}"""


# =============================================================================
# COVERAGE ANALYZER
# =============================================================================

def analyze_beat_for_coverage(beat_text: str) -> str:
    """Analyze a beat to determine camera coverage needs."""
    beat_lower = beat_text.lower()

    guidance_parts = []

    # Dialogue detection
    dialogue_keywords = ["says", "tells", "asks", "responds", "replies", "whispers",
                        "announces", "confesses", "reveals", "speaks", "declares"]
    if any(kw in beat_lower for kw in dialogue_keywords):
        guidance_parts.append("DIALOGUE detected - use cA for speaker, cB for listener reaction")

    # Reaction detection
    reaction_keywords = ["reacts", "shocked", "surprised", "gasps", "realizes",
                        "discovers", "notices", "sees", "witnesses", "watches"]
    if any(kw in beat_lower for kw in reaction_keywords):
        guidance_parts.append("REACTION detected - include reaction shot (cB) for emotional response")

    # Action detection
    action_keywords = ["runs", "fights", "grabs", "throws", "pushes", "falls",
                      "enters", "exits", "moves", "rushes", "strikes"]
    if any(kw in beat_lower for kw in action_keywords):
        guidance_parts.append("ACTION detected - capture the action (cA) and any reactions (cB)")

    # Establishing detection
    establishing_keywords = ["dawn", "dusk", "morning", "evening", "arrives at",
                            "enters the", "at the", "in the"]
    if any(kw in beat_lower for kw in establishing_keywords):
        guidance_parts.append("Consider ESTABLISHING shot (WS/EWS) to set the scene")

    # Emotional detection
    emotional_keywords = ["tears", "cries", "smiles", "longing", "love", "fear",
                         "hope", "despair", "joy", "pain", "anguish", "tender"]
    if any(kw in beat_lower for kw in emotional_keywords):
        guidance_parts.append("EMOTIONAL beat - use CU/ECU for intimate feeling")

    # Prop/object focus
    prop_keywords = ["holds", "picks up", "places", "gives", "receives", "reads",
                    "writes", "the letter", "the ring", "the sword", "the book"]
    if any(kw in beat_lower for kw in prop_keywords):
        guidance_parts.append("PROP focus detected - consider INSERT shot for key object")

    if not guidance_parts:
        guidance_parts.append("Standard coverage - start with establishing, then key moments")

    return "\n".join(f"- {g}" for g in guidance_parts)


def extract_characters_from_beat(beat_text: str, all_characters: list[dict]) -> list[str]:
    """Extract character tags mentioned in a beat."""
    beat_lower = beat_text.lower()
    found_chars = []

    for char in all_characters:
        name = char.get("name", "").lower()
        tag = char.get("tag", "")
        # Check for name in beat
        if name and name in beat_lower:
            found_chars.append(tag)

    return found_chars


def infer_location_from_beat(beat_text: str, all_locations: list[dict]) -> tuple[str, str]:
    """Infer location tag and name from beat text."""
    beat_lower = beat_text.lower()

    for loc in all_locations:
        name = loc.get("name", "").lower()
        tag = loc.get("tag", "")
        # Check for location name in beat
        if name and name in beat_lower:
            return tag, loc.get("name", "")

    # Default to first location or generic
    if all_locations:
        return all_locations[0].get("tag", "LOC_MAIN"), all_locations[0].get("name", "Main Location")

    return "LOC_SCENE", "Scene Location"


# =============================================================================
# DIRECTOR PIPELINE
# =============================================================================

class DirectorPipeline:
    """
    Director Pipeline - Generates visual script from confirmed outline.

    Takes confirmed_outline.json (list of beats) and generates:
    - visual_script.json with parsable frame/camera structure
    - prompts.json for image generation

    Each beat becomes a scene, each scene has multiple frames,
    each frame may have multiple cameras for coverage.
    """

    def __init__(
        self,
        project_path: Path,
        max_frames: Optional[int] = None,
        log_callback: Optional[Callable[[str], None]] = None,
        stage_callback: Optional[Callable[[str, str, Optional[str]], None]] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
    ):
        self.project_path = Path(project_path)
        self.max_frames = max_frames

        self._log = log_callback or (lambda x: logger.info(x))
        self._stage = stage_callback or (lambda *args: None)
        self._progress = progress_callback or (lambda x: None)

        self.llm = LLMClient()

    async def run(self) -> dict:
        """Execute the director pipeline."""
        try:
            # Stage 1: Load Confirmed Outline
            self._stage("Load Confirmed Outline", PipelineStage.RUNNING.value)
            self._progress(0.05)

            # Try new format first (confirmed_outline.json)
            outline_path = self.project_path / "outlines" / "confirmed_outline.json"
            if not outline_path.exists():
                # Fallback to old format
                outline_path = self.project_path / "story_outline.json"
                if not outline_path.exists():
                    return {"success": False, "error": "No confirmed outline found. Run Outline Generator first."}

            outline_data = json.loads(outline_path.read_text(encoding="utf-8"))

            # Handle both formats
            if "beats" in outline_data:
                # New format: list of beat strings
                beats = outline_data.get("beats", [])
            else:
                # Old format: scenes with beats
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
            world_context = world_config.get("world_context", {})
            characters = world_config.get("characters", [])
            locations = world_config.get("locations", [])

            self._log(f"World: {world_context.get('time_period', 'Unknown')}")
            self._log(f"Characters: {len(characters)}, Locations: {len(locations)}")
            self._stage("Load World Config", PipelineStage.COMPLETE.value)

            # Build lookup maps
            characters_map = {c["tag"]: c for c in characters}
            locations_map = {l["tag"]: l for l in locations}

            # Stage 3: Generate Frames for Each Beat
            self._stage("Generate Frames", PipelineStage.RUNNING.value)
            self._progress(0.15)

            all_scenes = []
            all_frames = []
            total_frames = 0

            for i, beat_text in enumerate(beats):
                scene_num = i + 1
                self._log(f"Scene {scene_num}: {beat_text[:50]}...")

                # Analyze beat for characters and location
                char_tags = extract_characters_from_beat(beat_text, characters)
                loc_tag, loc_name = infer_location_from_beat(beat_text, locations)

                # Infer time of day
                time_of_day = self._infer_time_of_day(beat_text)

                # Generate frames for this beat
                scene_data = await self._generate_beat_frames(
                    scene_num=scene_num,
                    beat_text=beat_text,
                    char_tags=char_tags if char_tags else [c["tag"] for c in characters[:2]],
                    loc_tag=loc_tag,
                    loc_name=loc_name,
                    time_of_day=time_of_day,
                    world_context=world_context,
                    characters_map=characters_map,
                    locations_map=locations_map,
                )

                if scene_data:
                    frames = scene_data.get("frames", [])
                    all_scenes.append(scene_data)
                    all_frames.extend(frames)
                    total_frames += len(frames)
                    self._log(f"  -> {len(frames)} frames generated")

                # Progress: 15% to 85%
                progress = 0.15 + (0.70 * (i + 1) / len(beats))
                self._progress(progress)

                # Check frame limit
                if self.max_frames and total_frames >= self.max_frames:
                    self._log(f"Reached frame limit ({self.max_frames})")
                    break

            self._stage("Generate Frames", PipelineStage.COMPLETE.value)
            self._progress(0.90)

            # Stage 4: Save Outputs
            self._stage("Save Outputs", PipelineStage.RUNNING.value)

            visual_script = {
                "title": world_config.get("title", outline_data.get("title", "Untitled")),
                "created_at": datetime.now().isoformat(),
                "total_scenes": len(all_scenes),
                "total_frames": total_frames,
                "visual_style": world_config.get("visual_style", "live_action"),
                "scenes": all_scenes,
                "frames": all_frames,  # Flattened for easy access
            }

            # Save outputs
            storyboard_dir = self.project_path / "storyboard"
            storyboard_dir.mkdir(parents=True, exist_ok=True)

            # visual_script.json
            vs_path = storyboard_dir / "visual_script.json"
            vs_path.write_text(json.dumps(visual_script, indent=2), encoding="utf-8")
            self._log("Saved visual_script.json")

            # prompts.json - for user editing
            prompts = self._extract_prompts(visual_script)
            prompts_path = storyboard_dir / "prompts.json"
            prompts_path.write_text(json.dumps(prompts, indent=2), encoding="utf-8")
            self._log(f"Saved prompts.json ({len(prompts)} prompts)")

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
            logger.exception(f"Director pipeline error: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_beat_frames(
        self,
        scene_num: int,
        beat_text: str,
        char_tags: list[str],
        loc_tag: str,
        loc_name: str,
        time_of_day: str,
        world_context: dict,
        characters_map: dict,
        locations_map: dict,
    ) -> Optional[dict]:
        """Generate frames for a single beat/scene."""

        # Analyze beat for coverage guidance
        coverage_guidance = analyze_beat_for_coverage(beat_text)

        # Format character details
        char_details = ""
        for tag in char_tags:
            char = characters_map.get(tag, {})
            if char:
                char_details += f"- {tag} ({char.get('name', 'Unknown')}):\n"
                char_details += f"  Appearance: {char.get('appearance', 'Not specified')}\n"
                char_details += f"  Clothing: {char.get('clothing', 'Period-appropriate attire')}\n"

        if not char_details:
            char_details = "Characters present in scene"

        # Format location details
        loc = locations_map.get(loc_tag, {})
        loc_details = f"- {loc_tag}: {loc.get('description', loc_name)}\n"
        if loc.get("view_north"):
            loc_details += f"  Looking North: {loc.get('view_north')}\n"
            loc_details += f"  Looking East: {loc.get('view_east', 'N/A')}\n"
            loc_details += f"  Looking South: {loc.get('view_south', 'N/A')}\n"
            loc_details += f"  Looking West: {loc.get('view_west', 'N/A')}\n"

        # Escape beat text for JSON template
        beat_escaped = beat_text.replace('"', '\\"').replace('\n', ' ')

        prompt = BEAT_TO_FRAMES_TEMPLATE.format(
            scene_number=scene_num,
            beat_text=beat_text,
            beat_text_escaped=beat_escaped[:100],
            location_name=loc_name,
            time_of_day=time_of_day,
            characters=", ".join(char_tags),
            time_period=world_context.get("time_period", ""),
            clothing_norms=world_context.get("clothing_norms", ""),
            architecture_style=world_context.get("architecture_style", ""),
            lighting_style=world_context.get("lighting_style", ""),
            color_palette=world_context.get("color_palette", ""),
            mood=world_context.get("mood", ""),
            character_details=char_details,
            location_details=loc_details,
            coverage_guidance=coverage_guidance,
        )

        try:
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=DIRECTOR_SYSTEM,
                max_tokens=4096,
                temperature=0.7,
            )

            scene_data = self._extract_json(response)
            if scene_data:
                # Ensure frame IDs are properly formatted
                for j, frame in enumerate(scene_data.get("frames", [])):
                    if not frame.get("frame_id") or not frame["frame_id"].startswith(f"{scene_num}."):
                        # Determine camera letter
                        camera = chr(ord('A') + (j % 26))
                        frame_num = (j // 2) + 1  # Pair frames for coverage
                        frame["frame_id"] = f"{scene_num}.{frame_num}.c{camera}"
                    frame["scene_number"] = scene_num

                return scene_data

        except Exception as e:
            logger.error(f"Frame generation failed for scene {scene_num}: {e}")

        return None

    def _infer_time_of_day(self, beat_text: str) -> str:
        """Infer time of day from beat text."""
        beat_lower = beat_text.lower()

        if any(kw in beat_lower for kw in ["dawn", "sunrise", "morning", "wakes"]):
            return "dawn"
        elif any(kw in beat_lower for kw in ["dusk", "sunset", "evening", "twilight"]):
            return "dusk"
        elif any(kw in beat_lower for kw in ["night", "midnight", "dark", "lantern", "candle"]):
            return "night"
        else:
            return "day"

    def _extract_json(self, text: str) -> Optional[dict]:
        """Extract JSON from LLM response."""
        if not text:
            return None

        # Try to find JSON block
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                try:
                    return json.loads(text[start:end].strip())
                except json.JSONDecodeError:
                    pass

        # Try to find raw JSON object
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

        return None

    def _extract_prompts(self, visual_script: dict) -> list[dict]:
        """Extract prompts for user editing and image generation."""
        prompts = []

        for frame in visual_script.get("frames", []):
            prompts.append({
                "frame_id": frame.get("frame_id", ""),
                "scene_number": frame.get("scene_number", 0),
                "prompt": frame.get("prompt", ""),
                "visual_description": frame.get("visual_description", ""),
                "camera_notation": frame.get("camera_notation", ""),
                "tags": frame.get("tags", {}),
                "location_direction": frame.get("location_direction", "NORTH"),
                "edited": False,
            })

        return prompts

    def _to_markdown(self, visual_script: dict) -> str:
        """Convert visual script to readable markdown."""
        lines = [f"# {visual_script.get('title', 'Visual Script')}\n"]
        lines.append(f"**Generated:** {visual_script.get('created_at', 'Unknown')}")
        lines.append(f"**Total Scenes:** {visual_script.get('total_scenes', 0)}")
        lines.append(f"**Total Frames:** {visual_script.get('total_frames', 0)}")
        lines.append(f"**Visual Style:** {visual_script.get('visual_style', 'live_action')}\n")
        lines.append("---\n")

        current_scene = None
        for frame in visual_script.get("frames", []):
            scene_num = frame.get("scene_number", 0)

            # New scene header
            if scene_num != current_scene:
                current_scene = scene_num
                # Find scene data
                scene_data = None
                for s in visual_script.get("scenes", []):
                    if s.get("scene_number") == scene_num:
                        scene_data = s
                        break

                if scene_data:
                    lines.append(f"\n## Scene {scene_num}")
                    lines.append(f"*{scene_data.get('beat', '')[:100]}...*\n")
                    lines.append(f"**Location:** {scene_data.get('location', 'Unknown')}")
                    lines.append(f"**Time:** {scene_data.get('time_of_day', 'day')}\n")

            # Frame details
            frame_id = frame.get("frame_id", "?")
            camera = frame.get("camera_notation", "MS")
            lines.append(f"### [{frame_id}] {camera}")
            lines.append(f"**{frame.get('visual_description', '')}**\n")
            lines.append(f"> {frame.get('prompt', '')}\n")

            tags = frame.get("tags", {})
            if tags.get("characters"):
                lines.append(f"*Characters:* {', '.join(tags['characters'])}")
            if tags.get("props"):
                lines.append(f"*Props:* {', '.join(tags['props'])}")
            lines.append("")

        return "\n".join(lines)


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def direct(project_path: Path, max_frames: int = None) -> dict:
    """Quick helper to run director pipeline."""
    pipeline = DirectorPipeline(project_path, max_frames=max_frames)
    return await pipeline.run()
