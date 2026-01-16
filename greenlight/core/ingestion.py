"""
Document Ingestion Pipeline for Project Greenlight.

Handles pitch/synopsis ingestion and entity extraction.
Processes full text without chunking to maintain complete context.

Flow:
1. Process pitch/synopsis text
2. Extract entities using full context
3. Save source text and entities for world builder
4. Output: source_text.json, extracted_entities.json

TRACE: INGEST-001
"""

import json
import logging
from pathlib import Path
from typing import Callable, Optional
from datetime import datetime

from .config import settings
from .llm import LLMClient, generate_parallel

logger = logging.getLogger(__name__)


# =============================================================================
# SYSTEM PROMPTS FOR ENTITY EXTRACTION
# =============================================================================

ENTITY_EXTRACTION_SYSTEM = """You are an entity extraction specialist for cinematic pre-production.

Extract ALL NAMED ENTITIES from the provided story text. Read the ENTIRE text carefully.

1. CHARACTERS: Named people, described individuals who could be characters
   - Include protagonists, antagonists, supporting characters
   - Note their role if apparent (protagonist, love interest, mentor, etc.)
   - Include ALL named characters, even minor ones

2. LOCATIONS: Named places, described settings
   - Include specific rooms, buildings, cities, landscapes
   - Note if interior/exterior when apparent

3. PROPS: Significant named objects
   - Only include items with story significance
   - Skip generic items unless specifically described

CRITICAL RULES:
- Read the ENTIRE story text before extracting - characters may appear anywhere
- Only extract entities that are EXPLICITLY mentioned or clearly described
- Do NOT invent or hallucinate entities
- Use the exact names as written in the text
- For unnamed entities, use descriptive names (e.g., "The Old Man", "Palace Courtyard")

Output JSON:
{
    "characters": [
        {"name": "Character Name", "role_hint": "protagonist/antagonist/supporting/mentioned", "context": "brief description from story"}
    ],
    "locations": [
        {"name": "Location Name", "type_hint": "interior/exterior/both", "context": "brief description from story"}
    ],
    "props": [
        {"name": "Prop Name", "significance": "plot/character/setting", "context": "brief description from story"}
    ]
}

If no entities of a type are found, return an empty array for that type."""


# =============================================================================
# UTILITIES
# =============================================================================

def estimate_tokens(text: str) -> int:
    """Estimate token count (rough approximation: ~4 chars per token)."""
    return len(text) // 4


