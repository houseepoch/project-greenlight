"""
Test script for the ingestion pipeline.
Runs entity extraction on the test pitch.
"""

import asyncio
import json
from pathlib import Path

# Add project to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from greenlight.core.ingestion import IngestionPipeline
from greenlight.core.config import settings


async def main():
    print("=" * 60)
    print("INGESTION PIPELINE TEST")
    print("=" * 60)

    # Check API keys
    print("\nAPI Keys Status:")
    print(f"  xAI: {'OK' if settings.xai_api_key else 'MISSING'}")
    print(f"  Replicate: {'OK' if settings.replicate_api_token else 'MISSING'}")
    print(f"  Gemini: {'OK' if settings.gemini_api_key else 'MISSING'}")

    if not settings.xai_api_key:
        print("\nERROR: XAI_API_KEY not configured!")
        return

    # Set up paths
    project_path = Path(__file__).parent / "test_project"
    pitch_file = project_path / "pitch.md"

    if not pitch_file.exists():
        print(f"\nERROR: Pitch file not found: {pitch_file}")
        return

    print(f"\nProject path: {project_path}")
    print(f"Pitch file: {pitch_file}")

    # Create pipeline with logging
    def log(msg):
        print(f"  {msg}")

    def progress(p):
        bar_len = 30
        filled = int(bar_len * p)
        bar = "#" * filled + "-" * (bar_len - filled)
        print(f"\r  Progress: [{bar}] {p*100:.0f}%", end="", flush=True)
        if p >= 1.0:
            print()

    print("\n" + "-" * 60)
    print("Starting ingestion...")
    print("-" * 60)

    pipeline = IngestionPipeline(
        project_path=project_path,
        log_callback=log,
        progress_callback=progress,
    )

    try:
        result = await pipeline.ingest_files([pitch_file])

        print("\n" + "-" * 60)
        print("RESULTS")
        print("-" * 60)

        if result["success"]:
            print("\n[OK] Ingestion successful!")
            print(f"\nStats:")
            stats = result["stats"]
            print(f"  Documents processed: {stats['documents_processed']}")
            print(f"  Images processed: {stats['images_processed']}")
            print(f"  Total chunks: {stats['total_chunks']}")
            print(f"  Characters found: {stats['characters_found']}")
            print(f"  Locations found: {stats['locations_found']}")
            print(f"  Props found: {stats['props_found']}")

            # Load and display entities
            entities_path = Path(result["entities_path"])
            if entities_path.exists():
                entities_data = json.loads(entities_path.read_text())

                print("\n" + "=" * 60)
                print("EXTRACTED ENTITIES")
                print("=" * 60)

                print("\nCHARACTERS:")
                for char in entities_data["entities"]["characters"][:10]:
                    name = char.get("name", char.get("descriptive_name", "Unknown"))
                    role = char.get("role_hint", "")
                    mentions = char.get("mentions", 1)
                    print(f"  - {name} ({role}) - {mentions} mentions")

                print("\nLOCATIONS:")
                for loc in entities_data["entities"]["locations"][:10]:
                    name = loc.get("name", loc.get("descriptive_name", "Unknown"))
                    type_hint = loc.get("type_hint", "")
                    mentions = loc.get("mentions", 1)
                    print(f"  - {name} ({type_hint}) - {mentions} mentions")

                print("\nPROPS:")
                for prop in entities_data["entities"]["props"][:10]:
                    name = prop.get("name", prop.get("descriptive_name", "Unknown"))
                    significance = prop.get("significance", "")
                    mentions = prop.get("mentions", 1)
                    print(f"  - {name} ({significance}) - {mentions} mentions")
        else:
            print(f"\n[FAIL] Ingestion failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
