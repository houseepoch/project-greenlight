"""
World Builder Pipeline for Project Greenlight.

Takes confirmed entities from ingestion and progressively builds
the complete world bible with:
- Core world context (setting, time period, culture)
- Character descriptions (10-24 words per field)
- Location descriptions with directional views
- Prop descriptions

Fields populate progressively in parallel, with status updates
for real-time UI updates.

TRACE: INGEST-003
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from greenlight.core.llm import LLMClient, generate_parallel
from greenlight.core.models import (
    Character,
    Location,
    Prop,
    WorldConfig,
    WorldContext,
    FieldStatus,
    PipelineStage,
)

logger = logging.getLogger(__name__)


# =============================================================================
# SYSTEM PROMPTS - World Bible Generation
# =============================================================================

# Each prompt is designed to generate 10-24 word responses for consistency

WORLD_CONTEXT_PROMPTS = {
    "setting": """You are a world-building expert. Based on the source material provided,
describe the SETTING of this story in 10-24 words.

Focus on: geographic location, environment, general atmosphere.
Be specific and evocative. This will inform all visual decisions.

Example: "A mist-shrouded mountain village in feudal Japan, surrounded by ancient cedar forests and sacred shrines."

Output ONLY the setting description, 10-24 words.""",

    "time_period": """You are a world-building expert. Based on the source material provided,
describe the TIME PERIOD of this story in 10-24 words.

Focus on: specific era, year/century if applicable, historical context.
Be precise about technological and social development.

Example: "Late Edo period Japan, 1860s, on the cusp of modernization as Western influence begins."

Output ONLY the time period description, 10-24 words.""",

    "cultural_context": """You are a world-building expert. Based on the source material provided,
describe the CULTURAL CONTEXT of this story in 10-24 words.

Focus on: social norms, belief systems, customs, values that drive character behavior.
This informs how characters interact and make decisions.

Example: "Strict Confucian hierarchy governs all relationships; honor and family duty override personal desire."

Output ONLY the cultural context, 10-24 words.""",

    "social_structure": """You are a world-building expert. Based on the source material provided,
describe the SOCIAL STRUCTURE in 10-24 words.

Focus on: class system, power dynamics, who holds authority and why.
This determines character status and conflicts.

Example: "Rigid caste system with samurai nobility, merchant class rising in influence, peasants bound to land."

Output ONLY the social structure description, 10-24 words.""",

    "technology_level": """You are a world-building expert. Based on the source material provided,
describe the TECHNOLOGY LEVEL in 10-24 words.

Focus on: what technology exists, what doesn't, how people accomplish tasks.
This prevents anachronisms in visual prompts.

Example: "Pre-industrial craftsmanship, paper lanterns and candles for light, horses and palanquins for travel."

Output ONLY the technology level description, 10-24 words.""",

    "clothing_norms": """You are a world-building expert. Based on the source material provided,
describe the CLOTHING NORMS in 10-24 words.

Focus on: typical garments, materials, styles appropriate to the setting.
This MUST inform all character costume descriptions.

Example: "Flowing hanfu robes in silk and cotton, jade ornaments, elaborate hairstyles with pins for women."

Output ONLY the clothing norms description, 10-24 words.""",

    "architecture_style": """You are a world-building expert. Based on the source material provided,
describe the ARCHITECTURE STYLE in 10-24 words.

Focus on: building types, materials, distinctive features of the setting.
This informs all location descriptions.

Example: "Traditional wooden pavilions with curved tile roofs, paper screens, rock gardens, covered walkways."

Output ONLY the architecture style description, 10-24 words.""",

    "color_palette": """You are a world-building expert. Based on the source material provided,
describe the dominant COLOR PALETTE in 10-24 words.

Focus on: colors that define the visual mood of this world.
This creates visual consistency across all generated images.

Example: "Muted earth tones with vermillion accents, ink black, jade green, gold highlights on nobility."

Output ONLY the color palette description, 10-24 words.""",

    "lighting_style": """You are a world-building expert. Based on the source material provided,
describe the LIGHTING STYLE in 10-24 words.

Focus on: how scenes are typically lit, light sources available in this world.
This creates cinematic consistency.

Example: "Warm candlelight and paper lantern glow indoors, misty natural light outdoors, dramatic shadows."

