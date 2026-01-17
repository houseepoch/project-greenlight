"""
Simplified Image Generation for Project Greenlight.

Supports:
- Replicate: Seedream, FLUX 2 Pro, P-Image-Edit, FLUX 1.1 Pro
- Google: Gemini Flash Image (Nano Banana), Gemini Pro Image
- Stability: SD 3.5, SDXL

No complex context engines or singleton patterns - just direct API calls.
"""

import asyncio
import base64
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Any

from .config import settings

logger = logging.getLogger(__name__)


class ImageModel(str, Enum):
    """Available image generation models."""
    # Replicate
    SEEDREAM = "seedream"  # ByteDance Seedream 4.5 - Cheap, fast, quality
    FLUX_2_PRO = "flux_2_pro"  # FLUX 2 Pro - High quality, 8 ref images
    P_IMAGE_EDIT = "p_image_edit"  # P-Image-Edit - Fast editing
    FLUX_1_1_PRO = "flux_1_1_pro"  # FLUX 1.1 Pro - Flagship
    Z_IMAGE_TURBO = "z_image_turbo"  # Pruna AI Z-Image-Turbo - Fast, quality

    # Google/Gemini
    NANO_BANANA = "nano_banana"  # Gemini Flash Image
    NANO_BANANA_PRO = "nano_banana_pro"  # Gemini Pro Image

    # Stability
    SD_3_5 = "sd_3_5"
    SDXL = "sdxl"


# Model to provider mapping
MODEL_PROVIDERS = {
    ImageModel.SEEDREAM: "replicate",
    ImageModel.FLUX_2_PRO: "replicate",
    ImageModel.P_IMAGE_EDIT: "replicate",
    ImageModel.FLUX_1_1_PRO: "replicate",
    ImageModel.Z_IMAGE_TURBO: "replicate",
    ImageModel.NANO_BANANA: "gemini",
    ImageModel.NANO_BANANA_PRO: "gemini",
    ImageModel.SD_3_5: "stability",
    ImageModel.SDXL: "replicate",
}

# Replicate model identifiers
REPLICATE_MODELS = {
    ImageModel.SEEDREAM: "bytedance/seedream-4.5",  # Seedream 4.5 - supports up to 14 reference images
    ImageModel.FLUX_2_PRO: "black-forest-labs/flux-2-pro",  # Flux 2 Pro - up to 8 reference images
    ImageModel.P_IMAGE_EDIT: "prunaai/p-image-edit",
    ImageModel.FLUX_1_1_PRO: "black-forest-labs/flux-1.1-pro",
    ImageModel.Z_IMAGE_TURBO: "prunaai/z-image-turbo",
    ImageModel.SDXL: "stability-ai/sdxl:latest",
}


# Prompt templates
PROMPT_TEMPLATE_CREATE = (
    "Create a new image inspired by the reference images, maintain subject identity "
    "and original structure while dynamically manipulating them to be immersed into "
    "the scene with each subject being imported into the scene by reference of their "
    "unique name or tag as their source of design TRUTH, create this image:"
)

PROMPT_TEMPLATE_EDIT = (
    "Edit image maintaining its qualities and subject identity while precisely "
    "making these changes:"
)

PROMPT_SUFFIX_CLEAN = (
    " --no labels, no tags, no subtitles, no dialogue, no multi-frame, no text overlays, "
    "no character name text, no CHAR_ text, no LOC_ text, no watermarks, single frame only"
)

# =============================================================================
# MEDIA TYPE STYLE REINFORCEMENT TEMPLATES
# These provide style-specific guidance without referencing artists
# =============================================================================

