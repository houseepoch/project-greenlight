"""
CineStage Director Test - Single-pass staging with hybrid visual poetry.

Tests the new approach:
1. All beats → scene graph in ONE LLM call
2. 300-500 word prompts per frame
3. Camera notation: [scene.frame.camera]
4. Output designed for card-based UI (text → flip → image)
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from greenlight.core.llm import LLMClient

# =============================================================================
# CINESTAGE SYSTEM PROMPT (Simplified from CinePro)
# =============================================================================

CINESTAGE_SYSTEM_PROMPT = """You are CINESTAGE DIRECTOR - transforming story beats into cinematic frames.

## TASK
Convert ALL story beats into a scene graph. ONE scene per beat. 2-4 frames per scene.

## FRAME ID FORMAT
[scene.frame.camera] - Example: [3.2.cB] = Scene 3, Frame 2, Camera B

## CAMERA COVERAGE
- DIALOGUE: Speaker (cA) + Listener reaction (cB)
- ACTION: Main action (cA) + Reaction if needed (cB)
- ESTABLISHING: Single wide shot (cA)
- EMOTIONAL: Close-up single camera (cA)

## SHOT TYPES
EWS=Extreme Wide, WS=Wide, MS=Medium, MCU=Medium Close-Up, CU=Close-Up, ECU=Extreme Close-Up, OTS=Over-shoulder, INS=Insert

## PROMPT STYLE (300-500 words per frame)

Write VISUAL POETRY, not metadata. Each prompt must describe:

1. CAMERA POSITION relative to subject:
   - "three-quarter from camera right at arm's length"
   - "positioned behind shoulder, looking past toward window"

2. CHARACTER ACTION with micro-tensions:
   - "chin tilted toward lattice, gaze unfocused on distant cypress"
   - "fingertips pressing lacquer sill with weight of held breath"

3. DEPTH LAYERS as artistic chain:
   - "silk cushions occupy lower third in soft focus, rising sharply into focus where jade comb catches morning gold, beyond which paper screens dissolve into cream striations"

4. LIGHTING as active force:
   - "lantern glow pools on lacquered table, catching individual threads in silk collar, throwing the far wall into burnt umber shadow"

5. MATERIAL TEXTURES with wear:
   - "raw silk in ivory, weave visible as crosshatch with imperfections pulling at shoulder seam"
   - "bronze Go stones worn smooth by generations of play"

6. STYLE TAG at end:
   - "; cinematic still, Tang Dynasty China, [lighting], 35mm film grain"

## WARDROBE VISIBILITY
- CU: Face to collar only
- MS: Waist up, arms visible
- WS: Full figure + environment

## OUTPUT FORMAT

```json
{
  "title": "Story Title",
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
          "prompt": "300-500 word visual poetry prompt ending with style tag",
          "characters": ["Character names"],
          "duration": 3.0
        }
      ]
    }
  ]
}
```

Generate complete scene graph. Output ONLY valid JSON."""


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
# WORLD CONTEXT (simplified for test)
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


async def run_cinestage_test():
    """Run the CineStage director test."""
    print("=" * 60)
    print("CINESTAGE DIRECTOR TEST")
    print("=" * 60)
    print(f"Beats: {len(TEST_BEATS)}")
    print(f"Model: Grok 4.1 Fast")
    print("=" * 60)

    # Build prompt
    beats_text = "\n".join([f"{i+1:02d}. {beat}" for i, beat in enumerate(TEST_BEATS)])

    user_prompt = f"""Convert these {len(TEST_BEATS)} story beats into a complete scene graph.

{WORLD_CONTEXT}

STORY BEATS:
{beats_text}

