"""
CineStage Director Test - Batched by 5 scenes for consistent prompt length.

Approach:
- Split 15 beats into 3 batches of 5
- Each batch gets its own LLM call
- Consistent 150-250 word prompts throughout
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
import time

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from greenlight.core.llm import LLMClient

# =============================================================================
# CINESTAGE SYSTEM PROMPT (Batch-optimized)
# =============================================================================

CINESTAGE_SYSTEM_PROMPT = """You are CINESTAGE DIRECTOR - transforming story beats into cinematic frames.

## TASK
Convert the provided story beats into a scene graph. ONE scene per beat. 2-4 frames per scene.

## FRAME ID FORMAT
[scene.frame.camera] - Example: [3.2.cB] = Scene 3, Frame 2, Camera B

## CAMERA COVERAGE
- DIALOGUE: Speaker (cA) + Listener reaction (cB)
- ACTION: Main action (cA) + Reaction if needed (cB)
- ESTABLISHING: Single wide shot (cA)
- EMOTIONAL: Close-up single camera (cA)

## SHOT TYPES
EWS=Extreme Wide, WS=Wide, MS=Medium, MCU=Medium Close-Up, CU=Close-Up, ECU=Extreme Close-Up, OTS=Over-shoulder, INS=Insert

## PROMPT REQUIREMENTS (CRITICAL - 200-300 WORDS EACH)

EVERY prompt MUST be 200-300 words. This is MANDATORY. Include ALL of these:

1. CAMERA POSITION relative to subject:
   - "three-quarter from camera right at arm's length"
   - "positioned behind shoulder, looking past toward window"

2. CHARACTER ACTION with micro-tensions:
   - "chin tilted toward lattice, gaze unfocused on distant cypress"
   - "fingertips pressing lacquer sill with weight of held breath"

3. DEPTH LAYERS as artistic chain (foreground → midground → background):
   - "silk cushions occupy lower third in soft focus, rising sharply into focus where jade comb catches morning gold, beyond which paper screens dissolve into cream striations"

4. LIGHTING as active force:
   - "lantern glow pools on lacquered table, catching individual threads in silk collar, throwing the far wall into burnt umber shadow"

5. MATERIAL TEXTURES with wear:
   - "raw silk in ivory, weave visible as crosshatch with imperfections at shoulder seam"
   - "bronze Go stones worn smooth by generations of play"

6. STYLE TAG at end:
   - "; cinematic still, Tang Dynasty China, [lighting], 35mm film grain"

## WARDROBE VISIBILITY BY SHOT
- CU: Face to collar only
- MS: Waist up, arms visible
- WS: Full figure + environment

## OUTPUT FORMAT (JSON)

{
  "scenes": [
    {
      "scene_number": 1,
      "beat": "Original beat text",
      "location": "Location name",
      "time_of_day": "dawn|day|dusk|night",
      "frames": [
        {
          "frame_id": "[1.1.cA]",
          "shot_type": "MS",
          "camera_position": "description of where camera is",
          "prompt": "200-300 word visual poetry prompt ending with style tag",
          "characters": ["Character names"],
          "duration": 3.0
        }
      ]
    }
  ]
}

Output ONLY valid JSON. Each prompt MUST be 200-300 words."""


# =============================================================================
# TEST OUTLINE (15 beats)
# =============================================================================

TEST_BEATS = [
    "Mei watches Lin tend flowers from her bedroom patio at Lu Xian, eyes filled with mystery longing.",
    "Madame Chou reveals Zhoa and Min Zhu as final suitors for Mei's contract, sparking whispers of hidden agendas.",
    "Mei instructs servant girl to deliver sealed note to Lin at florist shop, to open only at evening.",
    "Servant girl slips note to Lin on pressed dirt road, noticing his secretive glance toward Lu Xian.",
    "Zhoa visits Mei, boasting military honors but evading questions about his true affections, planting doubt.",
    "Min Zhu dines at Lu Xian, flaunting wealth while servant overhears hints of his gambling debts.",
    "Mei ponders Lin's dedication, questioning if his gentle touch hides a deeper connection to her past.",
    "Evening falls; Min Zhu enters her room, Go board ready on mahogany table amid tense silence.",
    "Game begins intensely; Min Zhu probes Mei's knowledge of Go masters, revealing his own shadowy training.",
    "Mei pours scented tea over Min Zhu's shoulder, her hair cascading, distracting him with sensual whispers.",
    "Flustered Min Zhu blunders key move; Mei uncovers his hidden bankruptcy through overheard brothel gossip.",
    "Lin reads note at florist shop by lantern light, unveiling his secret noble heritage and love for Mei.",
    "Mei wins Go wager; Min Zhu concedes, stakes clear as freedom matches her savings.",
    "Zhoa storms Lu Xian, exposing Madame Chou's rigged auction favoring Min Zhu's bribes.",
    "Mei reunites with Lin on pressed dirt road, embracing under stars with newfound truths.",
]

# =============================================================================
# WORLD CONTEXT
# =============================================================================

WORLD_CONTEXT = """WORLD CONTEXT:
Period: Tang Dynasty China, 8th century
Clothing: Hanfu silk robes, jade ornaments, embroidered collars
Architecture: Wooden pavilions, paper screens, latticed windows, lacquered furniture
Lighting: Lanterns, candlelight, dawn/dusk natural light
Color Palette: Ivory, jade green, burnt umber, gold accents