MEDIA_TYPE_STYLES = {
    "live_action": "Photorealistic cinematography, natural lighting, film grain texture, realistic proportions and anatomy, cinematic color grading, shallow depth of field, real-world physics",
    "anime": "Japanese animation style, expressive large eyes, dynamic line work, cel-shaded coloring, vibrant saturated colors, stylized proportions, dramatic poses, manga-inspired aesthetics",
    "animation_2d": "Traditional hand-drawn animation aesthetic, clean line art, fluid motion implied, painterly backgrounds, character design with appealing shapes, warm color palette, storybook quality",
    "animation_3d": "Modern 3D CGI rendering, smooth subsurface scattering on skin, stylized but grounded character design, ambient occlusion, global illumination, cinematic camera angles",
    "cartoon": "Stylized cartoon aesthetic, exaggerated features and expressions, bold outlines, flat colors with simple shading, playful proportions, squash and stretch implied, comedic timing",
    "claymation": "Stop-motion clay animation texture, visible fingerprint marks, tactile surface quality, slightly imperfect shapes, warm practical lighting, miniature set aesthetic, handcrafted feel",
    "mixed": "Hybrid visual style blending multiple mediums, creative compositing, artistic interpretation of reality, unique aesthetic fusion",
}


def get_media_style_prompt(visual_style: str) -> str:
    """Get the reinforcing style prompt for a media type."""
    return MEDIA_TYPE_STYLES.get(visual_style, MEDIA_TYPE_STYLES["live_action"])


@dataclass
class ImageRequest:
    """Image generation request."""
    prompt: str
    model: ImageModel = ImageModel.FLUX_2_PRO
    aspect_ratio: str = "16:9"
    reference_images: list[Path] = field(default_factory=list)
    output_path: Optional[Path] = None
    tag: Optional[str] = None  # For naming the output file
    prefix_type: str = "generate"  # "generate", "edit", "none"
    add_clean_suffix: bool = True
    negative_prompt: Optional[str] = None
    style_suffix: Optional[str] = None
    seed: Optional[int] = None  # Random seed for reproducibility/variation
    # Image editing specific
    source_image: Optional[Path] = None  # Image to edit (for inpainting/editing)
    edit_instruction: Optional[str] = None  # Specific edit instruction
    resolution: str = "2K"  # For Nano Banana Pro: "1K", "2K", "4K"


@dataclass
class ImageResult:
    """Image generation result."""
    success: bool
    image_path: Optional[Path] = None
    image_data: Optional[bytes] = None
    model_used: str = ""
    error: Optional[str] = None
    generation_time_ms: int = 0


