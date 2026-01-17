"""
Test script for the World Builder pipeline.
Generates world context and entity descriptions from confirmed entities.
"""

import asyncio
import json
from pathlib import Path

# Add project to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from greenlight.pipelines.world_builder import WorldBuilderPipeline
from greenlight.core.config import settings


async def main():
    print("=" * 70)
    print("WORLD BUILDER PIPELINE TEST")
    print("=" * 70)

    # Check API keys
    print("\nAPI Keys Status:")
    print(f"  xAI: {'OK' if settings.xai_api_key else 'MISSING'}")

    if not settings.xai_api_key:
        print("\nERROR: XAI_API_KEY not configured!")
        return

    # Set up paths
    project_path = Path(__file__).parent / "test_project"
    confirmed_path = project_path / "ingestion" / "confirmed_entities.json"

    if not confirmed_path.exists():
        print(f"\nERROR: Confirmed entities not found: {confirmed_path}")
        return

    print(f"\nProject path: {project_path}")
    print(f"Confirmed entities: {confirmed_path}")

    # Create pipeline with logging
    def log(msg):
        print(f"  {msg}")

    def progress(p):
        bar_len = 40
        filled = int(bar_len * p)
        bar = "#" * filled + "-" * (bar_len - filled)
        print(f"\r  Progress: [{bar}] {p*100:.0f}%", end="", flush=True)
        if p >= 1.0:
            print()

    def field_update(field_name, value, status):
        # Truncate long values for display
        display_value = value[:60] + "..." if len(value) > 60 else value
        print(f"\n    >> {field_name}: {display_value}")

    print("\n" + "-" * 70)
    print("Starting World Builder...")
    print("-" * 70)

    pipeline = WorldBuilderPipeline(
        project_path=project_path,
        visual_style="live_action",
        log_callback=log,
        progress_callback=progress,
        field_callback=field_update,
    )

    try:
        result = await pipeline.run()

        print("\n" + "-" * 70)
        print("RESULTS")
        print("-" * 70)

        if result["success"]:
            print("\n[OK] World Builder successful!")
            print(f"\nStats:")
            print(f"  Characters: {result.get('characters', 0)}")
            print(f"  Locations: {result.get('locations', 0)}")
            print(f"  Props: {result.get('props', 0)}")

            # Load and display world config
            world_config_path = project_path / "world_bible" / "world_config.json"
            if world_config_path.exists():
                world_config = json.loads(world_config_path.read_text())

                print("\n" + "=" * 70)
                print("WORLD CONTEXT")
                print("=" * 70)

                wc = world_config.get("world_context", {})
                for field, value in wc.items():
                    if value and field != "setting_rules":
                        print(f"\n{field.upper().replace('_', ' ')}:")
                        print(f"  {value}")

                print("\n" + "=" * 70)
                print("CHARACTERS")
                print("=" * 70)

                for char in world_config.get("characters", []):
                    print(f"\n{char.get('name')} ({char.get('tag')}) - {char.get('role', 'unknown')}")
                    print("-" * 40)
                    if char.get("appearance"):
                        print(f"  Appearance: {char['appearance']}")
                    if char.get("clothing"):
                        print(f"  Clothing: {char['clothing']}")
                    if char.get("personality"):
                        print(f"  Personality: {char['personality']}")
                    if char.get("summary"):
                        print(f"  Summary: {char['summary']}")

                print("\n" + "=" * 70)
                print("LOCATIONS")
                print("=" * 70)

                for loc in world_config.get("locations", []):
                    print(f"\n{loc.get('name')} ({loc.get('tag')})")
                    print("-" * 40)
                    if loc.get("description"):
                        print(f"  Description: {loc['description']}")
                    if loc.get("view_north"):
                        print(f"  View North: {loc['view_north']}")
                    if loc.get("view_east"):
                        print(f"  View East: {loc['view_east']}")
                    if loc.get("view_south"):
                        print(f"  View South: {loc['view_south']}")
                    if loc.get("view_west"):
                        print(f"  View West: {loc['view_west']}")

                print("\n" + "=" * 70)
                print("PROPS")
                print("=" * 70)

                for prop in world_config.get("props", []):
                    print(f"\n{prop.get('name')} ({prop.get('tag')})")
                    print("-" * 40)
                    if prop.get("description"):
                        print(f"  Description: {prop['description']}")

        else:
            print(f"\n[FAIL] World Builder failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