CHARACTERS:
- MEI: Courtesan at Lu Xian brothel, pale skin, dark hair with jade pins, melancholic beauty
- LIN: Humble florist, weathered hands, kind eyes, simple cotton robes
- MADAME CHOU: Brothel owner, calculating gaze, elaborate silk robes, jade rings
- MIN ZHU: Wealthy merchant, corpulent, flashy silk, gold jewelry
- ZHOA: Military general, stern face, military uniform, commanding presence
- SERVANT GIRL: Young, plain robes, observant eyes

LOCATIONS:
- LU XIAN BROTHEL: Multi-story wooden building, paper screens, lanterns, courtyard
- MEI'S BEDROOM: Lacquered vanity, silk cushions, latticed window overlooking courtyard
- FLORIST SHOP: Humble wooden structure, flower buckets, pressed dirt floor
- PRESSED DIRT ROAD: Evening lanterns, wooden buildings on sides, distant mountains"""


async def run_batch(llm: LLMClient, beats: list[str], scene_offset: int) -> dict:
    """Process a batch of beats."""
    beats_text = "\n".join([
        f"{scene_offset + i + 1:02d}. {beat}"
        for i, beat in enumerate(beats)
    ])

    user_prompt = f"""Convert these {len(beats)} story beats into scenes (scene numbers {scene_offset + 1}-{scene_offset + len(beats)}).

{WORLD_CONTEXT}

STORY BEATS:
{beats_text}

