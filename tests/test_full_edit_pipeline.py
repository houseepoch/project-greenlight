"""
Full Edit Pipeline Test for Orchid's Gambit

This script:
1. Uses already generated frames from scene_continuity_test/
2. Runs enhanced continuity check (with AI artifact detection)
3. Applies edit prompts using Nano Banana Pro
4. Saves corrected frames to /editedboard

Project: C:/Users/thriv/greenlight_projects/orchid's_gambit
"""

import asyncio
import json
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Set API keys
os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "AIzaSyCXwkYJUoNafQG7sSoyAzrI52pK16pHofY")

# Project paths
ORCHIDS_PROJECT = Path("C:/Users/thriv/greenlight_projects/orchid's_gambit")
SOURCE_DIR = ORCHIDS_PROJECT / "scene_continuity_test"
OUTPUT_DIR = ORCHIDS_PROJECT / "editedboard"


async def run_continuity_check(project_path: Path, source_dir: Path):
    """Run enhanced continuity check on source frames."""
    from greenlight.core.continuity_checker import ContinuityChecker

    print("\n" + "=" * 60)
    print("Phase 1: Running Enhanced Continuity Check")
    print("=" * 60)

    checker = ContinuityChecker(project_path)
    checker.output_dir = source_dir
    checker.report_dir = source_dir / "continuity_reports"

    result = await checker.check_continuity(batch_size=8)

    print(f"\nAnalyzed {result.total_frames} frames")
    print(f"Consistency: {result.overall_consistency_score * 100:.1f}%")
    print(f"Issues found: {result.total_issues}")
    print(f"  Critical: {result.critical_count}")
    print(f"  Major: {result.major_count}")
    print(f"  Minor: {result.minor_count}")

    return result


async def apply_edits(result, source_dir: Path, output_dir: Path, references_dir: Path):
    """Apply edit prompts to frames with issues using Nano Banana Pro."""
    from greenlight.core.image_gen import ImageGenerator, ImageRequest, ImageModel

    print("\n" + "=" * 60)
    print("Phase 2: Applying Corrections with Nano Banana Pro")
    print("=" * 60)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    generator = ImageGenerator(project_path=output_dir.parent)

    # Collect all frames and their issues
    frames_to_edit = []
    frames_to_copy = []

    for batch in result.batch_reports:
        for frame_report in batch.frame_reports:
            source_path = Path(frame_report.frame_path)
            if not source_path.exists():
                source_path = source_dir / f"{frame_report.frame_id}.png"

            if frame_report.issues:
                # Combine all edit prompts for this frame
                edit_prompts = [issue.edit_prompt for issue in frame_report.issues if issue.edit_prompt]
                affected_entities = set()
                for issue in frame_report.issues:
                    affected_entities.update(issue.affected_entities)

                frames_to_edit.append({
                    "frame_id": frame_report.frame_id,
                    "source_path": source_path,
                    "edit_prompts": edit_prompts,
                    "affected_entities": list(affected_entities),
                    "issues": frame_report.issues,
                })
            else:
                # No issues - just copy the frame
                frames_to_copy.append({
                    "frame_id": frame_report.frame_id,
                    "source_path": source_path,
                })

    print(f"\nFrames to edit: {len(frames_to_edit)}")
    print(f"Frames to copy (no issues): {len(frames_to_copy)}")

    # Copy frames with no issues
    for frame_info in frames_to_copy:
        source = frame_info["source_path"]
        dest = output_dir / f"{frame_info['frame_id']}.png"
        if source.exists():
            shutil.copy2(source, dest)
            print(f"[COPY] {frame_info['frame_id']} -> editedboard/")

    # Edit frames with issues
    edit_results = []
    for i, frame_info in enumerate(frames_to_edit, 1):
        frame_id = frame_info["frame_id"]
        source_path = frame_info["source_path"]
        edit_prompts = frame_info["edit_prompts"]
        affected_entities = frame_info["affected_entities"]

        print(f"\n--- Editing {i}/{len(frames_to_edit)}: {frame_id} ---")
        print(f"  Issues: {len(frame_info['issues'])}")

        # Combine edit prompts into one comprehensive instruction
        combined_prompt = " ".join(edit_prompts)

        # Truncate if too long (Nano Banana Pro has limits)
        if len(combined_prompt) > 2000:
            combined_prompt = combined_prompt[:2000] + "..."

        print(f"  Edit prompt: {combined_prompt[:150]}...")

        # Gather reference images for affected entities
        reference_images = []
        for entity_tag in affected_entities:
            ref_filename = result.entity_reference_map.get(entity_tag, f"{entity_tag}.png")
            ref_path = references_dir / ref_filename
            if ref_path.exists():
                reference_images.append(ref_path)
                print(f"  Reference: {ref_filename}")

        output_path = output_dir / f"{frame_id}.png"

        try:
            # Use Nano Banana Pro for editing
            request = ImageRequest(
                prompt=combined_prompt,
                model=ImageModel.NANO_BANANA_PRO,
                aspect_ratio="16:9",
                reference_images=reference_images,
                source_image=source_path,  # Original image to edit
                output_path=output_path,
                tag=f"{frame_id}_edited",
                prefix_type="edit",
                add_clean_suffix=True,
                resolution="2K",
            )

            edit_result = await generator.generate(request)

            if edit_result.success:
                print(f"  [OK] Edited in {edit_result.generation_time_ms}ms")
                edit_results.append({
                    "frame_id": frame_id,
                    "success": True,
                    "time_ms": edit_result.generation_time_ms,
                })
            else:
                print(f"  [FAIL] {edit_result.error}")
                # Copy original as fallback
                if source_path.exists():
                    shutil.copy2(source_path, output_path)
                    print(f"  [FALLBACK] Copied original")
                edit_results.append({
                    "frame_id": frame_id,
                    "success": False,
                    "error": edit_result.error,
                })

        except Exception as e:
            print(f"  [ERROR] {e}")
            # Copy original as fallback
            if source_path.exists():
                shutil.copy2(source_path, output_path)
                print(f"  [FALLBACK] Copied original")
            edit_results.append({
                "frame_id": frame_id,
                "success": False,
                "error": str(e),
            })

    return edit_results


