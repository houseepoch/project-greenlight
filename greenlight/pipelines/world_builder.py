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

# Each prompt is designed to generate 20-44 word responses for richer detail

WORLD_CONTEXT_PROMPTS = {
    "setting": """You are a world-building expert for cinematic pre-production.
Describe the SETTING of this story in 20-44 words.

Focus on: geographic location, specific region/country, environment type, climate, general atmosphere.
Be specific and evocative. This will inform all visual and character design decisions.

Example: "Imperial Tang Dynasty China, a bustling city district of Chang'an with narrow cobblestone streets, ornate wooden buildings with curved tile roofs, lantern-lit evenings, and flower markets at every corner."

Output ONLY the setting description, 20-44 words.""",

    "time_period": """You are a world-building expert for cinematic pre-production.
Describe the TIME PERIOD of this story in 20-44 words.

Focus on: specific era, year/century/decade, historical events shaping the period, technological and social context.
Be precise about what makes this moment in history distinctive.

Example: "Late Tang Dynasty, 8th century AD (circa 750-780 CE), the golden age of Chinese poetry and arts, just before the An Lushan Rebellion that would shake the empire."

Output ONLY the time period description, 20-44 words.""",

    "cultural_context": """You are a world-building expert for cinematic pre-production.
Describe the CULTURAL CONTEXT of this story in 20-44 words.

Focus on: dominant culture/ethnicity, social norms, belief systems, customs, values that drive character behavior.
This informs how characters interact, dress, and make decisions.

Example: "Han Chinese Confucian society with strict hierarchical protocols, filial piety governing family relationships, Buddhist temple influence, and a flourishing courtesan culture among the educated elite."

Output ONLY the cultural context, 20-44 words.""",

    "social_structure": """You are a world-building expert for cinematic pre-production.
Describe the SOCIAL STRUCTURE in 20-44 words.

Focus on: class system, power dynamics, who holds authority, how status is displayed through clothing and behavior.
This determines character status, conflicts, and visual costume hierarchy.

Example: "Rigid imperial hierarchy: emperor and nobility at apex, scholar-officials and military commanders mid-tier, merchants gaining influence through wealth, artisans respected for skill, courtesans owned but culturally valued."

Output ONLY the social structure description, 20-44 words.""",

    "technology_level": """You are a world-building expert for cinematic pre-production.
Describe the TECHNOLOGY LEVEL in 20-44 words.

Focus on: what technology exists, materials available, how people accomplish tasks, transportation, lighting, tools.
This prevents anachronisms in visual prompts and costume design.

Example: "Pre-industrial craftsmanship excellence: silk weaving, porcelain making, woodblock printing, paper money. Oil lanterns and candles for light, horses and sedan chairs for travel, no glass windows."

Output ONLY the technology level description, 20-44 words.""",

    "clothing_norms": """You are a costume designer for cinematic pre-production.
Describe the general CLOTHING NORMS for this setting in 20-44 words.

Focus on: silhouette shapes, typical garments by gender, common fabrics and materials, color significance, class distinctions in dress.
This is a REFERENCE for costume design, NOT story-specific character costumes.

Example: "Women wear layered hanfu with wide sleeves and floor-length skirts. Men wear changshan robes with topknots. Silk for nobility, cotton for commoners. Red for celebrations, white for mourning."

Output ONLY the clothing norms description, 20-44 words.""",

    "architecture_style": """You are a production designer for cinematic pre-production.
Describe the ARCHITECTURE STYLE in 20-44 words.

Focus on: building types, materials, structural features, decorative elements, distinctive visual characteristics.
This informs all location descriptions and establishes visual world consistency.

Example: "Traditional Tang wooden architecture: curved upswept tile roofs with glazed edges, red-lacquered columns, latticed paper screens, covered walkways connecting buildings, courtyard gardens with rock formations and ponds."

Output ONLY the architecture style description, 20-44 words.""",

    "color_palette": """You are an art director for cinematic pre-production.
Describe the dominant COLOR PALETTE in 20-44 words.

Focus on: primary colors, accent colors, colors by setting (interior/exterior), color meanings in this culture.
This creates visual consistency across all generated images.

Example: "Rich vermilion red for prosperity, imperial gold for nobility, jade green for life, ink black for calligraphy and hair. Interiors warm with amber lantern glow, exteriors muted earth tones."

Output ONLY the color palette description, 20-44 words.""",

    "lighting_style": """You are a cinematographer for cinematic pre-production.
Describe the LIGHTING STYLE in 20-44 words.

Focus on: primary light sources in this world, time of day preferences, mood lighting, interior vs exterior lighting quality.
This creates cinematic consistency across all scenes.

Example: "Warm golden hour sunlight through paper screens, intimate candlelight and lantern glow for night scenes, misty morning light outdoors, dramatic chiaroscuro shadows for tension."

Output ONLY the lighting style description, 20-44 words.""",

    "mood": """You are a director for cinematic pre-production.
Describe the overall MOOD/ATMOSPHERE in 20-44 words.

Focus on: emotional tone, underlying tensions, visual atmosphere, sensory qualities that pervade the story world.
This guides the emotional register and visual treatment of all scenes.

Example: "Simmering romantic tension beneath formal propriety, forbidden desire expressed through glances and poetry, melancholy beauty of impermanence, sensual intimacy in confined spaces, poetic longing."

Output ONLY the mood description, 20-44 words.""",
}


