"""
Test script to regenerate character references for Orchids Gambit project.
Tests: Mei, Madame Chou, Zhoa, Min Zhu
"""

import asyncio
from pathlib import Path
from greenlight.pipelines.references import ReferencesPipeline

PROJECT_PATH = Path(r"C:\Users\thriv\greenlight_projects\orichids_gambit")
TEST_CHARACTERS = ["CHAR_MEI", "CHAR_MADAME_CHOU", "CHAR_ZHOA", "CHAR_MIN_ZHU"]


async def test_regenerate():
    """Regenerate test characters with improved prompts."""

    # Delete existing images first
    refs_dir = PROJECT_PATH / "references"
    for tag in TEST_CHARACTERS:
        img_path = refs_dir / f"{tag}.png"
        if img_path.exists():
            print(f"Deleting existing: {img_path}")
            img_path.unlink()

    # Create pipeline with flux_2_pro model
    pipeline = ReferencesPipeline(
        project_path=PROJECT_PATH,
        image_model="flux_2_pro",
        entity_filter=TEST_CHARACTERS,
        log_callback=lambda x: print(f"  LOG: {x}"),
        progress_callback=lambda x: print(f"  Progress: {x:.1%}"),
    )

    print("\n=== Starting Reference Generation Test ===\n")
    result = await pipeline.run()

    print("\n=== Results ===")
    print(f"Success: {result.get('success')}")
    print(f"Generated: {result.get('generated', 0)}")
    print(f"Failed: {result.get('failed', 0)}")
    if result.get('error'):
        print(f"Error: {result.get('error')}")

    return result


if __name__ == "__main__":
    asyncio.run(test_regenerate())