Output ONLY the lighting style description, 10-24 words.""",

    "mood": """You are a world-building expert. Based on the source material provided,
describe the overall MOOD/ATMOSPHERE in 10-24 words.

Focus on: emotional tone, tension, underlying feelings that pervade the story.
This guides the emotional register of all scenes.

Example: "Simmering romantic tension beneath strict propriety, forbidden desire, melancholy beauty of impermanence."

Output ONLY the mood description, 10-24 words.""",
}


CHARACTER_FIELD_PROMPTS = {
    "appearance": """You are a character designer for cinematic pre-production.
Describe this character's PHYSICAL APPEARANCE in 20-40 words.

Include: age, body type/build, height impression, facial structure, skin tone, eye shape/color, hair style/color/length, and 1-2 distinguishing physical traits.
Be specific enough for visual reference generation with consistent likeness.

CRITICAL: Appearance must be appropriate for the world context provided.

Output ONLY the appearance description, 20-40 words.""",

    "clothing": """You are a costume designer for cinematic pre-production.
Describe this character's TYPICAL CLOTHING in 10-24 words.

CRITICAL: Clothing MUST match the world context clothing norms.
- If historical setting: period-appropriate garments only
- If modern setting: appropriate contemporary styles
- NEVER anachronistic clothing

Output ONLY the clothing description, 10-24 words.""",

    "personality": """You are a character analyst for cinematic pre-production.
Describe this character's KEY PERSONALITY TRAITS in 10-24 words.

Focus on: core traits that drive their behavior, how they interact with others.
This informs acting direction and dialogue tone.

Output ONLY the personality description, 10-24 words.""",

    "summary": """You are a character analyst for cinematic pre-production.
Write a brief CHARACTER SUMMARY in 15-24 words.

Combine their role, key trait, and central conflict/motivation.
This is the quick reference for this character.

Output ONLY the character summary, 15-24 words.""",
}


LOCATION_FIELD_PROMPTS = {
    "description": """You are a production designer for cinematic pre-production.
Describe this LOCATION in 15-24 words.

Focus on: physical space, atmosphere, key visual elements.
CRITICAL: Architecture must match the world context style.

Output ONLY the location description, 15-24 words.""",

    "view_north": """You are a cinematographer planning camera setups.
Describe what a camera sees looking NORTH in this location, in 10-20 words.

Focus on: key visual elements, depth, lighting from this angle.
This helps with reference image generation from specific angles.

Output ONLY the north view description, 10-20 words.""",

    "view_east": """You are a cinematographer planning camera setups.
Describe what a camera sees looking EAST in this location, in 10-20 words.

Focus on: key visual elements, depth, lighting from this angle.

Output ONLY the east view description, 10-20 words.""",

    "view_south": """You are a cinematographer planning camera setups.
Describe what a camera sees looking SOUTH in this location, in 10-20 words.

Focus on: key visual elements, depth, lighting from this angle.

Output ONLY the south view description, 10-20 words.""",

    "view_west": """You are a cinematographer planning camera setups.
Describe what a camera sees looking WEST in this location, in 10-20 words.

Focus on: key visual elements, depth, lighting from this angle.

Output ONLY the west view description, 10-20 words.""",
}


PROP_FIELD_PROMPTS = {
    "description": """You are a prop master for cinematic pre-production.
Describe this PROP in 10-24 words.

Focus on: physical appearance, material, distinctive features.
CRITICAL: Design must be appropriate for the world context.

Output ONLY the prop description, 10-24 words.""",

    "significance": """You are a story analyst for cinematic pre-production.
Describe this prop's STORY SIGNIFICANCE in 10-20 words.

Focus on: why this prop matters, what it represents, how it's used.

