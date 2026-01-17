"""
Test script for Nano Banana Pro (Gemini 3 Pro Image Preview)
"""

import asyncio
import os
import sys
from pathlib import Path

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Set the API key
os.environ["GEMINI_API_KEY"] = "AIzaSyCXwkYJUoNafQG7sSoyAzrI52pK16pHofY"

async def test_nano_banana():
    """Test Nano Banana Pro image generation."""

    print("=" * 60)
    print("Testing Nano Banana Pro (Gemini 3 Pro Image Preview)")
    print("=" * 60)

    try:
        from google import genai
        from google.genai import types

        print("\n[OK] google-genai SDK imported successfully")

        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        print("[OK] Client created")

        # Test prompt - cinematic storyboard frame
        prompt = """A cinematic wide shot of a lone samurai standing on a misty mountain cliff at dawn.
        The samurai is silhouetted against a dramatic orange and purple sky.
        Cherry blossom petals drift through the air.
        Photorealistic, cinematic lighting, 16:9 aspect ratio, film grain texture."""

        print(f"\n[PROMPT] {prompt[:100]}...")
        print("\n[WAIT] Generating image with gemini-3-pro-image-preview...")

        # Configure for image output
        config = types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
        )

        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=prompt,
            config=config,
        )

        print("[OK] Response received")
        print(f"[DEBUG] Response type: {type(response)}")

        # Check response
        if response.candidates and len(response.candidates) > 0:
            print(f"[OK] Got {len(response.candidates)} candidate(s)")
            candidate = response.candidates[0]
            print(f"[DEBUG] Candidate content type: {type(candidate.content)}")
            print(f"[DEBUG] Number of parts: {len(candidate.content.parts)}")

            for i, part in enumerate(candidate.content.parts):
                print(f"\n  Part {i}:")
                print(f"    Type: {type(part)}")
                print(f"    Dir: {[a for a in dir(part) if not a.startswith('_')]}")

                # Skip thought parts
                if hasattr(part, 'thought') and part.thought:
                    print("    (thinking image - skipped)")
                    continue

                if hasattr(part, 'text') and part.text:
                    print(f"    Text: {part.text[:200]}...")

                if hasattr(part, 'inline_data') and part.inline_data:
                    inline = part.inline_data
                    print(f"    inline_data type: {type(inline)}")
                    print(f"    inline_data dir: {[a for a in dir(inline) if not a.startswith('_')]}")
                    print(f"    mime_type: {inline.mime_type if hasattr(inline, 'mime_type') else 'N/A'}")

                    # Check if data is already bytes or base64 string
                    data = inline.data
                    print(f"    data type: {type(data)}")
                    print(f"    data length: {len(data) if data else 0}")

                    if isinstance(data, bytes):
                        image_data = data
                        print(f"    Data is already bytes")
                    elif isinstance(data, str):
                        import base64
                        image_data = base64.b64decode(data)
                        print(f"    Decoded from base64 string")
                    else:
                        print(f"    Unknown data type!")
                        continue

                    print(f"    Decoded size: {len(image_data)} bytes")
                    print(f"    First 8 bytes (hex): {image_data[:8].hex()}")

                    # Check if it's a valid PNG
                    if image_data[:4] == b'\x89PNG':
                        print("    [OK] Valid PNG!")
                    elif image_data[:3] == b'\xff\xd8\xff':
                        print("    [OK] Valid JPEG!")
                    else:
                        print(f"    [WARN] Unknown format, first 20 bytes: {image_data[:20]}")

                    # Save the image
                    ext = ".png" if image_data[:4] == b'\x89PNG' else ".jpg" if image_data[:3] == b'\xff\xd8\xff' else ".bin"
                    output_path = Path(f"test_nano_banana_output{ext}")
                    with open(output_path, "wb") as f:
                        f.write(image_data)

                    print(f"\n    Saved to {output_path} ({len(image_data)} bytes)")
                    print("\n" + "=" * 60)
                    print("[SUCCESS] Nano Banana Pro is working!")
                    print(f"   Image saved to: {output_path.absolute()}")
                    print("=" * 60)
                    return True

            print("\n[WARN] No image found in any part")
            return False
        else:
            print("[FAIL] No candidates in response")
            if hasattr(response, 'prompt_feedback'):
                print(f"[DEBUG] Prompt feedback: {response.prompt_feedback}")
            return False

    except Exception as e:
        print(f"\n[FAIL] Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_nano_banana())
    exit(0 if result else 1)
