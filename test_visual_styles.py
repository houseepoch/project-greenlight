"""
Test script to compare different visual styles for character generation.
Tests: anime, animation_3d, claymation, mixed
"""

import asyncio
import json
import shutil
from pathlib import Path
from greenlight.core.image_gen import ImageGenerator, ImageRequest, ImageModel
from greenlight.pipelines.references import (
    get_character_prompt_template,
    get_media_style_prompt,
    enhance_appearance_for_age,
    MEDIA_TYPE_STYLES
)

PROJECT_PATH = Path(r"C:\Users\thriv\greenlight_projects\orichids_gambit")
OUTPUT_DIR = Path(r"C:\Users\thriv\Documents\project-greenlight\style_tests")

# Visual styles to test
STYLES_TO_TEST = ["anime", "animation_3d", "claymation", "mixed"]


async def test_style(style: str, char_data: dict, style_notes: str = "") -> Path:
    """Generate Madame Chou in a specific visual style."""

    print(f"\n--- Testing {style.upper()} style ---")

    # Get the appropriate template
    char_template = get_character_prompt_template(style)
    media_style_prompt = get_media_style_prompt(style)

    # Get appearance and enhance if live_action
    raw_appearance = char_data.get("appearance", "")
    if style == "live_action":
        appearance = enhance_appearance_for_age(raw_appearance)
    else:
        appearance = raw_appearance

    # Build prompt
    prompt = char_template.format(
        name=char_data.get("name", "Madame Chou"),
        appearance=appearance,
        clothing=char_data.get("clothing", ""),
        media_style_prompt=media_style_prompt,
        style_notes=style_notes,
    )

    print(f"Prompt preview: {prompt[:200]}...")

    # Output path
    output_path = OUTPUT_DIR / f"madame_chou_{style}.png"

    # Generate
    generator = ImageGenerator()
    result = await generator.generate(ImageRequest(
        prompt=prompt,
        model=ImageModel.Z_IMAGE_TURBO,
        output_path=output_path,
        aspect_ratio="1:1",
        prefix_type="none",
        add_clean_suffix=True,
    ))

    if result.success:
        print(f"  SUCCESS: Saved to {output_path}")
    else:
        print(f"  FAILED: {result.error}")

    return output_path


async def main():
    """Run all style tests."""

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load character data from world_config
    world_config_path = PROJECT_PATH / "world_bible" / "world_config.json"
    world_config = json.loads(world_config_path.read_text(encoding="utf-8"))

    # Find Madame Chou
    char_data = None
    for char in world_config.get("characters", []):
        if char.get("tag") == "CHAR_MADAME_CHOU":
            char_data = char
            break

    if not char_data:
        print("ERROR: Could not find CHAR_MADAME_CHOU in world config")
        return

    print(f"Character: {char_data.get('name')}")
    print(f"Appearance: {char_data.get('appearance', '')[:100]}...")

    # Test each style
    results = {}
    for style in STYLES_TO_TEST:
        try:
            output_path = await test_style(style, char_data)
            results[style] = str(output_path)
        except Exception as e:
            print(f"  ERROR testing {style}: {e}")
            results[style] = f"ERROR: {e}"

    print("\n" + "=" * 50)
    print("RESULTS SUMMARY")
    print("=" * 50)
    for style, path in results.items():
        print(f"  {style}: {path}")

    print(f"\nAll test images saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
