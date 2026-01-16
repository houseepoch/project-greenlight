"""
Test script to regenerate Madame Chou specifically to test age accuracy.
"""

import asyncio
from pathlib import Path
from greenlight.pipelines.references import ReferencesPipeline

PROJECT_PATH = Path(r"C:\Users\thriv\greenlight_projects\orichids_gambit")


async def test_regenerate():
    """Regenerate Madame Chou with improved age prompts."""

    # Delete existing image
    refs_dir = PROJECT_PATH / "references"
    img_path = refs_dir / "CHAR_MADAME_CHOU.png"
    if img_path.exists():
        print(f"Deleting existing: {img_path}")
        img_path.unlink()

    # Create pipeline with flux_2_pro model
    pipeline = ReferencesPipeline(
        project_path=PROJECT_PATH,
        image_model="flux_2_pro",
        entity_filter=["CHAR_MADAME_CHOU"],
        log_callback=lambda x: print(f"  LOG: {x}"),
        progress_callback=lambda x: print(f"  Progress: {x:.1%}"),
    )

    print("\n=== Regenerating Madame Chou (Age Test) ===\n")
    result = await pipeline.run()

    print("\n=== Results ===")
    print(f"Success: {result.get('success')}")
    print(f"Generated: {result.get('generated', 0)}")
    if result.get('error'):
        print(f"Error: {result.get('error')}")

    return result


if __name__ == "__main__":
    asyncio.run(test_regenerate())
