"""
Outline Generator Pipeline for Project Greenlight.

Takes a world_config.json and generates 3 different story outline variants
for user selection and editing.

Flow:
1. Load world_config.json (from world builder)
2. Generate 3 outline variants with different narrative approaches
3. User selects one, edits bullets (add/remove/modify)
4. Confirmed outline feeds into Director pipeline

Each outline is a list of high-level story events (bullets) that can be
easily edited by the user before the cinematic prompting phase.

TRACE: OUTLINE-001
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
# OUTLINE VARIANT APPROACHES
# =============================================================================

OUTLINE_APPROACHES = {
    "dramatic": {
        "name": "Dramatic Arc",
        "description": "Classic three-act structure with rising tension and emotional climax",
        "prompt": """Create a DRAMATIC story outline following classic three-act structure:

ACT 1 (Setup ~25%):
- Establish the world and protagonist
- Introduce the central conflict/desire
- Inciting incident that disrupts status quo

ACT 2 (Confrontation ~50%):
- Rising stakes and complications
- Relationship developments
- Midpoint reversal or revelation
- Darkest moment / all seems lost

ACT 3 (Resolution ~25%):
- Climactic confrontation
- Resolution of central conflict
- New equilibrium / changed world

Focus on EMOTIONAL BEATS and CHARACTER TRANSFORMATION."""
    },

    "mystery": {
        "name": "Mystery Unfolding",
        "description": "Gradual revelation structure with secrets and discoveries",
        "prompt": """Create a MYSTERY-DRIVEN story outline with gradual revelations:

OPENING:
- Establish intrigue and questions
- Plant seeds of mystery
- Hook the audience with unknowns

INVESTIGATION:
- Clues discovered progressively
- Red herrings and misdirection
- Character motivations questioned
- Secrets begin to surface

REVELATIONS:
- Major truth uncovered
- Stakes become clear
- Pieces fall into place

RESOLUTION:
- Final revelation / twist
- Consequences of truth
- New understanding

Focus on INFORMATION FLOW and AUDIENCE DISCOVERY."""
    },

    "character": {
        "name": "Character Journey",
        "description": "Internal transformation focus with relationship milestones",
        "prompt": """Create a CHARACTER-FOCUSED story outline emphasizing internal journey:

STASIS:
- Who is the protagonist at start?
- What do they believe/want/fear?
- Key relationships established

CATALYST:
- What disrupts their world?
- What forces them to change?
- New relationships/conflicts

STRUGGLE:
- Internal vs external conflict
- Relationship tests
- Growth through adversity
- Moments of doubt

TRANSFORMATION:
- Key realization/change
- Relationship resolutions
- Who have they become?

Focus on INTERNAL STATES and RELATIONSHIP DYNAMICS."""
    }
}


OUTLINE_SYSTEM_PROMPT = """You are a master storyteller creating a story outline.

OUTPUT FORMAT:
Generate a list of 8-15 story beats as bullet points. Each bullet should be:
- One clear sentence describing what happens
- Include character names/tags where relevant
- Be specific enough to visualize but brief enough to edit

Example format:
[
  "Mei watches Lin tend flowers from her brothel window at dawn, longing visible in her eyes",
  "Madame Chou announces a wealthy merchant is coming to bid on Mei's contract",
  "Mei devises a plan to win her freedom through a wager",
  ...
]

RULES:
- Use character names from the world config
- Reference locations by name
- Each beat should be one moment/event
- Cover the full story arc
- Keep bullets short (under 20 words each)
- Output valid JSON array of strings"""


# =============================================================================
# OUTLINE GENERATOR PIPELINE
# =============================================================================

class OutlineGeneratorPipeline:
    """
    Generates 3 story outline variants from world_config.json.

    Each variant uses a different narrative approach:
    - Dramatic Arc: Classic three-act structure
    - Mystery Unfolding: Revelation-based progression
    - Character Journey: Internal transformation focus
    """

    def __init__(
        self,
        project_path: Path,
        log_callback: Optional[Callable[[str], None]] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
        variant_callback: Optional[Callable[[str, str, list], None]] = None,
    ):
        """
        Initialize the outline generator.

        Args:
            project_path: Path to the project directory
            log_callback: Function to call with log messages
            progress_callback: Function to call with progress (0-1)
            variant_callback: Function to call when variant completes (name, description, beats)
        """
        self.project_path = Path(project_path)

        self._log = log_callback or (lambda x: logger.info(x))
        self._progress = progress_callback or (lambda x: None)
        self._variant_update = variant_callback or (lambda *args: None)

        self.llm = LLMClient()

    async def run(self) -> dict:
        """Generate 3 outline variants."""
        try:
            # Load world config
            self._log("Loading world config...")
            self._progress(0.05)

            world_config_path = self.project_path / "world_bible" / "world_config.json"
            if not world_config_path.exists():
                return {"success": False, "error": "No world_config.json found. Run World Builder first."}

            world_config = json.loads(world_config_path.read_text(encoding="utf-8"))

            # Extract key info for prompts
            title = world_config.get("title", "Untitled")
            world_context = world_config.get("world_context", {})
            characters = world_config.get("characters", [])
            locations = world_config.get("locations", [])

            # Also load pitch/source if available
            pitch_content = ""
            pitch_path = self.project_path / "world_bible" / "pitch.md"
            if pitch_path.exists():
                pitch_content = pitch_path.read_text(encoding="utf-8")
            else:
                # Try chunks for source material
                chunks_path = self.project_path / "ingestion" / "chunks.json"
                if chunks_path.exists():
                    chunks_data = json.loads(chunks_path.read_text(encoding="utf-8"))
                    chunks = chunks_data.get("chunks", [])[:5]
                    pitch_content = "\n\n".join([c.get("text", "") for c in chunks])

            self._log(f"Loaded: {title}")
            self._log(f"  Characters: {len(characters)}")
            self._log(f"  Locations: {len(locations)}")
            self._progress(0.10)

            # Build context string
            context = self._build_context_string(world_config, pitch_content)

            # Generate 3 variants in parallel
            self._log("Generating 3 outline variants in parallel...")

            variants = {}
            prompts = []
            approach_names = list(OUTLINE_APPROACHES.keys())

            for approach_key in approach_names:
                approach = OUTLINE_APPROACHES[approach_key]
                prompt = f"""{approach['prompt']}

