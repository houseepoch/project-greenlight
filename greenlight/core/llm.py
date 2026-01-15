"""
LLM Client for Project Greenlight.

Uses Grok 4.1 Fast exclusively via xAI API.
Simple, fast, no fallbacks or routing complexity.
"""

import asyncio
import logging
from typing import Optional

import httpx

from .config import settings

logger = logging.getLogger(__name__)

# Grok 4.1 Fast - the only model we use
GROK_MODEL = "grok-4-1-fast"
GROK_API_URL = "https://api.x.ai/v1/chat/completions"


class LLMClient:
    """
    Simple LLM client using Grok 4.1 Fast only.

    Usage:
        client = LLMClient()
        response = await client.generate("Write a story about...")
    """

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self._validate_api_key()

    def _validate_api_key(self):
        """Ensure xAI API key is configured."""
        if not settings.xai_api_key:
            logger.warning("XAI_API_KEY not configured - LLM calls will fail")

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate text using Grok 4.1 Fast.

        Args:
            prompt: The user prompt
            system_prompt: Optional system instructions
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)

        Returns:
            Generated text response
        """
        if not settings.xai_api_key:
            raise ValueError("XAI_API_KEY not configured")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        GROK_API_URL,
                        headers={
                            "Authorization": f"Bearer {settings.xai_api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": GROK_MODEL,
                            "messages": messages,
                            "max_tokens": max_tokens,
                            "temperature": temperature,
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data["choices"][0]["message"]["content"]

            except httpx.HTTPStatusError as e:
                logger.warning(f"Grok API error (attempt {attempt + 1}): {e.response.status_code}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

            except Exception as e:
                logger.warning(f"LLM error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

        raise RuntimeError("All LLM attempts failed")

    async def generate_batch(
        self,
        prompts: list[tuple[str, str]],  # List of (prompt, system_prompt) tuples
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> list[str]:
        """
        Generate multiple responses in parallel.

        Args:
            prompts: List of (prompt, system_prompt) tuples
            max_tokens: Maximum tokens per response
            temperature: Sampling temperature

        Returns:
            List of generated responses (same order as prompts)
        """
        tasks = [
            self.generate(prompt, system, max_tokens, temperature)
            for prompt, system in prompts
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)


# Convenience function for quick generation
async def generate(
    prompt: str,
    system_prompt: str = "",
    max_tokens: int = 4096,
) -> str:
    """Quick generation helper using Grok 4.1 Fast."""
    client = LLMClient()
    return await client.generate(prompt, system_prompt, max_tokens)


# Convenience function for parallel generation (used by consensus extraction)
async def generate_parallel(
    prompts: list[tuple[str, str]],
    max_tokens: int = 4096,
) -> list[str]:
    """Generate multiple responses in parallel."""
    client = LLMClient()
    return await client.generate_batch(prompts, max_tokens)
