"""
Writer Pipeline - World-first extraction with 5-agent consensus.

Flow:
1. Load pitch
2. Extract WORLD CONTEXT first (time period, culture, clothing, etc.)
3. Extract entities with 5-agent consensus (removes hallucinations)
4. Enrich entities with world context (clothing, appearance appropriate to setting)
5. Generate story outline (light, editable)
6. Save outputs for user review

The world context rolls over to inform ALL entity extraction and enrichment.
"""

import json
import logging
import re
from collections import Counter
from pathlib import Path
from typing import Callable, Optional
from datetime import datetime

from greenlight.core.llm import LLMClient, generate_parallel
from greenlight.core.models import (
    PipelineStage,
    WorldContext,
    WorldConfig,
    Character,
    Location,
    Prop,
    StoryOutline,
    SceneOutline,
    SceneBeat,
)

logger = logging.getLogger(__name__)


# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

WORLD_CONTEXT_SYSTEM = """You are a world-building expert. Analyze the pitch and extract the WORLD CONTEXT - the setting details that will inform all character and location design.

Output valid JSON with this exact structure:
{
    "title": "Story title",
    "genre": "Primary genre",
    "logline": "One compelling sentence",
    "synopsis": "2-3 paragraph summary",
    "themes": ["theme1", "theme2"],
    "time_period": "Specific era and location (e.g., 'Tang Dynasty China, 8th century')",
    "technology_level": "What technology exists (e.g., 'Pre-industrial, paper/ink, no electricity')",
    "cultural_context": "Social norms, hierarchy, customs (e.g., 'Confucian hierarchy, courtesans as artists')",
    "social_structure": "Class system, power dynamics",
    "clothing_norms": "What people wear in this setting (e.g., 'Hanfu, silk robes, jade ornaments')",
    "architecture_style": "Building styles (e.g., 'Traditional Chinese pavilions, paper screens')",
    "color_palette": "Dominant colors of the world",
    "lighting_style": "How scenes are lit (e.g., 'Candlelight, lanterns, natural sunlight')",
    "mood": "Overall atmosphere",
    "setting_rules": ["Rule 1", "Rule 2"]
}

Be specific and detailed - these details constrain ALL character appearances and costumes."""


# 5 Agent perspectives for consensus extraction
AGENT_PERSPECTIVES = {
    "narrative": """You are a NARRATIVE analyst. Extract entities that are CRITICAL TO THE PLOT.
Focus on: protagonists, antagonists, mentors, key locations where plot happens, plot-critical props.
Only include entities that drive the story forward.""",

    "visual": """You are a VISUAL analyst. Extract entities that APPEAR ON SCREEN.
Focus on: characters we SEE, locations we VISIT, props that are SHOWN.
Only include entities with clear visual presence.""",

    "character": """You are a CHARACTER analyst. Extract entities related to RELATIONSHIPS and ROLES.
Focus on: all named characters, their relationships, supporting cast.
Include love interests, family members, allies, enemies.""",

    "technical": """You are a TECHNICAL analyst. Extract LANDMARK locations and SIGNIFICANT props.
Focus on: key settings, important objects, items with plot significance.
Include locations where key scenes happen, props that matter to the story.""",

    "holistic": """You are a HOLISTIC analyst. Extract entities for WORLD-BUILDING.
Focus on: atmosphere, setting elements, background characters, environmental details.
Include elements that establish the world even if not plot-critical.""",
}

ENTITY_EXTRACTION_TEMPLATE = """{perspective}

WORLD CONTEXT (use for reference):
Time Period: {time_period}
Cultural Context: {cultural_context}
Setting: {setting_rules}

PITCH TEXT:
{pitch}

Extract entities as JSON with this format:
{{
    "characters": [
        {{"tag": "CHAR_NAME", "name": "Display Name", "role": "protagonist/antagonist/supporting/love_interest/mentor"}}
    ],
    "locations": [
        {{"tag": "LOC_NAME", "name": "Display Name"}}
    ],
    "props": [
        {{"tag": "PROP_NAME", "name": "Display Name"}}
    ]
}}

TAG FORMAT RULES:
- Use CHAR_ prefix for characters, LOC_ for locations, PROP_ for props
- Use UPPERCASE_WITH_UNDERSCORES (e.g., CHAR_MEI, LOC_PALACE_COURTYARD)
- Keep tags concise but identifiable
- Do NOT include placeholder tags like [CHARACTER_NAME] or [LOCATION]

Only output valid JSON."""