class ImageGenerator:
    """
    Simple image generator supporting multiple providers.

    Usage:
        generator = ImageGenerator()
        result = await generator.generate(ImageRequest(
            prompt="A cinematic shot of...",
            model=ImageModel.SEEDREAM
        ))
    """

    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = Path(project_path) if project_path else None
        self._replicate_client = None

    async def generate(self, request: ImageRequest) -> ImageResult:
        """Generate an image based on the request."""
        start_time = datetime.now()

        # Build the full prompt
        prompt = self._build_prompt(request)

        provider = MODEL_PROVIDERS.get(request.model, "replicate")

        try:
            if provider == "replicate":
                result = await self._generate_replicate(request, prompt)
            elif provider == "gemini":
                result = await self._generate_gemini(request, prompt)
            elif provider == "stability":
                result = await self._generate_stability(request, prompt)
            else:
                return ImageResult(success=False, error=f"Unknown provider: {provider}")

            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            result.generation_time_ms = int(elapsed)
            result.model_used = request.model.value

            return result

        except Exception as e:
            logger.exception(f"Image generation failed: {e}")
            return ImageResult(success=False, error=str(e))

    def _build_prompt(self, request: ImageRequest) -> str:
        """Build the full prompt with templates and suffixes."""
        parts = []

        # Add template prefix
        if request.prefix_type == "generate":
            parts.append(PROMPT_TEMPLATE_CREATE)
        elif request.prefix_type == "edit":
            parts.append(PROMPT_TEMPLATE_EDIT)

        # Add style suffix if provided
        if request.style_suffix:
            parts.append(request.style_suffix)

        # Add the main prompt
        parts.append(request.prompt)

        # Add clean suffix to prevent artifacts
        if request.add_clean_suffix:
            parts.append(PROMPT_SUFFIX_CLEAN)

        return " ".join(parts)

    async def _generate_replicate(self, request: ImageRequest, prompt: str) -> ImageResult:
        """Generate using Replicate API."""
        if not settings.replicate_api_token:
            return ImageResult(success=False, error="Replicate API token not configured")

        # Ensure the replicate library can find the token
        # (pydantic loads from .env but doesn't export to os.environ)
        import os
        os.environ["REPLICATE_API_TOKEN"] = settings.replicate_api_token

        import replicate

        model_id = REPLICATE_MODELS.get(request.model)
        if not model_id:
            return ImageResult(success=False, error=f"Unknown Replicate model: {request.model}")

        # Prepare input
        input_data: dict[str, Any] = {
            "prompt": prompt,
        }

        # Handle model-specific parameters
        if request.model == ImageModel.Z_IMAGE_TURBO:
            # Z-Image-Turbo uses height parameter instead of aspect_ratio
            # Convert aspect ratio to height (width is auto-calculated)
            # Note: Z-Image-Turbo is primarily used for reference images (1:1 portraits)
            aspect_to_height = {
                "1:1": 768,
                "16:9": 576,
                "9:16": 1024,
                "4:3": 672,
                "3:4": 896,
            }
            input_data["height"] = aspect_to_height.get(request.aspect_ratio, 768)
        else:
            # Most models use aspect_ratio
            if request.aspect_ratio:
                input_data["aspect_ratio"] = request.aspect_ratio

        # Add seed - use provided seed or generate random one for variation
        # This ensures each generation is unique unless explicitly seeded
        seed = request.seed if request.seed is not None else random.randint(0, 2147483647)
        input_data["seed"] = seed
        logger.debug(f"Using seed: {seed}")

        # Disable safety checker for legitimate creative content
        # This prevents false positives on period-appropriate costume descriptions
        input_data["disable_safety_checker"] = True

        # Set safety tolerance to max for Flux models (1-5 scale, 5 = most permissive)
        if request.model in [ImageModel.FLUX_2_PRO, ImageModel.FLUX_1_1_PRO]:
            input_data["safety_tolerance"] = 5  # Most permissive
            input_data["output_format"] = "png"

        # Add negative prompt
        if request.negative_prompt:
            input_data["negative_prompt"] = request.negative_prompt

        # Handle reference images for models that support them
        if request.reference_images:
            # Determine max refs and parameter name based on model
            if request.model == ImageModel.SEEDREAM:
                max_refs = 14  # Seedream 4.5 supports up to 14 reference images
                ref_param = "image_input"
            elif request.model == ImageModel.FLUX_2_PRO:
                max_refs = 8
                ref_param = "input_images"
            elif request.model == ImageModel.P_IMAGE_EDIT:
                max_refs = 8
                ref_param = "reference_images"
            else:
                max_refs = 0  # Model doesn't support reference images
                ref_param = None

            if ref_param:
                ref_images = []
                for ref_path in request.reference_images[:max_refs]:
                    if ref_path.exists():
                        with open(ref_path, "rb") as f:
                            img_data = base64.b64encode(f.read()).decode()
                            ref_images.append(f"data:image/png;base64,{img_data}")
                if ref_images:
                    input_data[ref_param] = ref_images
                    logger.info(f"Added {len(ref_images)} reference images via '{ref_param}'")

        # Run the model
        try:
            output = await asyncio.to_thread(
                replicate.run,
                model_id,
                input=input_data
            )

            # Handle different output formats from Replicate
            # Newer versions return FileOutput objects, older return URLs
            image_url = None
            image_data = None

            if isinstance(output, list) and len(output) > 0:
                item = output[0]
                # Check if it's a FileOutput object (has .read() method)
                if hasattr(item, 'read'):
                    image_data = await asyncio.to_thread(item.read)
                elif hasattr(item, 'url'):
                    image_url = item.url
                elif isinstance(item, str):
                    image_url = item
                else:
                    image_url = str(item)
            elif hasattr(output, 'read'):
                # Single FileOutput object
                image_data = await asyncio.to_thread(output.read)
            elif hasattr(output, 'url'):
                image_url = output.url
            elif isinstance(output, str):
                image_url = output
            else:
                # Try to convert to string (might be a URL)
                image_url = str(output)

            # Download the image if we got a URL
            if image_url and not image_data:
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(image_url)
                    response.raise_for_status()
                    image_data = response.content

            if not image_data:
                return ImageResult(success=False, error="No image data received from model")

            # Save if output path provided
            image_path = None
            if request.output_path:
                request.output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(request.output_path, "wb") as f:
                    f.write(image_data)
                image_path = request.output_path

            return ImageResult(
                success=True,
                image_path=image_path,
                image_data=image_data
            )

        except Exception as e:
            logger.exception(f"Replicate generation failed: {e}")
            return ImageResult(success=False, error=str(e))

    async def _generate_gemini(self, request: ImageRequest, prompt: str) -> ImageResult:
        """
        Generate using Google Gemini image generation (Nano Banana).

        Models:
        - gemini-2.5-flash-image: Nano Banana - Fast, efficient, 1024px
        - gemini-3-pro-image-preview: Nano Banana Pro - Professional quality, up to 4K

        Nano Banana Pro features:
        - High-resolution output: 1K, 2K, 4K
        - Advanced text rendering for infographics, logos
        - Grounding with Google Search for real-time data
        - Up to 14 reference images (6 objects + 5 humans)
        - Thinking mode for complex prompts
        """
        if not settings.gemini_api_key:
            return ImageResult(success=False, error="Gemini API key not configured")

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.gemini_api_key)

            # Select model based on request
            # Nano Banana = gemini-2.5-flash-image (fast, efficient)
            # Nano Banana Pro = gemini-3-pro-image-preview (professional, 4K, thinking)
            model_name = (
                "gemini-2.5-flash-image"
                if request.model == ImageModel.NANO_BANANA
                else "gemini-3-pro-image-preview"
            )

            # Build content parts
            contents = [prompt]

            # Add reference images if provided
            # Nano Banana: up to 3 images work best
            # Nano Banana Pro: up to 14 images (6 objects + 5 humans high-fidelity)
            max_refs = 14 if request.model == ImageModel.NANO_BANANA_PRO else 3
            if request.reference_images:
                for ref_path in request.reference_images[:max_refs]:
                    if ref_path.exists():
                        with open(ref_path, "rb") as f:
                            img_data = f.read()
                        # Determine mime type from extension
                        suffix = ref_path.suffix.lower()
                        mime_map = {
                            ".png": "image/png",
                            ".jpg": "image/jpeg",
                            ".jpeg": "image/jpeg",
                            ".webp": "image/webp",
                            ".gif": "image/gif",
                        }
                        mime_type = mime_map.get(suffix, "image/png")
                        contents.append(
                            types.Part.from_bytes(
                                data=img_data,
                                mime_type=mime_type
                            )
                        )

            # Configure image generation settings
            # Map aspect ratio to Gemini format
            aspect_ratio = request.aspect_ratio or "16:9"

            # For Nano Banana Pro, we can specify resolution
            image_size = "2K" if request.model == ImageModel.NANO_BANANA_PRO else None

            # Build generation config
            config = types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            )

            # Run generation
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=model_name,
                contents=contents,
                config=config,
            )

            # Extract image from response
            if response.candidates and len(response.candidates) > 0:
                for part in response.candidates[0].content.parts:
                    # Skip thought parts (interim thinking images)
                    if hasattr(part, 'thought') and part.thought:
                        continue

                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Handle data - SDK returns raw bytes, not base64
                        raw_data = part.inline_data.data
                        if isinstance(raw_data, bytes):
                            image_data = raw_data
                        else:
                            # Fallback for older SDK versions that might return base64
                            image_data = base64.b64decode(raw_data)

                        # Save if output path provided
                        image_path = None
                        if request.output_path:
                            request.output_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(request.output_path, "wb") as f:
                                f.write(image_data)
                            image_path = request.output_path

                        return ImageResult(
                            success=True,
                            image_path=image_path,
                            image_data=image_data
                        )

            return ImageResult(success=False, error="No image in response")

        except ImportError:
            # Fallback to old SDK if new one not installed
            logger.warning("google-genai package not installed, trying legacy SDK")
            return await self._generate_gemini_legacy(request, prompt)
        except Exception as e:
            logger.exception(f"Gemini generation failed: {e}")
            return ImageResult(success=False, error=str(e))

    async def _generate_gemini_legacy(self, request: ImageRequest, prompt: str) -> ImageResult:
        """Fallback to legacy google.generativeai SDK."""
        try:
            import google.generativeai as genai

            genai.configure(api_key=settings.gemini_api_key)

            model_name = (
                "gemini-2.5-flash-image"
                if request.model == ImageModel.NANO_BANANA
                else "gemini-3-pro-image-preview"
            )

            model = genai.GenerativeModel(model_name)

            # Build content parts
            parts = [prompt]

            # Add reference images
            if request.reference_images:
                max_refs = 14 if request.model == ImageModel.NANO_BANANA_PRO else 3
                for ref_path in request.reference_images[:max_refs]:
                    if ref_path.exists():
                        with open(ref_path, "rb") as f:
                            img_data = f.read()
                        parts.append({
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": base64.b64encode(img_data).decode()
                            }
                        })

            response = await asyncio.to_thread(
                model.generate_content,
                parts,
                generation_config={"response_mime_type": "image/png"}
            )

            # Extract image from response
            if hasattr(response, 'parts') and len(response.parts) > 0:
                for part in response.parts:
                    if hasattr(part, 'inline_data'):
                        # Handle data - SDK may return raw bytes or base64
                        raw_data = part.inline_data.data
                        if isinstance(raw_data, bytes):
                            image_data = raw_data
                        else:
                            image_data = base64.b64decode(raw_data)

                        image_path = None
                        if request.output_path:
                            request.output_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(request.output_path, "wb") as f:
                                f.write(image_data)
                            image_path = request.output_path

                        return ImageResult(
                            success=True,
                            image_path=image_path,
                            image_data=image_data
                        )

            return ImageResult(success=False, error="No image in response (legacy SDK)")

        except Exception as e:
            logger.exception(f"Gemini legacy generation failed: {e}")
            return ImageResult(success=False, error=str(e))

    async def _generate_stability(self, request: ImageRequest, prompt: str) -> ImageResult:
        """Generate using Stability AI."""
        # Stability AI can be accessed via Replicate for simplicity
        # Or implement direct API if needed
        return ImageResult(
            success=False,
            error="Stability AI direct API not implemented - use Replicate SDXL instead"
        )


    async def edit_image(self, request: ImageRequest) -> ImageResult:
        """
        Edit an existing image using Nano Banana Pro's semantic masking.

        This uses conversational editing - describe what to change and the model
        will identify and modify only that part while preserving the rest.

        Example:
            result = await generator.edit_image(ImageRequest(
                prompt="Change the sofa color to red",
                source_image=Path("living_room.png"),
                model=ImageModel.NANO_BANANA_PRO
            ))
        """
        if not request.source_image or not request.source_image.exists():
            return ImageResult(success=False, error="Source image required for editing")

        # Force Nano Banana Pro for best editing results
        request.model = ImageModel.NANO_BANANA_PRO

        # Add source image as reference
        request.reference_images = [request.source_image] + list(request.reference_images or [])

        # Build edit prompt
        edit_prompt = request.edit_instruction or request.prompt

        # Add context to help model understand this is an edit
        full_prompt = f"Edit the provided image: {edit_prompt}. Keep everything else unchanged."

        return await self._generate_gemini_edit(request, full_prompt)

    async def _generate_gemini_edit(self, request: ImageRequest, prompt: str) -> ImageResult:
        """
        Gemini-specific image editing using Nano Banana Pro.

        Supports:
        - Semantic masking (describe what to change, model finds it)
        - Style transfer
        - Element addition/removal
        - Color/lighting adjustments
        """
        if not settings.gemini_api_key:
            return ImageResult(success=False, error="Gemini API key not configured")

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.gemini_api_key)

            # Build content with source image first, then edit instruction
            contents = []

            # Add source image
            if request.source_image and request.source_image.exists():
                with open(request.source_image, "rb") as f:
                    img_data = f.read()
                suffix = request.source_image.suffix.lower()
                mime_map = {
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".webp": "image/webp",
                }
                mime_type = mime_map.get(suffix, "image/png")
                contents.append(
                    types.Part.from_bytes(data=img_data, mime_type=mime_type)
                )

            # Add additional reference images (for style transfer, element addition)
            for ref_path in (request.reference_images or [])[1:]:  # Skip first (source)
                if ref_path.exists():
                    with open(ref_path, "rb") as f:
                        ref_data = f.read()
                    contents.append(
                        types.Part.from_bytes(
                            data=ref_data,
                            mime_type="image/png"
                        )
                    )

            # Add the edit prompt
            contents.append(prompt)

            # Configure for image output
            config = types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            )

            # Run generation
            response = await asyncio.to_thread(
                client.models.generate_content,
                model="gemini-3-pro-image-preview",
                contents=contents,
                config=config,
            )

            # Extract edited image
            if response.candidates and len(response.candidates) > 0:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'thought') and part.thought:
                        continue

                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Handle data - SDK returns raw bytes, not base64
                        raw_data = part.inline_data.data
                        if isinstance(raw_data, bytes):
                            image_data = raw_data
                        else:
                            image_data = base64.b64decode(raw_data)

                        image_path = None
                        if request.output_path:
                            request.output_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(request.output_path, "wb") as f:
                                f.write(image_data)
                            image_path = request.output_path

                        return ImageResult(
                            success=True,
                            image_path=image_path,
                            image_data=image_data
                        )

            return ImageResult(success=False, error="No edited image in response")

        except ImportError:
            return ImageResult(
                success=False,
                error="google-genai package not installed. Run: pip install google-genai"
            )
        except Exception as e:
            logger.exception(f"Gemini edit failed: {e}")
            return ImageResult(success=False, error=str(e))