Output ONLY the significance description, 10-20 words.""",
}


# =============================================================================
# WORLD BUILDER PIPELINE
# =============================================================================

class WorldBuilderPipeline:
    """
    World Builder Pipeline - Progressive World Bible Generation.

    Takes confirmed entities and builds complete world bible with
    progressive field population for real-time UI updates.

    Outputs:
    - world_config.json (complete world bible)
    """

    def __init__(
        self,
        project_path: Path,
        visual_style: str = "live_action",
        log_callback: Optional[Callable[[str], None]] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
        field_callback: Optional[Callable[[str, str, str], None]] = None,
    ):
        """
        Initialize the world builder.

        Args:
            project_path: Path to the project directory
            visual_style: Visual style for the storyboard
            log_callback: Function to call with log messages
            progress_callback: Function to call with progress (0-1)
            field_callback: Function to call when a field completes (field_name, value, status)
        """
        self.project_path = Path(project_path)
        self.visual_style = visual_style

        self._log = log_callback or (lambda x: logger.info(x))
        self._progress = progress_callback or (lambda x: None)
        self._field_update = field_callback or (lambda *args: None)

        self.llm = LLMClient()

    async def run(self) -> dict:
        """Execute the world builder pipeline."""
        try:
            # Load confirmed entities
            self._log("Loading confirmed entities...")
            self._progress(0.02)

            confirmed_path = self.project_path / "ingestion" / "confirmed_entities.json"
            if not confirmed_path.exists():
                return {"success": False, "error": "No confirmed entities found"}

            confirmed_data = json.loads(confirmed_path.read_text(encoding="utf-8"))
            entities = confirmed_data.get("entities", {})
            world_hints = confirmed_data.get("world_hints", {})

            # Load source chunks for context
            chunks_path = self.project_path / "ingestion" / "chunks.json"
            source_text = ""
            if chunks_path.exists():
                chunks_data = json.loads(chunks_path.read_text(encoding="utf-8"))
                # Combine first few chunks as context (not all to avoid token limits)
                chunks = chunks_data.get("chunks", [])[:5]
                source_text = "\n\n".join([c.get("text", "") for c in chunks])

            self._log(f"Entities: {len(entities.get('characters', []))} characters, "
                     f"{len(entities.get('locations', []))} locations, "
                     f"{len(entities.get('props', []))} props")

            self._progress(0.05)

            # Phase 1: Generate World Context (parallel)
            self._log("Generating world context...")
            world_context = await self._generate_world_context(source_text, world_hints)
            self._progress(0.25)

            # Phase 2: Generate Character Fields (parallel per character)
            self._log("Generating character descriptions...")
            characters = await self._generate_characters(
                entities.get("characters", []),
                world_context,
                source_text,
            )
            self._progress(0.50)

            # Phase 3: Generate Location Fields (parallel per location)
            self._log("Generating location descriptions...")
            locations = await self._generate_locations(
                entities.get("locations", []),
                world_context,
                source_text,
            )
            self._progress(0.75)

            # Phase 4: Generate Prop Fields
            self._log("Generating prop descriptions...")
            props = await self._generate_props(
                entities.get("props", []),
                world_context,
                source_text,
            )
            self._progress(0.90)

            # Build and save world config
            self._log("Saving world config...")

            all_tags = (
                [c.tag for c in characters] +
                [l.tag for l in locations] +
                [p.tag for p in props]
            )

            world_config = WorldConfig(
                title=self._extract_title(source_text),
                genre="Drama",  # Could be extracted from world hints
                visual_style=self.visual_style,
                logline="",
                synopsis="",
                themes=[],
                world_context=world_context,
                characters=characters,
                locations=locations,
                props=props,
                all_tags=all_tags,
                status="draft",
            )

            # Save to world_bible directory
            world_bible_dir = self.project_path / "world_bible"
            world_bible_dir.mkdir(parents=True, exist_ok=True)

            config_path = world_bible_dir / "world_config.json"
            config_path.write_text(
                json.dumps(world_config.model_dump(), indent=2),
                encoding="utf-8"
            )

            self._progress(1.0)
            self._log("World bible complete!")

            return {
                "success": True,
                "world_config_path": str(config_path),
                "characters": len(characters),
                "locations": len(locations),
                "props": len(props),
            }

        except Exception as e:
            logger.exception(f"World builder error: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_world_context(
        self,
        source_text: str,
        world_hints: dict,
    ) -> WorldContext:
        """Generate all world context fields in parallel."""
        # Build context string from hints
        hints_str = ""
        if world_hints:
            if world_hints.get("time_periods"):
                hints_str += f"Time period hints: {', '.join(world_hints['time_periods'])}\n"
            if world_hints.get("cultural_contexts"):
                hints_str += f"Cultural hints: {', '.join(world_hints['cultural_contexts'])}\n"
            if world_hints.get("visual_styles"):
                hints_str += f"Visual style hints: {', '.join(world_hints['visual_styles'])}\n"

        # Build prompts for all world context fields
        prompts = []
        field_names = list(WORLD_CONTEXT_PROMPTS.keys())

        for field_name in field_names:
            system_prompt = WORLD_CONTEXT_PROMPTS[field_name]
            user_prompt = f"""SOURCE MATERIAL:
{source_text[:3000]}