CHARACTER_ENRICHMENT_SYSTEM = """You enrich character details based on the world context.
The character's appearance and clothing MUST be appropriate for the time period and culture.

CRITICAL: Clothing must match the world context clothing norms.
- If set in historical China: hanfu, silk robes, traditional garments
- If set in medieval Europe: period-appropriate garments
- NEVER use modern clothing unless the world is explicitly modern

Output valid JSON:
{
    "appearance": "Physical description (age, build, features, hair)",
    "clothing": "Period-appropriate attire (MUST match world context)",
    "personality": "Key traits and behavior",
    "summary": "2-3 sentence character overview"
}"""


LOCATION_ENRICHMENT_SYSTEM = """You enrich location details based on the world context.
Architecture and details MUST be appropriate for the time period and culture.

Output valid JSON:
{
    "description": "Detailed location description",
    "view_north": "What you see looking north",
    "view_east": "What you see looking east",
    "view_south": "What you see looking south",
    "view_west": "What you see looking west"
}"""


STORY_OUTLINE_SYSTEM = """You create a story outline with scene-by-scene breakdown.
This is a LIGHT planning document - short descriptions only.

Use the provided character and location tags consistently.

Output valid JSON:
{
    "scenes": [
        {
            "scene_number": 1,
            "title": "Short scene title",
            "location_tag": "LOC_NAME",
            "location_name": "Location Name",
            "time_of_day": "day/night/dawn/dusk",
            "characters": ["CHAR_NAME1", "CHAR_NAME2"],
            "summary": "1-2 sentence description of what happens",
            "beats": [
                {"description": "First key moment", "characters": ["CHAR_NAME1"]},
                {"description": "Second key moment", "characters": ["CHAR_NAME1", "CHAR_NAME2"]}
            ]
        }
    ]
}"""


# =============================================================================
# WRITER PIPELINE
# =============================================================================

