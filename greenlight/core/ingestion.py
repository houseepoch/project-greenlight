"""
Document Ingestion Pipeline for Project Greenlight.

Handles multi-format document and image ingestion:
- Text files (.txt, .md)
- PDF documents (.pdf)
- Word documents (.docx)
- Images (.png, .jpg, .jpeg)
- Archives (.zip)

Flow:
1. File extraction (unzip if needed)
2. Document processing (text extraction, image analysis)
3. Chunking (500-1000 tokens with 10% overlap)
4. Entity extraction from chunks
5. Output: chunks.json, extracted_entities.json

TRACE: INGEST-001
"""

import asyncio
import io
import json
import logging
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Callable, Optional
from datetime import datetime

from .config import settings
from .llm import LLMClient, generate_parallel
from .isaac import IsaacClient

logger = logging.getLogger(__name__)


# =============================================================================
# SYSTEM PROMPTS FOR ENTITY EXTRACTION
# =============================================================================

CHUNK_ENTITY_EXTRACTION_SYSTEM = """You are an entity extraction specialist for cinematic pre-production.

Extract NAMED ENTITIES from the provided text chunk. Focus on:

1. CHARACTERS: Named people, described individuals who could be characters
   - Include protagonists, antagonists, supporting characters
   - Note their role if apparent (protagonist, love interest, mentor, etc.)

2. LOCATIONS: Named places, described settings
   - Include specific rooms, buildings, cities, landscapes
   - Note if interior/exterior when apparent

3. PROPS: Significant named objects
   - Only include items with story significance
   - Skip generic items unless specifically described

CRITICAL RULES:
- Only extract entities that are EXPLICITLY mentioned or clearly described
- Do NOT invent or hallucinate entities
- Use the exact names as written in the text
- For unnamed entities, use descriptive names (e.g., "The Old Man", "Palace Courtyard")

Output JSON:
{
    "characters": [
        {"name": "Character Name", "role_hint": "protagonist/antagonist/supporting/mentioned", "context": "brief quote or context"}
    ],
    "locations": [
        {"name": "Location Name", "type_hint": "interior/exterior/both", "context": "brief quote or context"}
    ],
    "props": [
        {"name": "Prop Name", "significance": "plot/character/setting", "context": "brief quote or context"}
    ]
}

If no entities of a type are found, return an empty array for that type."""


ENTITY_DEDUPLICATION_SYSTEM = """You are merging entity lists from multiple text chunks.

Given multiple entity lists, your job is to:
1. MERGE entities that refer to the same thing (different names, same entity)
2. DEDUPLICATE exact duplicates
3. CONSOLIDATE context from multiple mentions
4. ASSIGN confidence based on mention count

Rules:
- "Mei" and "Mei Ling" might be the same person - merge if context supports it
- "The palace" and "Imperial Palace" might be the same - merge if logical
- Keep the most descriptive/complete name as the primary name
- Preserve all unique context snippets

Output JSON:
{
    "characters": [
        {"name": "Primary Name", "aliases": ["other names"], "role_hint": "...", "mentions": 3, "contexts": ["ctx1", "ctx2"]}
    ],
    "locations": [
        {"name": "Primary Name", "aliases": ["other names"], "type_hint": "...", "mentions": 2, "contexts": ["ctx1"]}
    ],
    "props": [
        {"name": "Primary Name", "aliases": ["other names"], "significance": "...", "mentions": 1, "contexts": ["ctx1"]}
    ]
}"""