{hints_str}

Generate the {field_name.replace('_', ' ')} for this story world."""

            prompts.append((user_prompt, system_prompt))

        # Generate all in parallel
        self._log(f"  Generating {len(field_names)} world context fields in parallel...")
        results = await generate_parallel(prompts, max_tokens=150)

        # Build WorldContext from results
        field_values = {}
        for i, (field_name, result) in enumerate(zip(field_names, results)):
            if isinstance(result, Exception):
                self._log(f"  [WARN] {field_name} failed: {result}")
                field_values[field_name] = ""
            else:
                # Clean the result (remove any extra text)
                value = result.strip()
                # Truncate if too long (more than ~30 words)
                words = value.split()
                if len(words) > 30:
                    value = " ".join(words[:24]) + "..."

                field_values[field_name] = value
                self._field_update(f"world.{field_name}", value, "complete")
                self._log(f"  [OK] {field_name}: {value[:50]}...")

        return WorldContext(
            time_period=field_values.get("time_period", ""),
            technology_level=field_values.get("technology_level", ""),
            cultural_context=field_values.get("cultural_context", ""),
            social_structure=field_values.get("social_structure", ""),
            clothing_norms=field_values.get("clothing_norms", ""),
            architecture_style=field_values.get("architecture_style", ""),
            color_palette=field_values.get("color_palette", ""),
            lighting_style=field_values.get("lighting_style", ""),
            mood=field_values.get("mood", ""),
            setting_rules=[],  # Could be generated separately if needed
        )

    async def _generate_characters(
        self,
        char_entities: list[dict],
        world_context: WorldContext,
        source_text: str,
    ) -> list[Character]:
        """Generate character fields with world context awareness."""
        if not char_entities:
            return []

        characters = []

        for char_data in char_entities:
            char_name = char_data.get("name", "Unknown")
            char_tag = char_data.get("tag", f"CHAR_{char_name.upper().replace(' ', '_')}")

            self._log(f"  Generating {char_name}...")

            # Build prompts for all character fields
            prompts = []
            field_names = list(CHARACTER_FIELD_PROMPTS.keys())

            world_context_str = f"""WORLD CONTEXT:
Time Period: {world_context.time_period}
Cultural Context: {world_context.cultural_context}
Clothing Norms: {world_context.clothing_norms}
Social Structure: {world_context.social_structure}"""

            for field_name in field_names:
                system_prompt = CHARACTER_FIELD_PROMPTS[field_name]
                user_prompt = f"""CHARACTER: {char_name}
TAG: {char_tag}
ROLE: {char_data.get('role_hint', 'supporting')}

{world_context_str}

SOURCE MATERIAL EXCERPT:
{source_text[:2000]}

Generate the {field_name} for this character."""

                prompts.append((user_prompt, system_prompt))

            # Generate all fields in parallel
            results = await generate_parallel(prompts, max_tokens=150)

            # Build Character from results
            field_values = {}
            for field_name, result in zip(field_names, results):
                if isinstance(result, Exception):
                    field_values[field_name] = ""
                else:
                    value = result.strip()
                    words = value.split()
                    if len(words) > 30:
                        value = " ".join(words[:24]) + "..."
                    field_values[field_name] = value
                    self._field_update(f"character.{char_tag}.{field_name}", value, "complete")

            characters.append(Character(
                tag=char_tag,
                name=char_name,
                role=char_data.get("role_hint", "supporting"),
                appearance=field_values.get("appearance", ""),
                clothing=field_values.get("clothing", ""),
                personality=field_values.get("personality", ""),
                summary=field_values.get("summary", ""),
            ))

            self._log(f"    [OK] {char_name} complete")

        return characters

    async def _generate_locations(
        self,
        loc_entities: list[dict],
        world_context: WorldContext,
        source_text: str,
    ) -> list[Location]:
        """Generate location fields with directional views."""
        if not loc_entities:
            return []

        locations = []

        for loc_data in loc_entities:
            loc_name = loc_data.get("name", "Unknown")
            loc_tag = loc_data.get("tag", f"LOC_{loc_name.upper().replace(' ', '_')}")

            self._log(f"  Generating {loc_name}...")

            # Build prompts for all location fields
            prompts = []
            field_names = list(LOCATION_FIELD_PROMPTS.keys())

            world_context_str = f"""WORLD CONTEXT:
Time Period: {world_context.time_period}
Architecture Style: {world_context.architecture_style}
Lighting Style: {world_context.lighting_style}
Color Palette: {world_context.color_palette}"""

            for field_name in field_names:
                system_prompt = LOCATION_FIELD_PROMPTS[field_name]
                user_prompt = f"""LOCATION: {loc_name}
TAG: {loc_tag}

{world_context_str}

SOURCE MATERIAL EXCERPT:
{source_text[:2000]}

Generate the {field_name.replace('_', ' ')} for this location."""

                prompts.append((user_prompt, system_prompt))

            # Generate all fields in parallel
            results = await generate_parallel(prompts, max_tokens=150)

            # Build Location from results
            field_values = {}
            for field_name, result in zip(field_names, results):
                if isinstance(result, Exception):
                    field_values[field_name] = ""
                else:
                    value = result.strip()
                    words = value.split()
                    if len(words) > 25:
                        value = " ".join(words[:20]) + "..."
                    field_values[field_name] = value
                    self._field_update(f"location.{loc_tag}.{field_name}", value, "complete")

            locations.append(Location(
                tag=loc_tag,
                name=loc_name,
                description=field_values.get("description", ""),
                view_north=field_values.get("view_north", ""),
                view_east=field_values.get("view_east", ""),
                view_south=field_values.get("view_south", ""),
                view_west=field_values.get("view_west", ""),
            ))

            self._log(f"    [OK] {loc_name} complete")

        return locations

    async def _generate_props(
        self,
        prop_entities: list[dict],
        world_context: WorldContext,
        source_text: str,
    ) -> list[Prop]:
        """Generate prop descriptions."""
        if not prop_entities:
            return []

        props = []

        # Props are simpler - just description
        for prop_data in prop_entities:
            prop_name = prop_data.get("name", "Unknown")
            prop_tag = prop_data.get("tag", f"PROP_{prop_name.upper().replace(' ', '_')}")

            world_context_str = f"""WORLD CONTEXT:
Time Period: {world_context.time_period}
Technology Level: {world_context.technology_level}"""

            prompt = f"""PROP: {prop_name}
TAG: {prop_tag}

{world_context_str}

SOURCE MATERIAL EXCERPT:
{source_text[:1500]}

Generate a brief description (10-24 words) of this prop's appearance and significance."""

            try:
                result = await self.llm.generate(
                    prompt=prompt,
                    system_prompt=PROP_FIELD_PROMPTS["description"],
                    max_tokens=150,
                )

                description = result.strip()
                words = description.split()
                if len(words) > 30:
                    description = " ".join(words[:24]) + "..."

                self._field_update(f"prop.{prop_tag}.description", description, "complete")

                props.append(Prop(
                    tag=prop_tag,
                    name=prop_name,
                    description=description,
                ))

            except Exception as e:
                logger.warning(f"Prop generation failed for {prop_name}: {e}")
                props.append(Prop(tag=prop_tag, name=prop_name))

        return props

    def _extract_title(self, source_text: str) -> str:
        """Extract or generate a title from source text."""
        # Simple heuristic: look for common title patterns
        lines = source_text.split('\n')
        for line in lines[:10]:
            line = line.strip()
            # Skip empty lines and very long lines
            if not line or len(line) > 100:
                continue
            # If it looks like a title (short, possibly with special formatting)
            if line.startswith('#') or line.isupper() or len(line.split()) <= 6:
                return line.strip('#').strip()

        return "Untitled Project"


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def build_world(project_path: Path, visual_style: str = "live_action") -> dict:
    """Quick helper to build world bible."""
    pipeline = WorldBuilderPipeline(project_path, visual_style)
    return await pipeline.run()
