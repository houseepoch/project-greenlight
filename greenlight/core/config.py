"""
Configuration management for Project Greenlight.

Simple, flat configuration - no complex nesting or multiple config files.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache


# =============================================================================
# MODEL IDENTIFIERS (Updated 2026-01-14)
# =============================================================================

# LLM Models
class LLMModels:
    """Available LLM model identifiers."""
    # xAI Grok
    GROK_4_1_FAST = "grok-4-1-fast"  # Alias for grok-4-1-fast-reasoning
    GROK_4_1_FAST_REASONING = "grok-4-1-fast-reasoning"  # 2M context, agentic
    GROK_4_1_FAST_NON_REASONING = "grok-4-1-fast-non-reasoning"  # Fast, no CoT
    GROK_4 = "grok-4"  # Base Grok 4

    # Google Gemini
    GEMINI_3_PRO = "gemini-3-pro"

    # Anthropic Claude
    CLAUDE_HAIKU = "claude-haiku-4.5"
    CLAUDE_SONNET = "claude-sonnet-4"
    CLAUDE_OPUS = "claude-opus-4.5"


# Image Models (Replicate)
class ImageModels:
    """Available image model identifiers on Replicate."""
    # Vision/Analysis
    ISAAC_01 = "perceptron-ai-inc/isaac-0.1"  # 2B VLM, grounded perception

    # Text-to-Image Generation
    SEEDREAM_45 = "bytedance/seedream-4.5"  # Cinematic, portraits, fast
    FLUX_2_PRO = "black-forest-labs/flux-2-pro"  # 4MP, high-fidelity
    FLUX_2_DEV = "black-forest-labs/flux-2-dev"  # Development version

    # Google Gemini Image
    GEMINI_IMAGE = "gemini-3-pro-image-preview"  # Nano Banana Pro, 4K


# Model aliases for user-friendly names
MODEL_ALIASES = {
    # LLM aliases
    "grok": LLMModels.GROK_4_1_FAST,
    "grok-fast": LLMModels.GROK_4_1_FAST,
    "gemini": LLMModels.GEMINI_3_PRO,
    "claude": LLMModels.CLAUDE_SONNET,
    "claude-haiku": LLMModels.CLAUDE_HAIKU,
    "claude-opus": LLMModels.CLAUDE_OPUS,

    # Image aliases
    "isaac": ImageModels.ISAAC_01,
    "seedream": ImageModels.SEEDREAM_45,
    "flux": ImageModels.FLUX_2_PRO,
    "flux-pro": ImageModels.FLUX_2_PRO,
    "flux-dev": ImageModels.FLUX_2_DEV,
    "gemini-image": ImageModels.GEMINI_IMAGE,
    "nano-banana": ImageModels.GEMINI_IMAGE,
}


def resolve_model(alias: str) -> str:
    """Resolve a model alias to its full identifier."""
    return MODEL_ALIASES.get(alias.lower(), alias)


# =============================================================================
# SETTINGS
# =============================================================================

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    xai_api_key: str = Field(default="", alias="XAI_API_KEY")
    together_api_key: str = Field(default="", alias="TOGETHER_API_KEY")
    replicate_api_token: str = Field(default="", alias="REPLICATE_API_TOKEN")

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Default LLM settings
    default_llm: str = "grok-4-1-fast"  # Primary: Grok 4.1 Fast
    default_image_model: str = "flux_2_pro"  # Primary: FLUX 2 Pro (high quality)

    # Paths
    projects_dir: Path = Field(default_factory=lambda: Path.home() / "greenlight_projects")

    # Rate limiting
    rate_limit_per_minute: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider."""
        key_map = {
            "anthropic": self.anthropic_api_key,
            "gemini": self.gemini_api_key,
            "xai": self.xai_api_key,
            "together": self.together_api_key,
            "replicate": self.replicate_api_token,
        }
        return key_map.get(provider.lower())

    def validate_keys(self) -> dict[str, bool]:
        """Check which API keys are configured."""
        return {
            "anthropic": bool(self.anthropic_api_key),
            "gemini": bool(self.gemini_api_key),
            "xai": bool(self.xai_api_key),
            "together": bool(self.together_api_key),
            "replicate": bool(self.replicate_api_token),
        }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
