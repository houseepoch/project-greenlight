"""
Test ICB (Intelligent Continuity Blending) on Orchid's Gambit

Uses existing frames from scene_continuity_test and applies
individual edits to fix each issue.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Set API keys
os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "AIzaSyCXwkYJUoNafQG7sSoyAzrI52pK16pHofY")

# Project paths
ORCHIDS_PROJECT = Path("C:/Users/thriv/greenlight_projects/orchid's_gambit")
SOURCE_DIR = ORCHIDS_PROJECT / "scene_continuity_test"
OUTPUT_DIR = ORCHIDS_PROJECT / "blended"


async def main():
    from greenlight.core.icb import IntelligentContinuityBlender

    print("=" * 60)
    print("ICB Test - Orchid's Gambit")
    print("=" * 60)
    print(f"Project: {ORCHIDS_PROJECT}")
    print(f"Source: {SOURCE_DIR}")
    print(f"Output: {OUTPUT_DIR}")

    # Get frame IDs from source
    frame_ids = [p.stem for p in sorted(SOURCE_DIR.glob("sc*.png"))]
    print(f"\nFrames to process: {len(frame_ids)}")
    for fid in frame_ids:
        print(f"  {fid}")

    if not frame_ids:
        print("[ERROR] No source frames found")
        return

    # Create ICB blender
    blender = IntelligentContinuityBlender(ORCHIDS_PROJECT)

    print("\n" + "=" * 60)
    print("Running ICB")
    print("=" * 60)

    result = await blender.blend_frames(
        frame_ids=frame_ids,
        source_dir=SOURCE_DIR,
        output_dir=OUTPUT_DIR,
        replace_originals=False,
        severity_filter=["critical", "major"],  # Only process critical and major issues
    )

    print("\n" + "=" * 60)
    print("ICB Results")
    print("=" * 60)
    print(f"Frames processed: {result.frames_processed}")
    print(f"Frames with issues: {result.frames_with_issues}")
    print(f"Total issues: {result.total_issues}")
    print(f"Edits attempted: {result.total_edits_attempted}")
    print(f"Edits successful: {result.total_edits_successful}")
    print(f"Continuity before: {result.continuity_before * 100:.1f}%")
    print(f"Output dir: {result.output_dir}")

    print("\n--- Frame Details ---")
    for fr in result.frame_results:
        if fr.total_issues > 0:
            print(f"\n{fr.frame_id}:")
            print(f"  Issues: {fr.total_issues}")
            print(f"  Edits: {fr.edits_successful}/{fr.edits_applied} successful")
            for er in fr.edit_results:
                status = "OK" if er.success else f"FAIL: {er.error}"
                print(f"    [{er.severity}] {er.issue_type}: {status}")

    print("\n" + "=" * 60)
    print("ICB Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
