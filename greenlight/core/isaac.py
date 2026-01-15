"""
Isaac 0.1 Vision Client for Project Greenlight.

Uses Isaac 0.1 via Replicate API for image analysis.
Isaac 0.1 is a vision model optimized for detailed scene description
and entity extraction from images.

TRACE: INGEST-001
"""

import asyncio
import base64
import logging
from pathlib import Path
from typing import Optional

import httpx

from .config import settings, ImageModels

logger = logging.getLogger(__name__)

# Isaac 0.1 on Replicate
# Model: perceptron-ai-inc/isaac-0.1
# 2B parameter open-weight VLM for grounded perception, OCR, spatial reasoning
ISAAC_MODEL = ImageModels.ISAAC_01
REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"


# =============================================================================
# SYSTEM PROMPTS FOR IMAGE ANALYSIS
# =============================================================================

IMAGE_ANALYSIS_SYSTEM = """You are an expert visual analyst for cinematic pre-production.
Analyze this image and extract ALL relevant details for storyboard creation.

Focus on:
1. CHARACTERS: Describe each person visible - their appearance, clothing, posture, expression, age, distinguishing features
2. SETTING: Describe the environment - location type, architecture, lighting, time of day, atmosphere
3. OBJECTS: Note significant props or items that could be story-relevant
4. MOOD: The emotional tone conveyed by the image
5. VISUAL STYLE: Art style, color palette, cinematography if applicable

Be detailed and specific. These descriptions will be used to:
- Extract entity names (characters, locations, props)
- Inform world-building decisions
- Generate consistent visual prompts later

Output a structured analysis."""


ENTITY_EXTRACTION_FROM_IMAGE_SYSTEM = """You are extracting story entities from an image analysis.

From the visual analysis provided, identify:
1. POTENTIAL CHARACTERS: People who could be named characters
2. POTENTIAL LOCATIONS: Settings that could be named locations
3. POTENTIAL PROPS: Significant objects that could be named props

For each entity, suggest a descriptive name based on what you see.
Do NOT invent names - use descriptive placeholders like:
- "Young Woman in Red Dress" (character)
- "Traditional Courtyard" (location)
- "Ornate Sword" (prop)

Output JSON:
{
    "characters": [
        {"suggested_name": "...", "visual_description": "...", "role_hint": "protagonist/supporting/background"}
    ],
    "locations": [
        {"suggested_name": "...", "visual_description": "..."}
    ],
    "props": [
        {"suggested_name": "...", "visual_description": "...", "significance": "plot/aesthetic/background"}
    ],
    "world_hints": {
        "time_period": "...",
        "culture": "...",
        "mood": "...",
        "visual_style": "..."
    }
}"""


# =============================================================================
# ISAAC CLIENT
# =============================================================================

