#!/usr/bin/env python3
"""
Asset Generator CLI for Arcanomy Motion
Uses OpenAI DALL-E 3, Google Gemini, or Kie.ai to generate photorealistic assets.

Usage:
    # Generate from prompt
    python scripts/generate_asset.py --prompt "COMPLETE_PROMPT" --output "renders/images/asset.png"

    # With specific provider
    python scripts/generate_asset.py --prompt "..." --output "..." --provider kie
"""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import get_default_provider, get_image_model

# Load environment variables
load_dotenv()


def generate_dalle(prompt: str, output_path: str, size: str = "1024x1792") -> bool:
    """Generate image using OpenAI DALL-E 3."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] OPENAI_API_KEY not set", file=sys.stderr)
        return False

    try:
        model_name = get_image_model("openai")
        
        print(f"   [OpenAI] Model: {model_name}")
        print(f"   Prompt: {prompt[:100]}...")

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
        print(f"[ERROR] OpenAI API error: {e.response.status_code}", file=sys.stderr)
        print(f"   {e.response.text[:200]}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return False


def generate_kie(prompt: str, output_path: str) -> bool:
    """Generate image using Kie.ai Nano Banana Pro API."""
    api_key = os.getenv("KIE_API_KEY")
    if not api_key:
        print("[ERROR] KIE_API_KEY not set", file=sys.stderr)
        return False
    
    # Strip any smart quotes or whitespace from API key
    api_key = api_key.strip().strip('"').strip('"').strip('"').strip("'").strip("'")

    try:
        # Sanitize prompt
        prompt = prompt.replace('"', '"').replace('"', '"').replace("'", "'").replace("'", "'")
        prompt = prompt.replace('—', '-').replace('–', '-').replace('…', '...')
        
        model_name = get_image_model("kie")
        print(f"   [Kie.ai] Model: {model_name}")
        print(f"   Prompt: {prompt[:100]}...")

        # Step 1: Create task
        response = httpx.post(
            "https://api.kie.ai/api/v1/jobs/createTask",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_name,
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
        
        print(f"   Task created: {task_id}")
        
        # Step 2: Poll for result
        max_attempts = 60  # 5 minutes max
        for attempt in range(max_attempts):
            time.sleep(5)
            
            status_response = httpx.get(
                "https://api.kie.ai/api/v1/jobs/recordInfo",
                headers={"Authorization": f"Bearer {api_key}"},
                params={"taskId": task_id},
                timeout=30.0,
            )
            
            status_response.raise_for_status()
            status_data = status_response.json()
            
            if status_data.get("code") != 200:
                print(f"   Waiting... ({attempt + 1}/{max_attempts})")
                continue
            
            task_info = status_data.get("data", {})
            state = str(task_info.get("state", "")).lower()
            
            if state == "success":
                result_json_str = task_info.get("resultJson", "{}")
                try:
                    result_data = json.loads(result_json_str)
                    result_urls = result_data.get("resultUrls", [])
                    if result_urls:
                        image_url = result_urls[0]
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
                    return False
            
            elif state == "fail":
                fail_msg = task_info.get("failMsg", "Unknown error")
                print(f"[ERROR] Task failed: {fail_msg}", file=sys.stderr)
                return False
            
            else:
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


def generate_gemini(prompt: str, output_path: str) -> bool:
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
        print(f"   Prompt: {prompt[:100]}...")

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
    
    parser.add_argument("--prompt", required=True, help="Image generation prompt")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument(
        "--provider",
        default=get_default_provider("assets"),
        choices=["kie", "gemini", "openai"],
        help="API provider",
    )
    parser.add_argument("--size", default="1024x1792", help="Image size (DALL-E only)")

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"Arcanomy Motion - Asset Generator")
    print(f"{'='*60}")
    print(f"Output: {args.output}")
    print(f"Provider: {args.provider}")
    print(f"{'='*60}\n")

    if args.provider == "openai":
        success = generate_dalle(args.prompt, args.output, args.size)
    elif args.provider == "kie":
        success = generate_kie(args.prompt, args.output)
    else:
        success = generate_gemini(args.prompt, args.output)

    print(f"\n{'='*60}\n")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