# Convenience function
async def generate_image(
    prompt: str,
    model: str = "p_image_edit",
    output_path: Optional[Path] = None,
    reference_images: Optional[list[Path]] = None,
) -> ImageResult:
    """Quick image generation helper."""
    model_enum = ImageModel(model) if model in [m.value for m in ImageModel] else ImageModel.FLUX_2_PRO

    request = ImageRequest(
        prompt=prompt,
        model=model_enum,
        output_path=output_path,
        reference_images=reference_images or [],
    )

    generator = ImageGenerator()
    return await generator.generate(request)


async def edit_image(
    source_image: Path,
    edit_instruction: str,
    output_path: Optional[Path] = None,
    reference_images: Optional[list[Path]] = None,
) -> ImageResult:
    """
    Quick image editing helper using Nano Banana Pro.

    Args:
        source_image: The image to edit
        edit_instruction: What to change (e.g., "Change the sky to sunset colors")
        output_path: Where to save the result
        reference_images: Additional reference images for style/elements

    Returns:
        ImageResult with the edited image
    """
    request = ImageRequest(
        prompt=edit_instruction,
        model=ImageModel.NANO_BANANA_PRO,
        source_image=source_image,
        edit_instruction=edit_instruction,
        output_path=output_path,
        reference_images=reference_images or [],
    )

    generator = ImageGenerator()
    return await generator.edit_image(request)