IMAGE_CONTEXT_SYSTEM = """You are analyzing image descriptions for entity extraction.

From the image analysis provided, identify potential story entities:

1. CHARACTERS: People visible in the image
   - Describe their appearance, clothing, apparent role
   - Use descriptive names since we don't know actual names yet

2. LOCATIONS: The setting shown in the image
   - Describe architecture, environment, atmosphere
   - Note time period and cultural context if apparent

3. PROPS: Significant objects visible
   - Focus on items that could be story-relevant
   - Note their apparent significance

Also extract WORLD HINTS:
- Time period suggested by visuals
- Cultural context
- Visual style/mood
- Color palette

Output JSON:
{
    "characters": [{"descriptive_name": "...", "appearance": "...", "role_hint": "..."}],
    "locations": [{"descriptive_name": "...", "description": "...", "type_hint": "..."}],
    "props": [{"descriptive_name": "...", "description": "...", "significance": "..."}],
    "world_hints": {
        "time_period": "...",
        "cultural_context": "...",
        "visual_style": "...",
        "mood": "...",
        "color_palette": "..."
    }
}"""


# =============================================================================
# CHUNKING UTILITIES
# =============================================================================

def estimate_tokens(text: str) -> int:
    """Estimate token count (rough approximation: ~4 chars per token)."""
    return len(text) // 4