class WriterPipeline:
    """
    Writer Pipeline - World-first extraction with consensus.

    Outputs:
    - world_config.json (world context + enriched entities)
    - story_outline.json (editable scene breakdown)
    """

    def __init__(
        self,
        project_path: Path,
        visual_style: str = "live_action",
        media_type: str = "standard",
        log_callback: Optional[Callable[[str], None]] = None,
        stage_callback: Optional[Callable[[str, str, Optional[str]], None]] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
    ):
        self.project_path = Path(project_path)
        self.visual_style = visual_style
        self.media_type = media_type

        self._log = log_callback or (lambda x: None)
        self._stage = stage_callback or (lambda *args: None)
        self._progress = progress_callback or (lambda x: None)

        self.llm = LLMClient()

    async def run(self) -> dict:
        """Execute the writer pipeline."""
        try:
            # Stage 1: Load Pitch
            self._stage("Load Pitch", PipelineStage.RUNNING.value)
            self._progress(0.02)

            pitch_path = self.project_path / "world_bible" / "pitch.md"
            if not pitch_path.exists():
                return {"success": False, "error": "No pitch.md found"}

            pitch_content = pitch_path.read_text(encoding="utf-8")
            self._log(f"Loaded pitch ({len(pitch_content)} chars)")
            self._stage("Load Pitch", PipelineStage.COMPLETE.value)

            # Stage 2: Extract World Context FIRST
            self._stage("Extract World Context", PipelineStage.RUNNING.value)
            self._progress(0.05)
            self._log("Extracting world context (time period, culture, clothing)...")

            world_data = await self._extract_world_context(pitch_content)
            if not world_data:
                return {"success": False, "error": "Failed to extract world context"}

            world_context = WorldContext(
                time_period=world_data.get("time_period", ""),
                technology_level=world_data.get("technology_level", ""),
                cultural_context=world_data.get("cultural_context", ""),
                social_structure=world_data.get("social_structure", ""),
                clothing_norms=world_data.get("clothing_norms", ""),
                architecture_style=world_data.get("architecture_style", ""),
                color_palette=world_data.get("color_palette", ""),
                lighting_style=world_data.get("lighting_style", ""),
                mood=world_data.get("mood", ""),
                setting_rules=world_data.get("setting_rules", []),
            )

            self._log(f"World: {world_context.time_period}")
            self._log(f"Clothing: {world_context.clothing_norms}")
            self._stage("Extract World Context", PipelineStage.COMPLETE.value)
            self._progress(0.15)

            # Stage 3: 5-Agent Consensus Entity Extraction
            self._stage("Extract Entities (5-Agent Consensus)", PipelineStage.RUNNING.value)
            self._log("Running 5-agent consensus extraction...")

            entities = await self._extract_entities_consensus(pitch_content, world_context)

            self._log(f"Consensus: {len(entities['characters'])} characters, "
                     f"{len(entities['locations'])} locations, "
                     f"{len(entities['props'])} props")
            self._stage("Extract Entities (5-Agent Consensus)", PipelineStage.COMPLETE.value)
            self._progress(0.35)

            # Stage 4: Enrich Entities with World Context
            self._stage("Enrich Entities", PipelineStage.RUNNING.value)
            self._log("Enriching entities with world context...")

            characters = await self._enrich_characters(entities["characters"], world_context)
            locations = await self._enrich_locations(entities["locations"], world_context)
            props = self._create_props(entities["props"])

            self._log(f"Enriched {len(characters)} characters, {len(locations)} locations")
            self._stage("Enrich Entities", PipelineStage.COMPLETE.value)
            self._progress(0.55)

            # Stage 5: Generate Story Outline
            self._stage("Generate Story Outline", PipelineStage.RUNNING.value)
            self._log("Generating story outline...")

            story_outline = await self._generate_story_outline(
                pitch_content, world_data, characters, locations, props
            )

            self._log(f"Generated {len(story_outline.scenes)} scenes")
            self._stage("Generate Story Outline", PipelineStage.COMPLETE.value)
            self._progress(0.80)

            # Stage 6: Save Outputs
            self._stage("Save Outputs", PipelineStage.RUNNING.value)

            # Build all_tags list
            all_tags = (
                [c.tag for c in characters] +
                [l.tag for l in locations] +
                [p.tag for p in props]
            )

            # Create WorldConfig
            world_config = WorldConfig(
                title=world_data.get("title", "Untitled"),
                genre=world_data.get("genre", "Drama"),
                visual_style=self.visual_style,
                logline=world_data.get("logline", ""),
                synopsis=world_data.get("synopsis", ""),
                themes=world_data.get("themes", []),
                world_context=world_context,
                characters=characters,
                locations=locations,
                props=props,
                all_tags=all_tags,
                status="draft",
            )

            # Save world_config.json
            world_bible_dir = self.project_path / "world_bible"
            world_bible_dir.mkdir(parents=True, exist_ok=True)
            world_config_path = world_bible_dir / "world_config.json"
            world_config_path.write_text(
                json.dumps(world_config.model_dump(), indent=2),
                encoding="utf-8"
            )
            self._log("Saved world_config.json")

            # Save story_outline.json
            outline_path = self.project_path / "story_outline.json"
            outline_path.write_text(
                json.dumps(story_outline.model_dump(), indent=2),
                encoding="utf-8"
            )
            self._log("Saved story_outline.json")

            # Update project.json timestamp
            self._update_project_timestamp()

            self._stage("Save Outputs", PipelineStage.COMPLETE.value)
            self._progress(1.0)

            return {
                "success": True,
                "world_config_path": str(world_config_path),
                "story_outline_path": str(outline_path),
                "characters": len(characters),
                "locations": len(locations),
                "props": len(props),
                "scenes": len(story_outline.scenes),
            }

        except Exception as e:
            logger.exception(f"Writer pipeline error: {e}")
            return {"success": False, "error": str(e)}

    async def _extract_world_context(self, pitch: str) -> Optional[dict]:
        """Extract world context from pitch - this happens FIRST."""
        prompt = f"""Analyze this pitch and extract the WORLD CONTEXT:

{pitch}

Output only valid JSON."""

        try:
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=WORLD_CONTEXT_SYSTEM,
                max_tokens=2048,
            )
            return self._extract_json(response)
        except Exception as e:
            logger.error(f"World context extraction failed: {e}")
            return None

    async def _extract_entities_consensus(
        self, pitch: str, world_context: WorldContext
    ) -> dict:
        """
        Run 5-agent consensus entity extraction.

        Each agent extracts entities from their perspective.
        Only entities with ≥80% agreement (4/5 agents) are accepted.
        This removes hallucinated entities.
        """
        # Build prompts for all 5 agents
        prompts = []
        for perspective_name, perspective_prompt in AGENT_PERSPECTIVES.items():
            prompt = ENTITY_EXTRACTION_TEMPLATE.format(
                perspective=perspective_prompt,
                time_period=world_context.time_period,
                cultural_context=world_context.cultural_context,
                setting_rules=", ".join(world_context.setting_rules),
                pitch=pitch,
            )
            prompts.append((prompt, ""))  # No system prompt, it's in the user prompt

        # Run all 5 agents in parallel
        self._log("  Running 5 agents in parallel...")
        results = await generate_parallel(prompts, max_tokens=2048)

        # Parse results from each agent
        all_characters = []
        all_locations = []
        all_props = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Agent {i} failed: {result}")
                continue

            try:
                data = self._extract_json(result)
                if data:
                    # Normalize tags to uppercase
                    for char in data.get("characters", []):
                        tag = char.get("tag", "").upper()
                        if tag and tag.startswith("CHAR_"):
                            all_characters.append((tag, char.get("name", ""), char.get("role", "")))

                    for loc in data.get("locations", []):
                        tag = loc.get("tag", "").upper()
                        if tag and tag.startswith("LOC_"):
                            all_locations.append((tag, loc.get("name", "")))

                    for prop in data.get("props", []):
                        tag = prop.get("tag", "").upper()
                        if tag and tag.startswith("PROP_"):
                            all_props.append((tag, prop.get("name", "")))
            except Exception as e:
                logger.warning(f"Failed to parse agent {i} result: {e}")

        # Apply consensus (80% = 4/5 agents)
        consensus_threshold = 0.8
        num_agents = 5

        def apply_consensus(items: list) -> list:
            """Keep only items that appear in ≥80% of agents."""
            tag_counts = Counter(item[0] for item in items)
            consensus_tags = {
                tag for tag, count in tag_counts.items()
                if count / num_agents >= consensus_threshold
            }

            # Get the first occurrence with full data for each consensus tag
            seen = set()
            result = []
            for item in items:
                if item[0] in consensus_tags and item[0] not in seen:
                    seen.add(item[0])
                    result.append(item)
            return result

        consensus_chars = apply_consensus(all_characters)
        consensus_locs = apply_consensus(all_locations)
        consensus_props = apply_consensus(all_props)

        self._log(f"  Consensus threshold: {consensus_threshold * 100}%")
        self._log(f"  Characters: {len(set(c[0] for c in all_characters))} found → {len(consensus_chars)} accepted")
        self._log(f"  Locations: {len(set(l[0] for l in all_locations))} found → {len(consensus_locs)} accepted")
        self._log(f"  Props: {len(set(p[0] for p in all_props))} found → {len(consensus_props)} accepted")

        return {
            "characters": [{"tag": c[0], "name": c[1], "role": c[2]} for c in consensus_chars],
            "locations": [{"tag": l[0], "name": l[1]} for l in consensus_locs],
            "props": [{"tag": p[0], "name": p[1]} for p in consensus_props],
        }

    async def _enrich_characters(
        self, characters: list[dict], world_context: WorldContext
    ) -> list[Character]:
        """Enrich characters with world-context-aware details."""
        if not characters:
            return []

        # Build prompts for all characters
        prompts = []
        for char in characters:
            prompt = f"""Enrich this character:
Tag: {char['tag']}
Name: {char['name']}
Role: {char.get('role', 'supporting')}

WORLD CONTEXT (character must fit this setting):
Time Period: {world_context.time_period}
Cultural Context: {world_context.cultural_context}
Clothing Norms: {world_context.clothing_norms}
Social Structure: {world_context.social_structure}

Generate appearance, clothing (MUST match world context clothing norms), personality, and summary.
Output only valid JSON."""

            prompts.append((prompt, CHARACTER_ENRICHMENT_SYSTEM))

        # Run enrichment in parallel
        results = await generate_parallel(prompts, max_tokens=1024)

        enriched = []
        for i, (char, result) in enumerate(zip(characters, results)):
            if isinstance(result, Exception):
                logger.warning(f"Character enrichment failed for {char['tag']}: {result}")
                # Create basic character
                enriched.append(Character(
                    tag=char["tag"],
                    name=char["name"],
                    role=char.get("role", "supporting"),
                ))
                continue

            try:
                data = self._extract_json(result)
                if data:
                    enriched.append(Character(
                        tag=char["tag"],
                        name=char["name"],
                        role=char.get("role", "supporting"),
                        appearance=data.get("appearance", ""),
                        clothing=data.get("clothing", ""),
                        personality=data.get("personality", ""),
                        summary=data.get("summary", ""),
                    ))
                else:
                    enriched.append(Character(
                        tag=char["tag"],
                        name=char["name"],
                        role=char.get("role", "supporting"),
                    ))
            except Exception as e:
                logger.warning(f"Failed to parse character enrichment: {e}")
                enriched.append(Character(
                    tag=char["tag"],
                    name=char["name"],
                    role=char.get("role", "supporting"),
                ))

        return enriched

    async def _enrich_locations(
        self, locations: list[dict], world_context: WorldContext
    ) -> list[Location]:
        """Enrich locations with world-context-aware details and directional views."""
        if not locations:
            return []

        # Build prompts for all locations
        prompts = []
        for loc in locations:
            prompt = f"""Enrich this location:
Tag: {loc['tag']}
Name: {loc['name']}

WORLD CONTEXT (location must fit this setting):
Time Period: {world_context.time_period}
Architecture Style: {world_context.architecture_style}
Cultural Context: {world_context.cultural_context}
Lighting Style: {world_context.lighting_style}

Generate description and 4 directional views (what you see looking N/E/S/W).
Output only valid JSON."""

            prompts.append((prompt, LOCATION_ENRICHMENT_SYSTEM))

        # Run enrichment in parallel
        results = await generate_parallel(prompts, max_tokens=1024)

        enriched = []
        for loc, result in zip(locations, results):
            if isinstance(result, Exception):
                logger.warning(f"Location enrichment failed for {loc['tag']}: {result}")
                enriched.append(Location(tag=loc["tag"], name=loc["name"]))
                continue

            try:
                data = self._extract_json(result)
                if data:
                    enriched.append(Location(
                        tag=loc["tag"],
                        name=loc["name"],
                        description=data.get("description", ""),
                        view_north=data.get("view_north", ""),
                        view_east=data.get("view_east", ""),
                        view_south=data.get("view_south", ""),
                        view_west=data.get("view_west", ""),
                    ))
                else:
                    enriched.append(Location(tag=loc["tag"], name=loc["name"]))
            except Exception as e:
                logger.warning(f"Failed to parse location enrichment: {e}")
                enriched.append(Location(tag=loc["tag"], name=loc["name"]))

        return enriched

    def _create_props(self, props: list[dict]) -> list[Prop]:
        """Create prop objects (simple, no enrichment needed)."""
        return [Prop(tag=p["tag"], name=p["name"]) for p in props]

    async def _generate_story_outline(
        self,
        pitch: str,
        world_data: dict,
        characters: list[Character],
        locations: list[Location],
        props: list[Prop],
    ) -> StoryOutline:
        """Generate light story outline for user editing."""
        # Determine scene count
        scene_counts = {"short": "3-5", "standard": "8-12", "feature": "15-20"}
        scene_range = scene_counts.get(self.media_type, "8-12")

        # Format entities for prompt
        char_list = "\n".join([f"- {c.tag}: {c.name} ({c.role})" for c in characters])
        loc_list = "\n".join([f"- {l.tag}: {l.name}" for l in locations])
        prop_list = "\n".join([f"- {p.tag}: {p.name}" for p in props])

        prompt = f"""Create a story outline for this pitch:

PITCH:
{pitch}

TITLE: {world_data.get('title', 'Untitled')}
GENRE: {world_data.get('genre', 'Drama')}
LOGLINE: {world_data.get('logline', '')}

AVAILABLE CHARACTERS:
{char_list or "None defined"}

AVAILABLE LOCATIONS:
{loc_list or "None defined"}

AVAILABLE PROPS:
{prop_list or "None defined"}

Generate {scene_range} scenes. Use the exact character and location tags provided.
Keep descriptions SHORT - this is a planning document.
Output only valid JSON."""

        try:
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=STORY_OUTLINE_SYSTEM,
                max_tokens=4096,
            )

            data = self._extract_json(response)
            if data and "scenes" in data:
                scenes = []
                for s in data["scenes"]:
                    beats = [
                        SceneBeat(
                            description=b.get("description", ""),
                            characters=b.get("characters", [])
                        )
                        for b in s.get("beats", [])
                    ]
                    scenes.append(SceneOutline(
                        scene_number=s.get("scene_number", len(scenes) + 1),
                        title=s.get("title", ""),
                        location_tag=s.get("location_tag", ""),
                        location_name=s.get("location_name", ""),
                        time_of_day=s.get("time_of_day", "day"),
                        characters=s.get("characters", []),
                        summary=s.get("summary", ""),
                        beats=beats,
                    ))

                return StoryOutline(
                    title=world_data.get("title", "Untitled"),
                    total_scenes=len(scenes),
                    scenes=scenes,
                    status="draft",
                )
        except Exception as e:
            logger.error(f"Story outline generation failed: {e}")

        # Return empty outline on failure
        return StoryOutline(title=world_data.get("title", "Untitled"), status="draft")

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

    def _update_project_timestamp(self):
        """Update project.json last_modified timestamp."""
        config_path = self.project_path / "project.json"
        if config_path.exists():
            try:
                config = json.loads(config_path.read_text(encoding="utf-8"))
                config["last_modified"] = datetime.now().isoformat()
                config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
            except Exception:
                pass