Generate ONE scene per beat with 2-4 frames each.
CRITICAL: Each frame prompt MUST be 200-300 words of visual poetry.
Output ONLY valid JSON."""

    response = await llm.generate(
        prompt=user_prompt,
        system_prompt=CINESTAGE_SYSTEM_PROMPT,
        max_tokens=16000,
        temperature=0.7,
    )

    # Parse JSON
    if "```json" in response:
        start = response.find("```json") + 7
        end = response.find("```", start)
        if end > start:
            return json.loads(response[start:end].strip())

    start = response.find("{")
    end = response.rfind("}") + 1
    if start >= 0 and end > start:
        return json.loads(response[start:end])

    raise ValueError("Could not parse JSON")


async def run_cinestage_batched_test():
    """Run the batched CineStage director test."""
    print("=" * 60)
    print("CINESTAGE DIRECTOR TEST (BATCHED BY 5)")
    print("=" * 60)
    print(f"Total Beats: {len(TEST_BEATS)}")
    print(f"Batches: 3 (5 scenes each)")
    print(f"Model: Grok 4.1 Fast")
    print("=" * 60)

    llm = LLMClient()
    all_scenes = []
    total_time = 0

    # Process in batches of 5
    batch_size = 5
    batches = [
        TEST_BEATS[i:i + batch_size]
        for i in range(0, len(TEST_BEATS), batch_size)
    ]

    for batch_idx, batch_beats in enumerate(batches):
        scene_offset = batch_idx * batch_size
        print(f"\n[Batch {batch_idx + 1}/3] Processing scenes {scene_offset + 1}-{scene_offset + len(batch_beats)}...")

        start_time = time.time()

        try:
            result = await run_batch(llm, batch_beats, scene_offset)
            elapsed = time.time() - start_time
            total_time += elapsed

            scenes = result.get("scenes", [])
            frame_count = sum(len(s.get("frames", [])) for s in scenes)
            print(f"           -> {len(scenes)} scenes, {frame_count} frames in {elapsed:.1f}s")

            all_scenes.extend(scenes)

        except Exception as e:
            print(f"           -> ERROR: {e}")
            import traceback
            traceback.print_exc()

    # Compile final output
    scene_graph = {
        "title": "Shadows of the Go Board",
        "created_at": datetime.now().isoformat(),
        "pipeline": "cinestage-batched",
        "batch_size": batch_size,
        "total_scenes": len(all_scenes),
        "scenes": all_scenes,
    }

    total_frames = sum(len(s.get("frames", [])) for s in all_scenes)
    scene_graph["total_frames"] = total_frames

    # Analyze prompt lengths
    prompt_lengths = []
    for scene in all_scenes:
        for frame in scene.get("frames", []):
            prompt = frame.get("prompt", "")
            word_count = len(prompt.split())
            prompt_lengths.append(word_count)

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total Scenes: {len(all_scenes)}")
    print(f"Total Frames: {total_frames}")
    print(f"Total Time: {total_time:.1f}s ({total_time/len(TEST_BEATS):.2f}s per beat)")

    if prompt_lengths:
        avg_words = sum(prompt_lengths) / len(prompt_lengths)
        min_words = min(prompt_lengths)
        max_words = max(prompt_lengths)
        print(f"\nPrompt Stats:")
        print(f"  Average: {avg_words:.0f} words")
        print(f"  Range: {min_words}-{max_words} words")

        # Show distribution by batch
        for batch_idx in range(3):
            start = batch_idx * 5 * 3  # ~3 frames per scene
            end = start + 15
            batch_lengths = prompt_lengths[start:min(end, len(prompt_lengths))]
            if batch_lengths:
                batch_avg = sum(batch_lengths) / len(batch_lengths)
                print(f"  Batch {batch_idx + 1}: avg {batch_avg:.0f} words")

    # Save outputs
    output_dir = Path(__file__).parent / "cinestage_output_batched"
    output_dir.mkdir(exist_ok=True)

    # Full scene graph
    sg_path = output_dir / "visual_script.json"
    sg_path.write_text(json.dumps(scene_graph, indent=2), encoding="utf-8")
    print(f"\nSaved: {sg_path}")

    # Extracted prompts (for card UI)
    prompts = []
    for scene in all_scenes:
        for frame in scene.get("frames", []):
            prompts.append({
                "frame_id": frame.get("frame_id", ""),
                "scene_number": scene.get("scene_number", 0),
                "beat": scene.get("beat", "")[:50] + "...",
                "shot_type": frame.get("shot_type", ""),
                "camera_position": frame.get("camera_position", ""),
                "prompt": frame.get("prompt", ""),
                "characters": frame.get("characters", []),
                "word_count": len(frame.get("prompt", "").split()),
                "generated": False,
                "image_url": None,
            })

    prompts_path = output_dir / "prompts.json"
    prompts_path.write_text(json.dumps(prompts, indent=2), encoding="utf-8")
    print(f"Saved: {prompts_path} ({len(prompts)} cards)")

    # Sample output
    if all_scenes and all_scenes[0].get("frames"):
        print("\n" + "-" * 60)
        print("SAMPLE: Scene 1, Frame 1")
        print("-" * 60)
        first_frame = all_scenes[0]["frames"][0]
        print(f"Frame ID: {first_frame.get('frame_id')}")
        print(f"Shot: {first_frame.get('shot_type')}")
        print(f"Camera: {first_frame.get('camera_position')}")
        prompt = first_frame.get("prompt", "")
        print(f"Prompt ({len(prompt.split())} words):\n")
        print(prompt[:600] + "..." if len(prompt) > 600 else prompt)

    # Also show a later scene to verify consistency
    if len(all_scenes) >= 10 and all_scenes[9].get("frames"):
        print("\n" + "-" * 60)
        print("SAMPLE: Scene 10, Frame 1 (verifying consistency)")
        print("-" * 60)
        frame_10 = all_scenes[9]["frames"][0]
        print(f"Frame ID: {frame_10.get('frame_id')}")
        prompt = frame_10.get("prompt", "")
        print(f"Prompt ({len(prompt.split())} words):\n")
        print(prompt[:400] + "..." if len(prompt) > 400 else prompt)

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_cinestage_batched_test())