def chunk_text(
    text: str,
    min_tokens: int = 500,
    max_tokens: int = 1000,
    overlap_ratio: float = 0.1,
) -> list[dict]:
    """
    Chunk text into segments of 500-1000 tokens with 10% overlap.

    Args:
        text: The text to chunk
        min_tokens: Minimum tokens per chunk
        max_tokens: Maximum tokens per chunk
        overlap_ratio: Overlap between chunks (0.1 = 10%)

    Returns:
        List of chunk dicts with text, start_char, end_char, token_estimate
    """
    if not text.strip():
        return []

    # Split into paragraphs first
    paragraphs = re.split(r'\n\s*\n', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks = []
    current_chunk = []
    current_tokens = 0
    chunk_start = 0
    char_pos = 0

    for para in paragraphs:
        para_tokens = estimate_tokens(para)

        # If single paragraph exceeds max, we need to split it
        if para_tokens > max_tokens:
            # Finish current chunk if not empty
            if current_chunk:
                chunk_text_content = "\n\n".join(current_chunk)
                chunks.append({
                    "text": chunk_text_content,
                    "start_char": chunk_start,
                    "end_char": char_pos,
                    "token_estimate": current_tokens,
                })
                # Calculate overlap start
                overlap_tokens = int(current_tokens * overlap_ratio)
                overlap_chars = overlap_tokens * 4
                chunk_start = max(chunk_start, char_pos - overlap_chars)
                current_chunk = []
                current_tokens = 0

            # Split large paragraph by sentences
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sentence in sentences:
                sent_tokens = estimate_tokens(sentence)
                if current_tokens + sent_tokens > max_tokens and current_tokens >= min_tokens:
                    # Save chunk
                    chunk_text_content = " ".join(current_chunk)
                    chunks.append({
                        "text": chunk_text_content,
                        "start_char": chunk_start,
                        "end_char": char_pos,
                        "token_estimate": current_tokens,
                    })
                    # Overlap
                    overlap_tokens = int(current_tokens * overlap_ratio)
                    overlap_chars = overlap_tokens * 4
                    chunk_start = max(chunk_start, char_pos - overlap_chars)
                    current_chunk = []
                    current_tokens = 0

                current_chunk.append(sentence)
                current_tokens += sent_tokens
                char_pos += len(sentence) + 1

        else:
            # Check if adding this paragraph exceeds max
            if current_tokens + para_tokens > max_tokens and current_tokens >= min_tokens:
                # Save current chunk
                chunk_text_content = "\n\n".join(current_chunk)
                chunks.append({
                    "text": chunk_text_content,
                    "start_char": chunk_start,
                    "end_char": char_pos,
                    "token_estimate": current_tokens,
                })
                # Calculate overlap - keep last ~10% of tokens
                overlap_tokens = int(current_tokens * overlap_ratio)
                overlap_chars = overlap_tokens * 4
                chunk_start = max(chunk_start, char_pos - overlap_chars)
                current_chunk = []
                current_tokens = 0

            current_chunk.append(para)
            current_tokens += para_tokens
            char_pos += len(para) + 2  # +2 for paragraph separator

    # Don't forget the last chunk
    if current_chunk:
        chunk_text_content = "\n\n".join(current_chunk)
        chunks.append({
            "text": chunk_text_content,
            "start_char": chunk_start,
            "end_char": char_pos,
            "token_estimate": current_tokens,
        })

    # Number the chunks
    for i, chunk in enumerate(chunks):
        chunk["chunk_id"] = i + 1
        chunk["total_chunks"] = len(chunks)

    return chunks


# =============================================================================
# FILE PROCESSORS
# =============================================================================

async def process_text_file(file_path: Path) -> dict:
    """Process a plain text or markdown file."""
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    return {
        "type": "text",
        "filename": file_path.name,
        "content": content,
        "char_count": len(content),
        "token_estimate": estimate_tokens(content),
    }


async def process_pdf_file(file_path: Path) -> dict:
    """Process a PDF file using pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError:
        logger.error("pypdf not installed. Install with: pip install pypdf")
        return {
            "type": "pdf",
            "filename": file_path.name,
            "content": "",
            "error": "pypdf not installed",
        }

    try:
        reader = PdfReader(file_path)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

        content = "\n\n".join(text_parts)
        return {
            "type": "pdf",
            "filename": file_path.name,
            "content": content,
            "page_count": len(reader.pages),
            "char_count": len(content),
            "token_estimate": estimate_tokens(content),
        }
    except Exception as e:
        logger.error(f"PDF processing error: {e}")
        return {
            "type": "pdf",
            "filename": file_path.name,
            "content": "",
            "error": str(e),
        }


async def process_docx_file(file_path: Path) -> dict:
    """Process a Word document using python-docx."""
    try:
        from docx import Document
    except ImportError:
        logger.error("python-docx not installed. Install with: pip install python-docx")
        return {
            "type": "docx",
            "filename": file_path.name,
            "content": "",
            "error": "python-docx not installed",
        }

    try:
        doc = Document(file_path)
        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)

        content = "\n\n".join(text_parts)
        return {
            "type": "docx",
            "filename": file_path.name,
            "content": content,
            "paragraph_count": len(text_parts),
            "char_count": len(content),
            "token_estimate": estimate_tokens(content),
        }
    except Exception as e:
        logger.error(f"DOCX processing error: {e}")
        return {
            "type": "docx",
            "filename": file_path.name,
            "content": "",
            "error": str(e),
        }


async def process_image_file(file_path: Path) -> dict:
    """Process an image file using Isaac 0.1."""
    try:
        isaac = IsaacClient()
        result = await isaac.extract_entities_from_image(file_path)

        return {
            "type": "image",
            "filename": file_path.name,
            "analysis": result.get("raw_analysis", ""),
            "extracted_entities": {
                "characters": result.get("characters", []),
                "locations": result.get("locations", []),
                "props": result.get("props", []),
            },
            "world_hints": result.get("world_hints", {}),
        }
    except Exception as e:
        logger.error(f"Image processing error: {e}")
        return {
            "type": "image",
            "filename": file_path.name,
            "analysis": "",
            "error": str(e),
        }


async def extract_zip_file(zip_path: Path, extract_to: Path) -> list[Path]:
    """Extract a zip file and return list of extracted files."""
    extracted_files = []

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for member in zf.namelist():
                # Skip directories and hidden files
                if member.endswith('/') or member.startswith('__MACOSX'):
                    continue

                # Extract
                extracted_path = extract_to / member
                extracted_path.parent.mkdir(parents=True, exist_ok=True)
                zf.extract(member, extract_to)
                extracted_files.append(extracted_path)

    except Exception as e:
        logger.error(f"ZIP extraction error: {e}")

    return extracted_files


# =============================================================================
# INGESTION PIPELINE
# =============================================================================

class IngestionPipeline:
    """
    Document Ingestion Pipeline.

    Processes documents and images, extracts text, chunks content,
    and identifies potential entities for user confirmation.

    Outputs:
    - chunks.json: Processed text chunks
    - extracted_entities.json: Pre-confirmation entity list
    """

    SUPPORTED_TEXT = {".txt", ".md"}
    SUPPORTED_PDF = {".pdf"}
    SUPPORTED_DOCX = {".docx"}
    SUPPORTED_IMAGE = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    SUPPORTED_ARCHIVE = {".zip"}

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
        Ingest multiple files and/or pitch text and extract entities.

        Args:
            file_paths: List of file paths to process
            pitch: Optional pitch/synopsis text to include in entity extraction

        Returns:
            Dict with chunks, entities, and processing results
        """
        has_files = len(file_paths) > 0
        has_pitch = pitch and pitch.strip()

        if has_files:
            self._log(f"Starting ingestion of {len(file_paths)} files")
        if has_pitch:
            self._log("Including pitch/synopsis in entity extraction")
        self._progress(0.05)

        # Categorize files
        text_files = []
        pdf_files = []
        docx_files = []
        image_files = []
        zip_files = []
        unsupported = []

        for path in file_paths:
            suffix = path.suffix.lower()
            if suffix in self.SUPPORTED_TEXT:
                text_files.append(path)
            elif suffix in self.SUPPORTED_PDF:
                pdf_files.append(path)
            elif suffix in self.SUPPORTED_DOCX:
                docx_files.append(path)
            elif suffix in self.SUPPORTED_IMAGE:
                image_files.append(path)
            elif suffix in self.SUPPORTED_ARCHIVE:
                zip_files.append(path)
            else:
                unsupported.append(path)

        self._log(f"Files: {len(text_files)} text, {len(pdf_files)} PDF, "
                  f"{len(docx_files)} DOCX, {len(image_files)} images, "
                  f"{len(zip_files)} archives")

        # Extract zip files first
        if zip_files:
            self._log("Extracting archives...")
            extract_dir = self.project_path / "uploads" / "extracted"
            extract_dir.mkdir(parents=True, exist_ok=True)

            for zip_path in zip_files:
                extracted = await extract_zip_file(zip_path, extract_dir)
                for ext_path in extracted:
                    suffix = ext_path.suffix.lower()
                    if suffix in self.SUPPORTED_TEXT:
                        text_files.append(ext_path)
                    elif suffix in self.SUPPORTED_PDF:
                        pdf_files.append(ext_path)
                    elif suffix in self.SUPPORTED_DOCX:
                        docx_files.append(ext_path)
                    elif suffix in self.SUPPORTED_IMAGE:
                        image_files.append(ext_path)

        self._progress(0.15)

        # Process all files
        processed_docs = []
        processed_images = []

        # Process text files
        for path in text_files:
            try:
                result = await process_text_file(path)
                processed_docs.append(result)
                self._log(f"  [OK] {path.name} ({result.get('token_estimate', 0)} tokens)")
            except Exception as e:
                self._log(f"  [FAIL] {path.name}: {e}")

        # Process PDFs
        for path in pdf_files:
            try:
                result = await process_pdf_file(path)
                if result.get("content"):
                    processed_docs.append(result)
                    self._log(f"  [OK] {path.name} ({result.get('page_count', 0)} pages)")
                else:
                    self._log(f"  [FAIL] {path.name}: {result.get('error', 'No content')}")
            except Exception as e:
                self._log(f"  [FAIL] {path.name}: {e}")

        # Process DOCX files
        for path in docx_files:
            try:
                result = await process_docx_file(path)
                if result.get("content"):
                    processed_docs.append(result)
                    self._log(f"  [OK] {path.name} ({result.get('paragraph_count', 0)} paragraphs)")
                else:
                    self._log(f"  [FAIL] {path.name}: {result.get('error', 'No content')}")
            except Exception as e:
                self._log(f"  [FAIL] {path.name}: {e}")

        self._progress(0.35)

        # Process images (in parallel)
        if image_files:
            self._log(f"Analyzing {len(image_files)} images with Isaac 0.1...")
            image_tasks = [process_image_file(path) for path in image_files]
            image_results = await asyncio.gather(*image_tasks, return_exceptions=True)

            for i, result in enumerate(image_results):
                if isinstance(result, Exception):
                    self._log(f"  [FAIL] {image_files[i].name}: {result}")
                elif result.get("error"):
                    self._log(f"  [FAIL] {result.get('filename')}: {result.get('error')}")
                else:
                    processed_images.append(result)
                    self._log(f"  [OK] {result.get('filename')} analyzed")

        self._progress(0.50)

        # Combine all text content
        text_parts = []

        # Add pitch first if provided (highest priority content)
        if has_pitch:
            text_parts.append(f"=== STORY PITCH/SYNOPSIS ===\n{pitch.strip()}")

        # Add document content
        for doc in processed_docs:
            if doc.get("content"):
                text_parts.append(doc.get("content"))

        all_text = "\n\n---\n\n".join(text_parts)

        # Handle case with no text content
        if not all_text.strip():
            self._log("No text content to process")
            chunks = []
        else:
            # Chunk the combined text
            self._log("Chunking text content...")
            chunks = chunk_text(all_text, min_tokens=500, max_tokens=1000, overlap_ratio=0.1)
            self._log(f"Created {len(chunks)} chunks")

        self._progress(0.60)

        # Extract entities from chunks
        self._log("Extracting entities from chunks...")
        chunk_entities = await self._extract_entities_from_chunks(chunks)

        # Extract entities from images
        image_entities = self._collect_image_entities(processed_images)

        self._progress(0.80)

        # Merge and deduplicate entities
        self._log("Merging and deduplicating entities...")
        merged_entities = await self._merge_entities(chunk_entities, image_entities)

        self._progress(0.90)

        # Save outputs
        self._log("Saving outputs...")
        output_dir = self.project_path / "ingestion"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save chunks
        chunks_path = output_dir / "chunks.json"
        chunks_path.write_text(
            json.dumps({
                "created_at": datetime.now().isoformat(),
                "total_chunks": len(chunks),
                "has_pitch": has_pitch,
                "source_files": [d.get("filename") for d in processed_docs],
                "chunks": chunks,
            }, indent=2),
            encoding="utf-8"
        )

        # Save extracted entities (pre-confirmation)
        entities_path = output_dir / "extracted_entities.json"
        entities_path.write_text(
            json.dumps({
                "created_at": datetime.now().isoformat(),
                "status": "pending_confirmation",
                "has_pitch": has_pitch,
                "source_files": {
                    "documents": [d.get("filename") for d in processed_docs],
                    "images": [i.get("filename") for i in processed_images],
                },
                "entities": merged_entities,
                "world_hints": self._collect_world_hints(processed_images),
            }, indent=2),
            encoding="utf-8"
        )

        self._progress(1.0)
        self._log("Ingestion complete!")

        return {
            "success": True,
            "chunks_path": str(chunks_path),
            "entities_path": str(entities_path),
            "stats": {
                "documents_processed": len(processed_docs),
                "images_processed": len(processed_images),
                "total_chunks": len(chunks),
                "characters_found": len(merged_entities.get("characters", [])),
                "locations_found": len(merged_entities.get("locations", [])),
                "props_found": len(merged_entities.get("props", [])),
            }
        }

    async def _extract_entities_from_chunks(self, chunks: list[dict]) -> dict:
        """Extract entities from all chunks using LLM."""
        if not chunks:
            return {"characters": [], "locations": [], "props": []}

        # Build prompts for each chunk
        prompts = []
        for chunk in chunks:
            prompt = f"""Extract entities from this text chunk:

CHUNK {chunk['chunk_id']}/{chunk['total_chunks']}:
---
{chunk['text']}
---

Output only valid JSON."""

            prompts.append((prompt, CHUNK_ENTITY_EXTRACTION_SYSTEM))

        # Process in batches of 5 to avoid rate limits
        batch_size = 5
        all_entities = {"characters": [], "locations": [], "props": []}

        for i in range(0, len(prompts), batch_size):
            batch = prompts[i:i+batch_size]
            self._log(f"  Processing chunks {i+1}-{min(i+batch_size, len(prompts))}...")

            results = await generate_parallel(batch, max_tokens=1024)

            for result in results:
                if isinstance(result, Exception):
                    continue

                try:
                    data = self._extract_json(result)
                    if data:
                        all_entities["characters"].extend(data.get("characters", []))
                        all_entities["locations"].extend(data.get("locations", []))
                        all_entities["props"].extend(data.get("props", []))
                except Exception as e:
                    logger.warning(f"Failed to parse chunk entities: {e}")

        return all_entities

    def _collect_image_entities(self, processed_images: list[dict]) -> dict:
        """Collect entities from processed images."""
        entities = {"characters": [], "locations": [], "props": []}

        for img in processed_images:
            extracted = img.get("extracted_entities", {})
            entities["characters"].extend(extracted.get("characters", []))
            entities["locations"].extend(extracted.get("locations", []))
            entities["props"].extend(extracted.get("props", []))

        return entities

    def _collect_world_hints(self, processed_images: list[dict]) -> dict:
        """Collect world hints from processed images."""
        hints = {
            "time_periods": [],
            "cultural_contexts": [],
            "visual_styles": [],
            "moods": [],
            "color_palettes": [],
        }

        for img in processed_images:
            wh = img.get("world_hints", {})
            if wh.get("time_period"):
                hints["time_periods"].append(wh["time_period"])
            if wh.get("cultural_context"):
                hints["cultural_contexts"].append(wh["cultural_context"])
            if wh.get("visual_style"):
                hints["visual_styles"].append(wh["visual_style"])
            if wh.get("mood"):
                hints["moods"].append(wh["mood"])
            if wh.get("color_palette"):
                hints["color_palettes"].append(wh["color_palette"])

        return hints

    async def _merge_entities(
        self,
        chunk_entities: dict,
        image_entities: dict,
    ) -> dict:
        """Merge and deduplicate entities from all sources."""
        # Combine all entities
        all_chars = chunk_entities.get("characters", []) + image_entities.get("characters", [])
        all_locs = chunk_entities.get("locations", []) + image_entities.get("locations", [])
        all_props = chunk_entities.get("props", []) + image_entities.get("props", [])

        # Simple deduplication by name (case-insensitive)
        def dedupe_by_name(entities: list, name_key: str = "name") -> list:
            seen = {}
            result = []
            for entity in entities:
                name = entity.get(name_key, entity.get("descriptive_name", entity.get("suggested_name", "")))
                if not name:
                    continue
                name_lower = name.lower().strip()
                if name_lower not in seen:
                    seen[name_lower] = entity
                    entity["mentions"] = 1
                    result.append(entity)
                else:
                    seen[name_lower]["mentions"] = seen[name_lower].get("mentions", 1) + 1
                    # Merge contexts
                    existing_ctx = seen[name_lower].get("contexts", [])
                    new_ctx = entity.get("context", entity.get("contexts", []))
                    if isinstance(new_ctx, str):
                        new_ctx = [new_ctx]
                    seen[name_lower]["contexts"] = list(set(existing_ctx + new_ctx))

            # Sort by mentions (most mentioned first)
            return sorted(result, key=lambda x: x.get("mentions", 1), reverse=True)

        return {
            "characters": dedupe_by_name(all_chars),
            "locations": dedupe_by_name(all_locs),
            "props": dedupe_by_name(all_props),
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

async def ingest_project_files(project_path: Path, file_paths: list[Path]) -> dict:
    """Quick helper for project file ingestion."""
    pipeline = IngestionPipeline(project_path)
    return await pipeline.ingest_files(file_paths)
