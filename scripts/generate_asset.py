#!/usr/bin/env python3
"""
Asset Generator CLI for Arcanomy Motion
Uses OpenAI DALL-E 3 or Google Gemini to generate photorealistic assets.

Usage:
    # Generate from prompt
    python scripts/generate_asset.py --prompt "COMPLETE_PROMPT" --output "renders/images/asset.png"

    # Generate with reference image (for variations)
    python scripts/generate_asset.py --prompt "variation prompt" --reference-image "core.png" --output "variation.png"

    # Create composite (character + environment)
    python scripts/generate_asset.py --character "char.png" --environment "env.png" --output "composite.png"

    # Create vertical split
    python scripts/generate_asset.py --split-vertical "top.png" "bottom.png" --output "split.png"
"""

import argparse
import base64
import json
import os
import sys
from io import BytesIO
from pathlib import Path

import httpx
from dotenv import load_dotenv
from PIL import Image

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import get_default_provider, get_image_model

# Load environment variables
load_dotenv()


def create_composite(character_path: str, environment_path: str, output_path: str, character_scale: float = 1.0):
    """Create composite by overlaying character on environment."""
    # Target 9:16 for vertical reels
    TARGET_WIDTH = 1080
    TARGET_HEIGHT = 1920

    try:
        print(f"Creating composite image...")
        print(f"   Character: {character_path}")
        print(f"   Environment: {environment_path}")

        environment = Image.open(environment_path).convert("RGBA")
        character = Image.open(character_path).convert("RGBA")

        env_width, env_height = environment.size
        char_width, char_height = character.size

        # Resize environment to target dimensions
        env_aspect = env_width / env_height
        target_aspect = TARGET_WIDTH / TARGET_HEIGHT

        if env_aspect > target_aspect:
            # Wider - crop width
            environment = environment.resize(
                (int(env_width * TARGET_HEIGHT / env_height), TARGET_HEIGHT),
                Image.Resampling.LANCZOS
            )
            left = (environment.size[0] - TARGET_WIDTH) // 2
            environment = environment.crop((left, 0, left + TARGET_WIDTH, TARGET_HEIGHT))
        else:
            # Taller - scale and pad
            scale_factor = TARGET_WIDTH / env_width
            new_height = int(env_height * scale_factor)
            environment = environment.resize((TARGET_WIDTH, new_height), Image.Resampling.LANCZOS)

            if new_height < TARGET_HEIGHT:
                padded = Image.new("RGBA", (TARGET_WIDTH, TARGET_HEIGHT), (0, 0, 0, 255))
                y_offset = (TARGET_HEIGHT - new_height) // 2
                padded.paste(environment, (0, y_offset))
                environment = padded
            elif new_height > TARGET_HEIGHT:
                top = (new_height - TARGET_HEIGHT) // 2
                environment = environment.crop((0, top, TARGET_WIDTH, top + TARGET_HEIGHT))

        # Scale character
        if character_scale != 1.0:
            char_width = int(char_width * character_scale)
            char_height = int(char_height * character_scale)
            character = character.resize((char_width, char_height), Image.Resampling.LANCZOS)

        # Center character
        x_offset = (TARGET_WIDTH - char_width) // 2
        y_offset = (TARGET_HEIGHT - char_height) // 2

        composite = environment.copy()
        composite.paste(character, (x_offset, y_offset), character)

        final = Image.new("RGB", composite.size, (0, 0, 0))
        final.paste(composite, mask=composite.split()[3])

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        final.save(output_path, "PNG")
        
        print(f"[OK] Composite saved: {output_path}")
        return True

    except Exception as e:
        print(f"[ERROR] Creating composite: {e}", file=sys.stderr)
        return False


def create_split_vertical(top_path: str, bottom_path: str, output_path: str):
    """Create vertical split composite."""
    try:
        print(f"Creating vertical split...")
        
        top_img = Image.open(top_path).convert("RGB")
        bottom_img = Image.open(bottom_path).convert("RGB")

        top_width, top_height = top_img.size
        bottom_width, bottom_height = bottom_img.size

        final_width = max(top_width, bottom_width)
        final_height = top_height + bottom_height

        final = Image.new("RGB", (final_width, final_height), (0, 0, 0))

        top_x = (final_width - top_width) // 2
        final.paste(top_img, (top_x, 0))

        bottom_x = (final_width - bottom_width) // 2
        final.paste(bottom_img, (bottom_x, top_height))

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        final.save(output_path, "PNG")
        
        print(f"[OK] Split saved: {output_path}")
        return True

    except Exception as e:
        print(f"[ERROR] Creating split: {e}", file=sys.stderr)
        return False