STORY CONTEXT:
{context}

Generate 8-15 story beats as a JSON array of strings.
Each beat is one sentence describing a key story moment.
Use the character and location names provided."""

                prompts.append((prompt, OUTLINE_SYSTEM_PROMPT))

            # Run all 3 in parallel
            results = await generate_parallel(prompts, max_tokens=2048)

            self._progress(0.70)

            # Process results
            for i, (approach_key, result) in enumerate(zip(approach_names, results)):
                approach = OUTLINE_APPROACHES[approach_key]

                if isinstance(result, Exception):
                    self._log(f"  [WARN] {approach['name']} failed: {result}")
                    variants[approach_key] = {
                        "name": approach["name"],
                        "description": approach["description"],
                        "beats": [],
                        "error": str(result),
                    }
                    continue

                # Parse the beats
                beats = self._extract_beats(result)

                variants[approach_key] = {
                    "name": approach["name"],
                    "description": approach["description"],
                    "beats": beats,
                }

                self._log(f"  [OK] {approach['name']}: {len(beats)} beats")
                self._variant_update(approach["name"], approach["description"], beats)

            self._progress(0.90)

            # Save outline variants
            self._log("Saving outline variants...")

            outlines_dir = self.project_path / "outlines"
            outlines_dir.mkdir(parents=True, exist_ok=True)

            output = {
                "created_at": datetime.now().isoformat(),
                "title": title,
                "status": "pending_selection",
                "variants": variants,
                "selected_variant": None,
                "confirmed_beats": [],
            }

            outlines_path = outlines_dir / "outline_variants.json"
            outlines_path.write_text(
                json.dumps(output, indent=2),
                encoding="utf-8"
            )

            self._progress(1.0)
            self._log("Outline generation complete!")

            return {
                "success": True,
                "outlines_path": str(outlines_path),
                "variants": {
                    k: {"name": v["name"], "beat_count": len(v["beats"])}
                    for k, v in variants.items()
                },
            }

        except Exception as e:
            logger.exception(f"Outline generation error: {e}")
            return {"success": False, "error": str(e)}

    def _build_context_string(self, world_config: dict, pitch: str) -> str:
        """Build context string for outline generation."""
        parts = []

        # Title and genre
        parts.append(f"TITLE: {world_config.get('title', 'Untitled')}")
        parts.append(f"GENRE: {world_config.get('genre', 'Drama')}")

        if world_config.get("logline"):
            parts.append(f"LOGLINE: {world_config['logline']}")

        # World context
        world_context = world_config.get("world_context", {})
        if world_context.get("time_period"):
            parts.append(f"SETTING: {world_context['time_period']}")
        if world_context.get("mood"):
            parts.append(f"MOOD: {world_context['mood']}")

        # Characters
        characters = world_config.get("characters", [])
        if characters:
            char_lines = []
            for c in characters:
                role = c.get("role", "supporting")
                summary = c.get("summary", "")
                char_lines.append(f"  - {c['name']} ({role}): {summary[:100]}...")
            parts.append("CHARACTERS:\n" + "\n".join(char_lines))

        # Locations
        locations = world_config.get("locations", [])
        if locations:
            loc_lines = [f"  - {l['name']}" for l in locations]
            parts.append("LOCATIONS:\n" + "\n".join(loc_lines))

        # Source material (truncated)
        if pitch:
            parts.append(f"SOURCE MATERIAL:\n{pitch[:2000]}...")

        return "\n\n".join(parts)

    def _extract_beats(self, text: str) -> list[str]:
        """Extract beat list from LLM response."""
        if not text:
            return []

        # Try JSON array
        try:
            # Find JSON array
            start = text.find("[")
            end = text.rfind("]") + 1
            if start >= 0 and end > start:
                beats = json.loads(text[start:end])
                if isinstance(beats, list):
                    return [str(b).strip() for b in beats if b]
        except json.JSONDecodeError:
            pass

        # Fallback: extract bullet points
        beats = []
        for line in text.split("\n"):
            line = line.strip()
            # Match bullet points (-, *, numbers)
            if line.startswith(("-", "*", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
                # Clean up the line
                beat = line.lstrip("-*0123456789.) ").strip()
                if beat and len(beat) > 10:
                    beats.append(beat)

        return beats


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def generate_outlines(project_path: Path) -> dict:
    """Quick helper to generate outline variants."""
    pipeline = OutlineGeneratorPipeline(project_path)
    return await pipeline.run()