class IsaacClient:
    """
    Client for Isaac 0.1 vision model via Replicate.

    Usage:
        client = IsaacClient()
        analysis = await client.analyze_image("/path/to/image.png")
        entities = await client.extract_entities_from_image("/path/to/image.png")
    """

    def __init__(self, max_retries: int = 3, timeout: float = 120.0):
        self.max_retries = max_retries
        self.timeout = timeout
        self._validate_api_key()

    def _validate_api_key(self):
        """Ensure Replicate API token is configured."""
        if not settings.replicate_api_token:
            logger.warning("REPLICATE_API_TOKEN not configured - Isaac calls will fail")

    def _encode_image(self, image_path: Path) -> str:
        """Encode image to base64 data URI."""
        path = Path(image_path)

        # Determine MIME type
        suffix = path.suffix.lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime_type = mime_types.get(suffix, "image/png")

        # Read and encode
        with open(path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        return f"data:{mime_type};base64,{image_data}"

    async def _create_prediction(
        self,
        image_data_uri: str,
        prompt: str,
        max_tokens: int = 2048,
    ) -> Optional[str]:
        """Create a prediction via Replicate API and poll for result."""
        if not settings.replicate_api_token:
            raise ValueError("REPLICATE_API_TOKEN not configured")

        headers = {
            "Authorization": f"Bearer {settings.replicate_api_token}",
            "Content-Type": "application/json",
        }

        # Create prediction
        payload = {
            "version": "latest",  # Use latest version
            "input": {
                "image": image_data_uri,
                "prompt": prompt,
                "max_new_tokens": max_tokens,
            }
        }

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    # Start prediction
                    response = await client.post(
                        f"https://api.replicate.com/v1/models/{ISAAC_MODEL}/predictions",
                        headers=headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    prediction = response.json()

                    prediction_id = prediction.get("id")
                    if not prediction_id:
                        raise ValueError("No prediction ID returned")

                    # Poll for completion
                    get_url = prediction.get("urls", {}).get("get") or f"{REPLICATE_API_URL}/{prediction_id}"

                    while True:
                        await asyncio.sleep(1)  # Poll interval

                        status_response = await client.get(get_url, headers=headers)
                        status_response.raise_for_status()
                        status_data = status_response.json()

                        status = status_data.get("status")

                        if status == "succeeded":
                            output = status_data.get("output")
                            # Output can be string or list of strings
                            if isinstance(output, list):
                                return "".join(output)
                            return output

                        elif status == "failed":
                            error = status_data.get("error", "Unknown error")
                            raise RuntimeError(f"Prediction failed: {error}")

                        elif status == "canceled":
                            raise RuntimeError("Prediction was canceled")

                        # Still processing - continue polling

            except httpx.HTTPStatusError as e:
                logger.warning(f"Replicate API error (attempt {attempt + 1}): {e.response.status_code}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

            except Exception as e:
                logger.warning(f"Isaac error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

        raise RuntimeError("All Isaac attempts failed")

    async def analyze_image(
        self,
        image_path: str | Path,
        custom_prompt: Optional[str] = None,
    ) -> str:
        """
        Analyze an image and return detailed description.

        Args:
            image_path: Path to the image file
            custom_prompt: Optional custom analysis prompt

        Returns:
            Detailed analysis of the image
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        image_data = self._encode_image(path)
        prompt = custom_prompt or IMAGE_ANALYSIS_SYSTEM

        logger.info(f"Analyzing image: {path.name}")
        return await self._create_prediction(image_data, prompt)

    async def extract_entities_from_image(
        self,
        image_path: str | Path,
    ) -> dict:
        """
        Extract potential entities from an image.

        Args:
            image_path: Path to the image file

        Returns:
            Dict with characters, locations, props, and world_hints
        """
        import json

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # First, get detailed analysis
        image_data = self._encode_image(path)

        # Combined prompt for entity extraction
        prompt = f"""{IMAGE_ANALYSIS_SYSTEM}

After your analysis, {ENTITY_EXTRACTION_FROM_IMAGE_SYSTEM}

Provide BOTH the detailed analysis AND the JSON output."""

        logger.info(f"Extracting entities from image: {path.name}")
        response = await self._create_prediction(image_data, prompt, max_tokens=4096)

        # Try to extract JSON from response
        result = {
            "raw_analysis": response,
            "characters": [],
            "locations": [],
            "props": [],
            "world_hints": {},
        }

        # Find JSON in response
        if response:
            try:
                # Try to find JSON block
                if "```json" in response:
                    start = response.find("```json") + 7
                    end = response.find("```", start)
                    if end > start:
                        json_str = response[start:end].strip()
                        parsed = json.loads(json_str)
                        result.update(parsed)
                else:
                    # Try to find raw JSON object
                    start = response.find("{")
                    end = response.rfind("}") + 1
                    if start >= 0 and end > start:
                        json_str = response[start:end]
                        parsed = json.loads(json_str)
                        result.update(parsed)
            except json.JSONDecodeError:
                logger.warning("Could not parse JSON from Isaac response")

        return result

    async def analyze_batch(
        self,
        image_paths: list[str | Path],
        custom_prompt: Optional[str] = None,
    ) -> list[str]:
        """
        Analyze multiple images in parallel.

        Args:
            image_paths: List of image paths
            custom_prompt: Optional custom analysis prompt

        Returns:
            List of analysis results (same order as input)
        """
        tasks = [
            self.analyze_image(path, custom_prompt)
            for path in image_paths
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def analyze_image(image_path: str | Path, custom_prompt: Optional[str] = None) -> str:
    """Quick helper for single image analysis."""
    client = IsaacClient()
    return await client.analyze_image(image_path, custom_prompt)


async def extract_entities_from_image(image_path: str | Path) -> dict:
    """Quick helper for entity extraction from image."""
    client = IsaacClient()
    return await client.extract_entities_from_image(image_path)