def generate_dalle(prompt: str, output_path: str, size: str = "1024x1792") -> bool:
    """Generate image using OpenAI."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] OPENAI_API_KEY not set", file=sys.stderr)
        return False

    try:
        model_name = get_image_model("openai")
        
        print(f"   [OpenAI] Model: {model_name}")
        print(f"Prompt: {prompt[:100]}...")

        # Truncate if too long
        if len(prompt) > 4000:
            prompt = prompt[:3900] + "..."

        response = httpx.post(
            "https://api.openai.com/v1/images/generations",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_name,
                "prompt": prompt,
                "n": 1,
                "size": size,
                "quality": "hd",
                "response_format": "b64_json",
            },
            timeout=120.0,
        )
        response.raise_for_status()

        data = response.json()
        image_data = data["data"][0]["b64_json"]
        image_bytes = base64.b64decode(image_data)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(image_bytes)

        print(f"[OK] Image saved: {output_path}")
        return True

    except httpx.HTTPStatusError as e:
        print(f"[ERROR] OpenAI Image API error: {e.response.status_code}", file=sys.stderr)
        print(f"   {e.response.text[:200]}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return False


def generate_kie(prompt: str, output_path: str, reference_paths: list = None) -> bool:
    """Generate image using Kie.ai Nano Banana Pro API."""
    import time
    
    api_key = os.getenv("KIE_API_KEY")
    if not api_key:
        print("[ERROR] KIE_API_KEY not set", file=sys.stderr)
        return False
    
    # Strip any smart quotes or whitespace from API key
    api_key = api_key.strip().strip('"').strip('"').strip('"').strip("'").strip("'")

    try:
        # Sanitize prompt - replace smart quotes and other problematic characters
        prompt = prompt.replace('"', '"').replace('"', '"').replace("'", "'").replace("'", "'")
        prompt = prompt.replace('—', '-').replace('–', '-').replace('…', '...')
        
        model_name = get_image_model("kie")
        print(f"   [Kie.ai] Model: {model_name}")
        print(f"Prompt: {prompt[:100]}...")

        # Step 1: Create task
        response = httpx.post(
            "https://api.kie.ai/api/v1/jobs/createTask",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": get_image_model("kie"),
                "input": {
                    "prompt": prompt,
                    "aspect_ratio": "9:16",  # Vertical for reels
                    "resolution": "1K",
                    "output_format": "png"
                }
            },
            timeout=60.0,
        )
        response.raise_for_status()

        data = response.json()
        
        if data.get("code") != 200:
            print(f"[ERROR] Task creation failed: {data.get('msg')}", file=sys.stderr)
            return False
        
        task_id = data.get("data", {}).get("taskId")
        if not task_id:
            print("[ERROR] No taskId in response", file=sys.stderr)
            return False
        
        print(f"Task created: {task_id}")
        
        # Step 2: Poll for result using recordInfo endpoint
        max_attempts = 60  # 5 minutes max
        for attempt in range(max_attempts):
            time.sleep(5)  # Wait 5 seconds between polls
            
            # #region agent log
            import json as _json; open(r"c:\Dev\arcanomy-motion\.cursor\debug.log", "a").write(_json.dumps({"hypothesisId":"kie-poll","location":"generate_asset.py:kie_poll","message":"Polling recordInfo","data":{"task_id":task_id,"attempt":attempt+1},"timestamp":__import__("time").time(),"sessionId":"debug-session"})+"\n")
            # #endregion
            
            # Use recordInfo endpoint with taskId as query param
            status_response = httpx.get(
                "https://api.kie.ai/api/v1/jobs/recordInfo",
                headers={
                    "Authorization": f"Bearer {api_key}",
                },
                params={"taskId": task_id},
                timeout=30.0,
            )
            
            status_response.raise_for_status()
            status_data = status_response.json()
            
            # #region agent log
            import json as _json; open(r"c:\Dev\arcanomy-motion\.cursor\debug.log", "a").write(_json.dumps({"hypothesisId":"kie-response","location":"generate_asset.py:kie_status","message":"recordInfo response","data":{"code":status_data.get("code"),"state":status_data.get("data",{}).get("state")},"timestamp":__import__("time").time(),"sessionId":"debug-session"})+"\n")
            # #endregion
            
            if status_data.get("code") != 200:
                print(f"   Waiting... ({attempt + 1}/{max_attempts})")
                continue
            
            task_info = status_data.get("data", {})
            state = str(task_info.get("state", "")).lower()
            
            # Check state values: waiting, queuing, generating, success, fail
            if state == "success":
                # Parse resultJson string to get URLs
                result_json_str = task_info.get("resultJson", "{}")
                try:
                    result_data = json.loads(result_json_str)
                    result_urls = result_data.get("resultUrls", [])
                    if result_urls:
                        image_url = result_urls[0]
                        # #region agent log
                        import json as _json; open(r"c:\Dev\arcanomy-motion\.cursor\debug.log", "a").write(_json.dumps({"hypothesisId":"kie-success","location":"generate_asset.py:kie_download","message":"Downloading image","data":{"image_url":image_url[:100]},"timestamp":__import__("time").time(),"sessionId":"debug-session"})+"\n")
                        # #endregion
                        img_response = httpx.get(image_url, timeout=60.0)
                        img_response.raise_for_status()
                        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                        Path(output_path).write_bytes(img_response.content)
                        print(f"[OK] Image saved: {output_path}")
                        return True
                    else:
                        print(f"[ERROR] No resultUrls in resultJson", file=sys.stderr)
                        return False
                except json.JSONDecodeError as e:
                    print(f"[ERROR] Failed to parse resultJson: {e}", file=sys.stderr)
                    print(f"resultJson: {result_json_str[:200]}", file=sys.stderr)
                    return False
            
            elif state == "fail":
                fail_msg = task_info.get("failMsg", "Unknown error")
                fail_code = task_info.get("failCode", "")
                print(f"[ERROR] Task failed: {fail_code} - {fail_msg}", file=sys.stderr)
                return False
            
            else:
                # Still processing: waiting, queuing, generating
                print(f"   Waiting... ({attempt + 1}/{max_attempts}) state: {state}")
        
        print("[ERROR] Task timed out", file=sys.stderr)
        return False

    except httpx.HTTPStatusError as e:
        print(f"[ERROR] Kie.ai API error: {e.response.status_code}", file=sys.stderr)
        print(f"   {e.response.text[:500]}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[ERROR] Kie.ai error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


def generate_gemini(prompt: str, output_path: str, reference_paths: list = None) -> bool:
    """Generate image using Google Gemini."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY or GOOGLE_API_KEY not set", file=sys.stderr)
        return False

    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=api_key)
        
        model_name = get_image_model("gemini")

        print(f"   [Gemini] Model: {model_name}")
        print(f"Prompt: {prompt[:100]}...")

        if reference_paths:
            print(f"Using {len(reference_paths)} reference image(s)")
            parts = []
            for p in reference_paths:
                img = Image.open(p)
                img_bytes = BytesIO()
                img.save(img_bytes, format='PNG')
                parts.append(types.Part.from_bytes(data=img_bytes.getvalue(), mime_type="image/png"))
            parts.append(prompt)
            
            response = client.models.generate_content(
                model=model_name,
                contents=parts,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"]
                )
            )
        else:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"]
                )
            )

        if response.candidates:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    image_bytes = part.inline_data.data
                    if isinstance(image_bytes, str):
                        image_bytes = base64.b64decode(image_bytes)
                    
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    Path(output_path).write_bytes(image_bytes)
                    
                    print(f"[OK] Image saved: {output_path}")
                    return True

        print("[ERROR] No image in response", file=sys.stderr)
        return False

    except Exception as e:
        print(f"[ERROR] Gemini error: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Arcanomy Motion Asset Generator")
    
    # Generation mode
    parser.add_argument("--prompt", help="Image generation prompt")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--reference-image", action="append", help="Reference image(s) for variations")
    parser.add_argument(
        "--provider",
        default=get_default_provider("assets"),
        choices=["kie", "gemini", "openai"],
        help="API provider",
    )
    parser.add_argument("--size", default="1024x1792", help="Image size (DALL-E only)")
    
    # Composite mode
    parser.add_argument("--character", help="Character image for composite")
    parser.add_argument("--environment", help="Environment image for composite")
    parser.add_argument("--scale", type=float, default=1.0, help="Character scale factor")
    
    # Split mode
    parser.add_argument("--split-vertical", nargs=2, metavar=("TOP", "BOTTOM"), help="Create vertical split")

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"Arcanomy Motion - Asset Generator")
    print(f"{'='*60}")
    print(f"Output: {args.output}")

    # Determine mode and execute
    if args.split_vertical:
        print(f"Mode: Vertical Split")
        print(f"{'='*60}\n")
        success = create_split_vertical(args.split_vertical[0], args.split_vertical[1], args.output)
    
    elif args.character and args.environment:
        print(f"Mode: Composite")
        print(f"{'='*60}\n")
        success = create_composite(args.character, args.environment, args.output, args.scale)
    
    elif args.character or args.environment:
        print("[ERROR] Both --character and --environment required for composite", file=sys.stderr)
        sys.exit(1)
    
    else:
        if not args.prompt:
            print("[ERROR] --prompt required for generation mode", file=sys.stderr)
            sys.exit(1)
        
        print(f"Mode: Generate ({args.provider})")
        print(f"{'='*60}\n")
        
        if args.provider == "openai":
            success = generate_dalle(args.prompt, args.output, args.size)
        elif args.provider == "kie":
            success = generate_kie(args.prompt, args.output, args.reference_image)
        else:
            success = generate_gemini(args.prompt, args.output, args.reference_image)

    print(f"\n{'='*60}\n")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