CHARACTER_FIELD_PROMPTS = {
    "appearance": """You are a character designer for cinematic pre-production.
Describe this character's PHYSICAL APPEARANCE in 30-50 words.

MUST INCLUDE IN THIS ORDER:
1. Ethnicity/race appropriate to the cultural context (e.g., "Chinese woman", "Japanese man", "African warrior")
2. Age (specific number or narrow range like "early 30s")
3. Gender
4. Body type/build and height impression
5. Facial features: face shape, eye shape/color, nose, lips
6. Skin tone
7. Hair: color, length, style, texture
8. 1-2 distinguishing physical traits

CRITICAL: Ethnicity MUST match the world's cultural context. Be specific for consistent visual reference.

Output ONLY the appearance description, 30-50 words.""",

    "clothing": """You are a costume designer for cinematic pre-production.
Describe this character's DEFAULT COSTUME in 20-35 words.

Focus on VISUAL DESIGN elements:
- Garment types and silhouettes
- Fabrics and textures
- Colors and patterns
- Accessories and adornments
- How clothing reflects their status/role

CRITICAL: Costume MUST match the world's clothing norms and time period.
Do NOT describe story context or emotions - only visual costume details.

Output ONLY the costume description, 20-35 words.""",

    "personality": """You are a character analyst for cinematic pre-production.
Describe this character's KEY PERSONALITY TRAITS in 15-30 words.

Focus on: core behavioral traits, emotional tendencies, how they carry themselves, interaction style with others.
This informs acting direction, posture, and expression in reference images.

Output ONLY the personality description, 15-30 words.""",

    "summary": """You are a character analyst for cinematic pre-production.
Write a brief CHARACTER SUMMARY in 20-35 words.

Combine: their role in the story, defining trait, central motivation, and key relationship.
This is the quick reference that captures who this character is.

Output ONLY the character summary, 20-35 words.""",
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

            # Load full source text for context - world builder needs the complete story
            source_text_path = self.project_path / "ingestion" / "source_text.json"
            source_text = ""
            if source_text_path.exists():
                source_data = json.loads(source_text_path.read_text(encoding="utf-8"))
                source_text = source_data.get("text", "")
                self._log(f"Loaded full source text ({len(source_text):,} chars) for context")

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

        # Use more source text for world context (up to 8000 chars)
        context_limit = min(len(source_text), 8000)

        for field_name in field_names:
            system_prompt = WORLD_CONTEXT_PROMPTS[field_name]
            user_prompt = f"""SOURCE MATERIAL:
{source_text[:context_limit]}

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
                # Truncate if too long (more than ~50 words)
                words = value.split()
                if len(words) > 50:
                    value = " ".join(words[:44]) + "..."

                field_values[field_name] = value
                self._field_update(f"world.{field_name}", value, "complete")
                self._log(f"  [OK] {field_name}: {value[:60]}...")

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

            # Extract character-specific context from full story
            char_context = self._extract_character_context(char_name, source_text)

            for field_name in field_names:
                system_prompt = CHARACTER_FIELD_PROMPTS[field_name]
                user_prompt = f"""CHARACTER: {char_name}
TAG: {char_tag}
ROLE: {char_data.get('role_hint', 'supporting')}

{world_context_str}

CHARACTER CONTEXT FROM STORY:
{char_context}

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
                    # Allow longer descriptions for appearance (50 words) and clothing (35 words)
                    max_words = 50 if field_name == "appearance" else 35
                    if len(words) > max_words:
                        value = " ".join(words[:max_words]) + "..."
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

            # Extract location-specific context from full story
            loc_context = self._extract_entity_context(loc_name, source_text)

            for field_name in field_names:
                system_prompt = LOCATION_FIELD_PROMPTS[field_name]
                user_prompt = f"""LOCATION: {loc_name}
TAG: {loc_tag}

{world_context_str}

LOCATION CONTEXT FROM STORY:
{loc_context}

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

            # Extract prop-specific context from full story
            prop_context = self._extract_entity_context(prop_name, source_text)

            prompt = f"""PROP: {prop_name}
TAG: {prop_tag}

{world_context_str}

PROP CONTEXT FROM STORY:
{prop_context}

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

    def _extract_character_context(self, char_name: str, source_text: str, max_chars: int = 4000) -> str:
        """Extract paragraphs mentioning a specific character from the source text.

        This ensures character descriptions are based on actual story content,
        not just the character name.
        """
        if not source_text or not char_name:
            return source_text[:max_chars] if source_text else ""

        # Split into paragraphs
        paragraphs = source_text.split('\n\n')
        relevant_paragraphs = []
        name_lower = char_name.lower()

        # Also check for partial name matches (e.g., "Dr. Watanabe" matches "Watanabe")
        name_parts = char_name.split()

        for para in paragraphs:
            para_lower = para.lower()
            # Check if character name or any name part is in paragraph
            if name_lower in para_lower or any(part.lower() in para_lower for part in name_parts if len(part) > 2):
                relevant_paragraphs.append(para.strip())

        if relevant_paragraphs:
            # Join relevant paragraphs up to max_chars
            context = "\n\n".join(relevant_paragraphs)
            if len(context) > max_chars:
                context = context[:max_chars] + "..."
            return context

        # Fallback: return beginning of story if no matches
        return source_text[:max_chars] if len(source_text) > max_chars else source_text

    def _extract_entity_context(self, entity_name: str, source_text: str, max_chars: int = 3000) -> str:
        """Extract paragraphs mentioning a specific entity (location/prop) from the source text."""
        if not source_text or not entity_name:
            return source_text[:max_chars] if source_text else ""

        # Split into paragraphs
        paragraphs = source_text.split('\n\n')
        relevant_paragraphs = []
        name_lower = entity_name.lower()

        # Also check for partial matches
        name_parts = [p for p in entity_name.split() if len(p) > 2]

        for para in paragraphs:
            para_lower = para.lower()
            # Check if entity name or significant parts are in paragraph
            if name_lower in para_lower or any(part.lower() in para_lower for part in name_parts):
                relevant_paragraphs.append(para.strip())

        if relevant_paragraphs:
            context = "\n\n".join(relevant_paragraphs)
            if len(context) > max_chars:
                context = context[:max_chars] + "..."
            return context

        # Fallback: return beginning of story
        return source_text[:max_chars] if len(source_text) > max_chars else source_text

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