class IngestionPipeline:
    """
    Ingestion Pipeline for Project Greenlight.

    Processes pitch/synopsis text and extracts entities using full context.
    No chunking - the entire text is processed as one unit.

    Outputs:
    - source_text.json: Full source text for world builder
    - extracted_entities.json: Pre-confirmation entity list
    """

    def __init__(
        self,
        project_path: Path,
        log_callback: Optional[Callable[[str], None]] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
    ):
        self.project_path = Path(project_path)
        self._log = log_callback or (lambda x: logger.info(x))
        self._progress = progress_callback or (lambda x: None)
        self.llm = LLMClient()

    async def ingest_files(self, file_paths: list[Path], pitch: Optional[str] = None) -> dict:
        """
        Ingest pitch text and extract entities using full context.

        Args:
            file_paths: List of file paths to process (kept for compatibility)
            pitch: The pitch/synopsis text for entity extraction

        Returns:
            Dict with source text, entities, and processing results
        """
        has_pitch = pitch and pitch.strip()

        if not has_pitch:
            self._log("No pitch/synopsis provided")
            return {"success": False, "error": "No pitch/synopsis provided"}

        self._log("Starting entity extraction from pitch...")
        self._progress(0.10)

        # Use the pitch as the full source text
        source_text = pitch.strip()
        char_count = len(source_text)
        token_estimate = estimate_tokens(source_text)

        self._log(f"Processing {char_count:,} characters (~{token_estimate:,} tokens)")
        self._progress(0.20)

        # Extract entities from the FULL text (no chunking)
        self._log("Extracting entities from full text...")
        entities = await self._extract_entities_from_text(source_text)

        self._progress(0.70)

        # Deduplicate entities
        self._log("Deduplicating entities...")
        merged_entities = self._dedupe_entities(entities)

        self._progress(0.85)

        # Save outputs
        self._log("Saving outputs...")
        output_dir = self.project_path / "ingestion"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save full source text (for world builder to use)
        source_path = output_dir / "source_text.json"
        source_path.write_text(
            json.dumps({
                "created_at": datetime.now().isoformat(),
                "char_count": char_count,
                "token_estimate": token_estimate,
                "text": source_text,
            }, indent=2),
            encoding="utf-8"
        )

        # Save extracted entities (pre-confirmation)
        entities_path = output_dir / "extracted_entities.json"
        entities_path.write_text(
            json.dumps({
                "created_at": datetime.now().isoformat(),
                "status": "pending_confirmation",
                "has_pitch": True,
                "source_files": {"documents": [], "images": []},
                "entities": merged_entities,
                "world_hints": {},
            }, indent=2),
            encoding="utf-8"
        )

        self._progress(1.0)
        self._log("Ingestion complete!")

        return {
            "success": True,
            "source_path": str(source_path),
            "entities_path": str(entities_path),
            "stats": {
                "documents_processed": 0,
                "images_processed": 0,
                "total_chunks": 1,  # Full text as single "chunk"
                "characters_found": len(merged_entities.get("characters", [])),
                "locations_found": len(merged_entities.get("locations", [])),
                "props_found": len(merged_entities.get("props", [])),
            }
        }

    async def _extract_entities_from_text(self, text: str) -> dict:
        """Extract entities using 3 parallel LLM calls and take consensus.

        Only entities that appear in all 3 extractions are included.
        This reduces hallucinations and ensures reliable extraction.
        """
        if not text:
            return {"characters": [], "locations": [], "props": []}

        prompt = f"""Extract all entities from this story:

---
{text}
---

Output only valid JSON with all characters, locations, and props found."""

        # Run 3 parallel extractions
        prompts = [(prompt, ENTITY_EXTRACTION_SYSTEM)] * 3

        try:
            self._log("  Running 3 parallel extractions...")
            results = await generate_parallel(prompts, max_tokens=4096)

            # Parse all results
            extractions = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"Extraction {i+1} failed: {result}")
                    continue
                data = self._extract_json(result)
                if data:
                    extractions.append(data)
                    self._log(f"  Extraction {i+1}: {len(data.get('characters', []))} chars, "
                             f"{len(data.get('locations', []))} locs, {len(data.get('props', []))} props")

            if not extractions:
                return {"characters": [], "locations": [], "props": []}

            # Find consensus - entities present in all extractions
            consensus = self._find_consensus(extractions)
            self._log(f"  Consensus: {len(consensus['characters'])} chars, "
                     f"{len(consensus['locations'])} locs, {len(consensus['props'])} props")

            return consensus

        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")

        return {"characters": [], "locations": [], "props": []}

    def _find_consensus(self, extractions: list[dict]) -> dict:
        """Find entities that appear in all extractions (consensus)."""
        if len(extractions) == 1:
            return extractions[0]

        def get_names_set(entities: list) -> set:
            """Get lowercase names from entity list."""
            names = set()
            for e in entities:
                name = e.get("name", "").lower().strip()
                if name:
                    names.add(name)
            return names

        def filter_by_consensus(all_extractions: list[dict], entity_type: str) -> list:
            """Keep only entities whose names appear in ALL extractions."""
            # Get name sets from each extraction
            name_sets = [get_names_set(ext.get(entity_type, [])) for ext in all_extractions]

            # Find intersection (names in ALL extractions)
            if not name_sets:
                return []
            consensus_names = name_sets[0]
            for ns in name_sets[1:]:
                consensus_names = consensus_names.intersection(ns)

            # Return entities from first extraction that are in consensus
            result = []
            seen = set()
            for ext in all_extractions:
                for entity in ext.get(entity_type, []):
                    name = entity.get("name", "").lower().strip()
                    if name in consensus_names and name not in seen:
                        seen.add(name)
                        result.append(entity)

            return result

        return {
            "characters": filter_by_consensus(extractions, "characters"),
            "locations": filter_by_consensus(extractions, "locations"),
            "props": filter_by_consensus(extractions, "props"),
        }

    def _dedupe_entities(self, entities: dict) -> dict:
        """Simple deduplication by name (case-insensitive)."""
        def dedupe_list(items: list) -> list:
            seen = {}
            result = []
            for item in items:
                name = item.get("name", "")
                if not name:
                    continue
                name_lower = name.lower().strip()
                if name_lower not in seen:
                    seen[name_lower] = item
                    item["mentions"] = 1
                    result.append(item)
                else:
                    seen[name_lower]["mentions"] = seen[name_lower].get("mentions", 1) + 1
            return result

        return {
            "characters": dedupe_list(entities.get("characters", [])),
            "locations": dedupe_list(entities.get("locations", [])),
            "props": dedupe_list(entities.get("props", [])),
        }

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


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def ingest_pitch(project_path: Path, pitch: str) -> dict:
    """Quick helper for pitch ingestion."""
    pipeline = IngestionPipeline(project_path)
    return await pipeline.ingest_files([], pitch=pitch)
