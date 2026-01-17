"""
Test script for Director pipeline prompt tuning.

Runs director + storyboard on limited beats to evaluate prompt quality.
Outputs to tests/image_generation/ for evaluation.

Usage:
    python -m tests.test_director_tuning

After running, check:
- tests/image_generation/prompts.json for prompt quality
- tests/image_generation/generated/ for image output
"""

import asyncio
import json
import shutil
from pathlib import Path
from datetime import datetime

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from greenlight.pipelines.director import DirectorPipeline, build_world_context
from greenlight.pipelines.storyboard import StoryboardPipeline


# Configuration
SOURCE_PROJECT = Path(r"C:\Users\thriv\greenlight_projects\orchid's_gambit")
TEST_OUTPUT = Path(__file__).parent / "image_generation"
NUM_BEATS = 4  # Number of beats to test


def log(msg: str):
    """Simple console logger."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def setup_test_project():
    """Create a minimal test project structure."""
    log("Setting up test project...")

    # Clean previous run
    if TEST_OUTPUT.exists():
        shutil.rmtree(TEST_OUTPUT)

    # Create directories
    TEST_OUTPUT.mkdir(parents=True, exist_ok=True)
    (TEST_OUTPUT / "outlines").mkdir(exist_ok=True)
    (TEST_OUTPUT / "world_bible").mkdir(exist_ok=True)
    (TEST_OUTPUT / "storyboard").mkdir(exist_ok=True)
    (TEST_OUTPUT / "references").mkdir(exist_ok=True)

    # Copy world config (contains character/location definitions)
    src_world = SOURCE_PROJECT / "world_bible" / "world_config.json"
    dst_world = TEST_OUTPUT / "world_bible" / "world_config.json"
    shutil.copy(src_world, dst_world)
    log(f"Copied world_config.json")

    # Copy references directory if it exists
    src_refs = SOURCE_PROJECT / "references"
    if src_refs.exists():
        dst_refs = TEST_OUTPUT / "references"
        if dst_refs.exists():
            shutil.rmtree(dst_refs)
        shutil.copytree(src_refs, dst_refs)
        log(f"Copied references directory")

    # Create limited outline with only NUM_BEATS
    src_outline = SOURCE_PROJECT / "outlines" / "confirmed_outline.json"
    outline_data = json.loads(src_outline.read_text(encoding="utf-8"))

    # Limit beats
    original_beats = outline_data.get("beats", [])
    limited_beats = original_beats[:NUM_BEATS]

    outline_data["beats"] = limited_beats
    outline_data["test_run"] = True
    outline_data["original_beat_count"] = len(original_beats)

    dst_outline = TEST_OUTPUT / "outlines" / "confirmed_outline.json"
    dst_outline.write_text(json.dumps(outline_data, indent=2), encoding="utf-8")
    log(f"Created test outline with {len(limited_beats)} beats (from {len(original_beats)} total)")

    return TEST_OUTPUT


async def run_director(project_path: Path) -> dict:
    """Run the director pipeline."""
    log("="*60)
    log("RUNNING DIRECTOR PIPELINE")
    log("="*60)

    pipeline = DirectorPipeline(
        project_path=project_path,
        llm_model="grok-4-1-fast",
        log_callback=log,
    )

    result = await pipeline.run()

    if result.get("success"):
        log(f"Director complete: {result.get('total_scenes')} scenes, {result.get('total_frames')} frames")
    else:
        log(f"Director FAILED: {result.get('error')}")

    return result


async def run_storyboard(project_path: Path) -> dict:
    """Run the storyboard pipeline."""
    log("="*60)
    log("RUNNING STORYBOARD PIPELINE")
    log("="*60)

    pipeline = StoryboardPipeline(
        project_path=project_path,
        image_model="flux_2_pro",
        log_callback=log,
    )

    result = await pipeline.run()

    if result.get("success"):
        log(f"Storyboard complete: {result.get('completed')} images generated")
    else:
        log(f"Storyboard FAILED: {result.get('error')}")

    return result


def print_prompts_summary(project_path: Path):
    """Print summary of generated prompts for review."""
    prompts_path = project_path / "storyboard" / "prompts.json"
    if not prompts_path.exists():
        log("No prompts.json found")
        return

    prompts = json.loads(prompts_path.read_text(encoding="utf-8"))

    log("="*60)
    log("PROMPTS SUMMARY")
    log("="*60)

    for p in prompts:
        frame_id = p.get("frame_id", "?")
        word_count = p.get("word_count", 0)
        shot_type = p.get("shot_type", "?")
        chars = ", ".join(p.get("characters", []))

        # Check for issues (target is 340-555 words)
        issues = []
        if word_count < 340:
            issues.append(f"!! UNDER 340 WORDS ({word_count})")
        if word_count > 555:
            issues.append(f"OVER 555 WORDS ({word_count})")

        prompt_text = p.get("prompt", "")
        if "center" in prompt_text.lower() and "thirds" not in prompt_text.lower():
            issues.append("POSSIBLY CENTERED")
        if "lattice" in prompt_text.lower() and "obscur" in prompt_text.lower():
            issues.append("MAY OBSCURE FACE")

        status = " | ".join(issues) if issues else "OK"

        log(f"{frame_id} [{shot_type}] - {word_count}w - {chars}")
        log(f"  Status: {status}")
        log(f"  Preview: {prompt_text[:100]}...")
        log("")


def print_world_context_preview(project_path: Path):
    """Show what world context is being sent to the LLM."""
    import sys
    world_path = project_path / "world_bible" / "world_config.json"
    if not world_path.exists():
        return

    world_config = json.loads(world_path.read_text(encoding="utf-8"))
    context = build_world_context(world_config)

    log("="*60)
    log("WORLD CONTEXT BEING SENT TO LLM")
    log("="*60)
    # Handle encoding for Windows console
    try:
        print(context)
    except UnicodeEncodeError:
        # Replace star with ASCII alternative
        print(context.replace("★", "*"))
    log("="*60)


async def main():
    """Main test runner."""
    log("Director Pipeline Tuning Test")
    log(f"Source project: {SOURCE_PROJECT}")
    log(f"Test output: {TEST_OUTPUT}")
    log(f"Testing with {NUM_BEATS} beats")
    log("")

    # Setup
    project_path = setup_test_project()

    # Show world context being sent
    print_world_context_preview(project_path)

    # Run director
    director_result = await run_director(project_path)
    if not director_result.get("success"):
        return

    # Show prompts summary
    print_prompts_summary(project_path)

    # Run storyboard
    storyboard_result = await run_storyboard(project_path)

    # Final summary
    log("="*60)
    log("TEST COMPLETE")
    log("="*60)
    log(f"Output directory: {project_path}")
    log(f"Prompts: {project_path / 'storyboard' / 'prompts.json'}")
    log(f"Images: {project_path / 'storyboard_output' / 'generated'}")
    log("")
    log("Review the prompts and images, then tune staging.py and re-run.")


if __name__ == "__main__":
    asyncio.run(main())
