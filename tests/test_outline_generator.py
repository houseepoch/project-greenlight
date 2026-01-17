"""
Test script for Outline Generator Pipeline.

Tests generating 3 story outline variants from world_config.json.
"""

import asyncio
import json
from pathlib import Path

# Add the project to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from greenlight.pipelines.outline_generator import OutlineGeneratorPipeline


def log(msg: str):
    print(f"  {msg}")


def progress(p: float):
    bar_width = 30
    filled = int(bar_width * p)
    bar = '#' * filled + '-' * (bar_width - filled)
    print(f"\r  [{bar}] {p*100:.0f}%", end='', flush=True)
    if p >= 1.0:
        print()


def variant_update(name: str, description: str, beats: list):
    print(f"\n  === {name} ===")
    print(f"  {description}")
    print(f"  Generated {len(beats)} beats")


async def main():
    project_path = Path(__file__).parent / "test_project"

    # Check for world_config.json
    world_config_path = project_path / "world_bible" / "world_config.json"
    if not world_config_path.exists():
        print("[ERROR] No world_config.json found!")
        print("Run test_world_builder.py first to generate the world config.")
        return

    print("\n" + "=" * 60)
    print("OUTLINE GENERATOR TEST")
    print("=" * 60)
    print(f"\nProject: {project_path}")

    # Load world config to show what we're working with
    world_config = json.loads(world_config_path.read_text(encoding="utf-8"))
    print(f"Title: {world_config.get('title', 'Untitled')}")
    print(f"Characters: {len(world_config.get('characters', []))}")
    print(f"Locations: {len(world_config.get('locations', []))}")

    print("\n" + "-" * 60)
    print("Generating 3 outline variants...")
    print("-" * 60)

    pipeline = OutlineGeneratorPipeline(
        project_path=project_path,
        log_callback=log,
        progress_callback=progress,
        variant_callback=variant_update,
    )

    result = await pipeline.run()

    print("\n" + "-" * 60)
    print("RESULT")
    print("-" * 60)

    if result["success"]:
        print("[OK] Outline generation complete!")
        print(f"Saved to: {result.get('outlines_path')}")

        # Load and display variants
        outlines_path = Path(result["outlines_path"])
        data = json.loads(outlines_path.read_text(encoding="utf-8"))

        print("\n" + "=" * 60)
        print("GENERATED VARIANTS")
        print("=" * 60)

        for key, variant in data.get("variants", {}).items():
            print(f"\n--- {variant['name']} ({len(variant['beats'])} beats) ---")
            print(f"Description: {variant['description']}\n")
            for i, beat in enumerate(variant["beats"], 1):
                print(f"  {i:02d}. {beat}")

    else:
        print(f"[FAIL] {result.get('error')}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