async def main():
    print("=" * 60)
    print("Full Edit Pipeline - Orchid's Gambit")
    print(f"Project: {ORCHIDS_PROJECT}")
    print(f"Source: {SOURCE_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 60)

    # Check paths exist
    if not ORCHIDS_PROJECT.exists():
        print(f"[ERROR] Project not found: {ORCHIDS_PROJECT}")
        return

    if not SOURCE_DIR.exists():
        print(f"[ERROR] Source directory not found: {SOURCE_DIR}")
        print("Run test_continuity_orchids_v2.py first to generate frames")
        return

    # List source frames
    source_frames = list(SOURCE_DIR.glob("sc*.png"))
    print(f"\nSource frames found: {len(source_frames)}")
    for f in sorted(source_frames):
        print(f"  {f.name}")

    references_dir = ORCHIDS_PROJECT / "references"

    # Phase 1: Run continuity check
    result = await run_continuity_check(ORCHIDS_PROJECT, SOURCE_DIR)

    if result.total_issues == 0:
        print("\n[INFO] No issues found - copying all frames to editedboard/")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        for frame_path in source_frames:
            dest = OUTPUT_DIR / frame_path.name
            shutil.copy2(frame_path, dest)
        print(f"Copied {len(source_frames)} frames")
    else:
        # Phase 2: Apply edits
        edit_results = await apply_edits(result, SOURCE_DIR, OUTPUT_DIR, references_dir)

        # Summary
        success_count = sum(1 for r in edit_results if r["success"])
        print(f"\n" + "=" * 60)
        print("Edit Results Summary")
        print("=" * 60)
        print(f"Frames edited: {success_count}/{len(edit_results)}")
        for r in edit_results:
            status = "OK" if r["success"] else "FAIL"
            print(f"  [{status}] {r['frame_id']}")

    # Save pipeline report
    report_path = OUTPUT_DIR / "edit_pipeline_report.json"
    report = {
        "project": str(ORCHIDS_PROJECT),
        "source_dir": str(SOURCE_DIR),
        "output_dir": str(OUTPUT_DIR),
        "timestamp": datetime.now().isoformat(),
        "continuity_score": result.overall_consistency_score,
        "total_issues": result.total_issues,
        "frames_processed": result.total_frames,
        "entity_references": result.entity_reference_map,
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n[DONE] Pipeline report saved to {report_path}")
    print(f"Edited frames saved to: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