Generate ONE scene per beat with 2-4 frames each.
Each frame prompt should be 300-500 words of visual poetry.
Follow camera coverage rules (dialogue needs speaker + listener shots).
Output ONLY valid JSON."""

    print("\n[1/3] Sending to LLM...")
    start_time = asyncio.get_event_loop().time()

    llm = LLMClient()

    try:
        response = await llm.generate(
            prompt=user_prompt,
            system_prompt=CINESTAGE_SYSTEM_PROMPT,
            max_tokens=32000,  # Large output expected
            temperature=0.7,
        )

        elapsed = asyncio.get_event_loop().time() - start_time
        print(f"[2/3] Response received in {elapsed:.1f}s")
        print(f"      Response length: {len(response)} chars")

        # Parse JSON
        scene_graph = None

        # Try JSON block
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            if end > start:
                try:
                    scene_graph = json.loads(response[start:end].strip())
                except json.JSONDecodeError as e:
                    print(f"      JSON block parse failed: {e}")

        # Try raw JSON
        if not scene_graph:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    scene_graph = json.loads(response[start:end])
                except json.JSONDecodeError as e:
                    print(f"      Raw JSON parse failed: {e}")

        if not scene_graph:
            print("[ERROR] Could not parse response as JSON")
            # Save raw response for debugging
            debug_path = Path(__file__).parent / "cinestage_raw_response.txt"
            debug_path.write_text(response, encoding="utf-8")
            print(f"      Raw response saved to: {debug_path}")
            return

        # Analyze output
        scenes = scene_graph.get("scenes", [])
        total_frames = sum(len(s.get("frames", [])) for s in scenes)

        print(f"\n[3/3] RESULTS:")
        print(f"      Title: {scene_graph.get('title', 'Untitled')}")
        print(f"      Scenes: {len(scenes)}")
        print(f"      Total Frames: {total_frames}")
        print(f"      Time: {elapsed:.1f}s ({elapsed/len(TEST_BEATS):.2f}s per beat)")

        # Analyze prompt lengths
        prompt_lengths = []
        for scene in scenes:
            for frame in scene.get("frames", []):
                prompt = frame.get("prompt", "")
                word_count = len(prompt.split())
                prompt_lengths.append(word_count)

        if prompt_lengths:
            avg_words = sum(prompt_lengths) / len(prompt_lengths)
            min_words = min(prompt_lengths)
            max_words = max(prompt_lengths)
            print(f"\n      Prompt Stats:")
            print(f"        Average: {avg_words:.0f} words")
            print(f"        Range: {min_words}-{max_words} words")

        # Save outputs
        output_dir = Path(__file__).parent / "cinestage_output"
        output_dir.mkdir(exist_ok=True)

        # Full scene graph
        sg_path = output_dir / "visual_script.json"
        sg_path.write_text(json.dumps(scene_graph, indent=2), encoding="utf-8")
        print(f"\n      Saved: {sg_path}")

        # Extracted prompts (for card UI)
        prompts = []
        for scene in scenes:
            for frame in scene.get("frames", []):
                prompts.append({
                    "frame_id": frame.get("frame_id", ""),
                    "scene_number": scene.get("scene_number", 0),
                    "beat": scene.get("beat", "")[:50] + "...",
                    "shot_type": frame.get("shot_type", ""),
                    "prompt": frame.get("prompt", ""),
                    "characters": frame.get("characters", []),
                    "word_count": len(frame.get("prompt", "").split()),
                    "generated": False,  # For UI: flip card to show image when True
                    "image_url": None,
                })

        prompts_path = output_dir / "prompts.json"
        prompts_path.write_text(json.dumps(prompts, indent=2), encoding="utf-8")
        print(f"      Saved: {prompts_path} ({len(prompts)} cards)")

        # Markdown preview
        md_lines = [f"# {scene_graph.get('title', 'Visual Script')}\n"]
        md_lines.append(f"**Generated:** {datetime.now().isoformat()}")
        md_lines.append(f"**Pipeline:** CineStage (single-pass)")
        md_lines.append(f"**Time:** {elapsed:.1f}s for {len(TEST_BEATS)} beats\n")
        md_lines.append("---\n")

        for scene in scenes[:3]:  # First 3 scenes as preview
            md_lines.append(f"\n## Scene {scene.get('scene_number', '?')}")
            md_lines.append(f"*{scene.get('beat', '')}*\n")
            md_lines.append(f"**Location:** {scene.get('location', '?')} | **Time:** {scene.get('time_of_day', '?')}\n")

            for frame in scene.get("frames", []):
                md_lines.append(f"### {frame.get('frame_id', '?')} [{frame.get('shot_type', '?')}]")
                md_lines.append(f"*Camera: {frame.get('camera_position', 'N/A')}*\n")

                prompt = frame.get("prompt", "")
                # Show first 300 chars
                preview = prompt[:300] + "..." if len(prompt) > 300 else prompt
                md_lines.append(f"> {preview}\n")
                md_lines.append(f"**Words:** {len(prompt.split())} | **Characters:** {', '.join(frame.get('characters', []))}\n")

        md_lines.append("\n---\n*[Showing first 3 scenes. See visual_script.json for complete output]*")

        md_path = output_dir / "preview.md"
        md_path.write_text("\n".join(md_lines), encoding="utf-8")
        print(f"      Saved: {md_path}")

        print("\n" + "=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)

        # Show first scene as sample
        if scenes:
            print("\n--- SAMPLE OUTPUT (Scene 1, Frame 1) ---\n")
            first_frame = scenes[0].get("frames", [{}])[0]
            print(f"Frame ID: {first_frame.get('frame_id', 'N/A')}")
            print(f"Shot Type: {first_frame.get('shot_type', 'N/A')}")
            print(f"Camera: {first_frame.get('camera_position', 'N/A')}")
            print(f"\nPrompt ({len(first_frame.get('prompt', '').split())} words):")
            print("-" * 40)
            print(first_frame.get("prompt", "No prompt")[:500] + "...")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_cinestage_test())
