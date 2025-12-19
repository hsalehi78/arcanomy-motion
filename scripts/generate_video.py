#!/usr/bin/env python3
"""
Video Generator CLI for Arcanomy Motion
Uses Kling 2.5/2.6 (via Kie.ai) to animate seed images into video clips.

Usage:
    python scripts/generate_video.py \
        --image "renders/images/object_clock_spinning.png" \
        --prompt "Clock face glows in dim light. Second hand ticks forward slowly. Slow push in." \
        --output "renders/videos/clip_01.mp4"

    # With specific provider/model
    python scripts/generate_video.py \
        --image "renders/images/character.png" \
        --prompt "Person breathes slowly. Eyes blink. Slow zoom in." \
        --output "renders/videos/clip_02.mp4" \
        --provider kling-2.5

    # Dry run (save prompt, don't call API)
    python scripts/generate_video.py \
        --image "renders/images/asset.png" \
        --prompt "Motion description..." \
        --output "renders/videos/clip.mp4" \
        --dry-run
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

# Load environment variables
load_dotenv()

# Model mapping for Kie.ai
KLING_MODELS = {
    "kling": "kling/v2-5-turbo-image-to-video-pro",  # Default - fast, 1080p
    "kling-2.5": "kling/v2-5-turbo-image-to-video-pro",
    "kling-2.6": "kling-2.6/image-to-video",  # With native audio
}


def upload_image_to_imgbb(image_path: str) -> str | None:
    """Upload image to imgbb.com for temporary hosting (free, no account needed)."""
    api_key = os.getenv("IMGBB_API_KEY")
    if not api_key:
        print("[WARNING] IMGBB_API_KEY not set, trying catbox.moe...", file=sys.stderr)
        return upload_image_to_catbox(image_path)
    
    try:
        image_bytes = Path(image_path).read_bytes()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        
        response = httpx.post(
            "https://api.imgbb.com/1/upload",
            data={
                "key": api_key,
                "image": image_b64,
                "expiration": 600,  # 10 minutes
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            url = data["data"]["url"]
            print(f"   Image uploaded: {url[:50]}...")
            return url
        else:
            print(f"[ERROR] imgbb upload failed: {data}", file=sys.stderr)
            return None
            
    except Exception as e:
        print(f"[ERROR] imgbb upload error: {e}", file=sys.stderr)
        return None


def upload_image_to_catbox(image_path: str) -> str | None:
    """Upload image to catbox.moe (free, no account needed)."""
    try:
        with open(image_path, "rb") as f:
            response = httpx.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": (Path(image_path).name, f, "image/png")},
                timeout=120.0,
            )
        
        if response.status_code == 200 and response.text.startswith("https://"):
            url = response.text.strip()
            print(f"   Image uploaded: {url}")
            return url
        else:
            print(f"[ERROR] catbox upload failed: {response.text[:200]}", file=sys.stderr)
            return None
            
    except Exception as e:
        print(f"[ERROR] catbox upload error: {e}", file=sys.stderr)
        return None


def generate_kling(
    image_path: str,
    prompt: str,
    output_path: str,
    model: str = "kling/v2-5-turbo-image-to-video-pro",
    duration: str = "10",
    negative_prompt: str = "blur, distort, low quality, morphing, glitch",
    cfg_scale: float = 0.5,
) -> bool:
    """Generate video using Kling via Kie.ai API (Image-to-Video mode)."""
    api_key = os.getenv("KIE_API_KEY")
    if not api_key:
        print("[ERROR] KIE_API_KEY not set", file=sys.stderr)
        return False

    # Strip any smart quotes or whitespace from API key
    api_key = api_key.strip().strip('"').strip('"').strip('"').strip("'").strip("'")

    # Verify image exists
    if not Path(image_path).exists():
        print(f"[ERROR] Image not found: {image_path}", file=sys.stderr)
        return False

    try:
        # Sanitize prompt - replace smart quotes and other problematic characters
        prompt = prompt.replace('"', '"').replace('"', '"').replace("'", "'").replace("'", "'")
        prompt = prompt.replace('—', '-').replace('–', '-').replace('…', '...')

        print(f"Generating video with {model}...")
        print(f"Image: {image_path}")
        print(f"Prompt: {prompt[:100]}...")

        # Step 1: Upload image to get a URL
        print(f"   Uploading image...")
        image_url = upload_image_to_imgbb(image_path)
        if not image_url:
            image_url = upload_image_to_catbox(image_path)
        
        if not image_url:
            print("[ERROR] Failed to upload image for video generation", file=sys.stderr)
            return False

        # Step 2: Create video generation task
        print(f"   Creating video task...")
        payload = {
            "model": model,
            "input": {
                "prompt": prompt,
                "image_url": image_url,
                "duration": duration,
                "negative_prompt": negative_prompt,
                "cfg_scale": cfg_scale,
            }
        }
        response = httpx.post(
            "https://api.kie.ai/api/v1/jobs/createTask",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=120.0,
        )
        response.raise_for_status()

        data = response.json()

        if data.get("code") != 200:
            print(f"[ERROR] Task creation failed: {data.get('message') or data.get('msg')}", file=sys.stderr)
            return False

        task_id = data.get("data", {}).get("taskId")
        if not task_id:
            print("[ERROR] No taskId in response", file=sys.stderr)
            print(f"Response: {data}", file=sys.stderr)
            return False

        print(f"   Task created: {task_id}")

        # Step 3: Poll for result (video generation takes 2-5 min typically)
        max_attempts = 120  # 10 minutes max
        poll_interval = 5  # seconds

        for attempt in range(max_attempts):
            time.sleep(poll_interval)

            # Query task status using: GET /api/v1/jobs/recordInfo?taskId=...
            status_response = httpx.get(
                "https://api.kie.ai/api/v1/jobs/recordInfo",
                headers={
                    "Authorization": f"Bearer {api_key}",
                },
                params={"taskId": task_id},
                timeout=30.0,
            )

            if status_response.status_code == 404:
                # Still processing, continue waiting
                elapsed = (attempt + 1) * poll_interval
                print(f"   Waiting... ({elapsed}s elapsed, max {max_attempts * poll_interval}s)")
                continue

            status_response.raise_for_status()
            status_data = status_response.json()

            if status_data.get("code") != 200:
                # Not ready yet or error
                elapsed = (attempt + 1) * poll_interval
                print(f"   Waiting... ({elapsed}s elapsed)")
                continue

            task_info = status_data.get("data", {})
            state = str(task_info.get("state", "")).lower()

            # Check for success state (Kie.ai uses "success")
            if state == "success":
                # Parse resultJson to get the video URL
                result_json_str = task_info.get("resultJson", "{}")
                try:
                    result_json = json.loads(result_json_str) if isinstance(result_json_str, str) else result_json_str
                except json.JSONDecodeError:
                    result_json = {}
                
                video_url = None
                
                # Try resultUrls array first (from the API docs)
                result_urls = result_json.get("resultUrls", [])
                if result_urls and len(result_urls) > 0:
                    video_url = result_urls[0]
                
                # Fallback: try other field names
                if not video_url:
                    for field in ["video_url", "videoUrl", "url", "video", "result", "output_url"]:
                        if field in result_json:
                            val = result_json[field]
                            if isinstance(val, str) and val.startswith("http"):
                                video_url = val
                                break
                            elif isinstance(val, list) and len(val) > 0:
                                video_url = val[0] if isinstance(val[0], str) else val[0].get("url")
                                break

                # Also check at task_info level
                if not video_url:
                    for field in ["video_url", "videoUrl", "url", "result", "output_url"]:
                        if field in task_info:
                            val = task_info[field]
                            if isinstance(val, str) and val.startswith("http"):
                                video_url = val
                                break

                if video_url:
                    print(f"   Downloading video...")
                    video_response = httpx.get(video_url, timeout=180.0)
                    video_response.raise_for_status()
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    Path(output_path).write_bytes(video_response.content)
                    elapsed = (attempt + 1) * poll_interval
                    print(f"[OK] Video saved: {output_path} ({elapsed}s total)")
                    return True
                else:
                    print(f"[ERROR] No video URL in completed task", file=sys.stderr)
                    print(f"Task data: {json.dumps(task_info, indent=2)}", file=sys.stderr)
                    return False

            elif state == "fail":
                error_msg = task_info.get("failMsg", task_info.get("failCode", "Unknown error"))
                print(f"[ERROR] Task failed: {error_msg}", file=sys.stderr)
                return False

            elif state in ("waiting", "queuing", "generating"):
                # Still processing - show friendly status
                elapsed = (attempt + 1) * poll_interval
                status_msg = {"waiting": "Waiting", "queuing": "In queue", "generating": "Generating"}.get(state, state)
                print(f"   {status_msg}... ({elapsed}s elapsed)")
            else:
                # Unknown state
                elapsed = (attempt + 1) * poll_interval
                print(f"   Waiting... ({elapsed}s elapsed) state: {state}")

        print("[ERROR] Task timed out after 10 minutes", file=sys.stderr)
        return False

    except httpx.HTTPStatusError as e:
        print(f"[ERROR] Kie.ai API error: {e.response.status_code}", file=sys.stderr)
        print(f"   {e.response.text[:500]}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[ERROR] Video generation error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


def generate_runway(
    image_path: str,
    prompt: str,
    output_path: str,
) -> bool:
    """Generate video using Runway Gen-3 (placeholder for future implementation)."""
    api_key = os.getenv("RUNWAY_API_KEY")
    if not api_key:
        print("[ERROR] RUNWAY_API_KEY not set", file=sys.stderr)
        return False

    print("[ERROR] Runway Gen-3 provider not yet implemented", file=sys.stderr)
    print("   Please use --provider kling (default)", file=sys.stderr)
    return False


def dry_run(image_path: str, prompt: str, output_path: str) -> bool:
    """Save prompt to text file without calling API (for testing/debugging)."""
    try:
        # Verify image exists
        if not Path(image_path).exists():
            print(f"[WARNING] Image not found: {image_path}", file=sys.stderr)

        # Save prompt details
        prompt_path = Path(output_path).with_suffix(".prompt.txt")
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(f"# Video Generation Prompt (Dry Run)\n\n")
            f.write(f"Image: {image_path}\n")
            f.write(f"Output: {output_path}\n\n")
            f.write(f"## Motion Prompt:\n{prompt}\n")

        print(f"[DRY RUN] Prompt saved: {prompt_path}")
        return True

    except Exception as e:
        print(f"[ERROR] Dry run failed: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Arcanomy Motion Video Generator - Animate seed images with AI"
    )

    # Required arguments
    parser.add_argument("--image", required=True, help="Path to seed image to animate")
    parser.add_argument("--prompt", required=True, help="Video motion prompt (what happens in the clip)")
    parser.add_argument("--output", required=True, help="Output video file path (.mp4)")

    # Optional arguments
    parser.add_argument(
        "--provider",
        default="kling",
        choices=["kling", "kling-2.5", "kling-2.6", "runway"],
        help="Video generation API provider (default: kling = kling-2.5-turbo)"
    )
    parser.add_argument(
        "--duration",
        default="10",
        choices=["5", "10"],
        help="Video duration in seconds (default: 10)"
    )
    parser.add_argument(
        "--negative-prompt",
        default="blur, distort, low quality, morphing, glitch",
        help="Negative prompt (what to avoid)"
    )
    parser.add_argument(
        "--cfg-scale",
        type=float,
        default=0.5,
        help="CFG scale for generation (0-1, default: 0.5)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Save prompt to file without calling API"
    )

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"Arcanomy Motion - Video Generator")
    print(f"{'='*60}")
    print(f"Image:    {args.image}")
    print(f"Output:   {args.output}")
    print(f"Provider: {args.provider}")
    print(f"Duration: {args.duration}s")
    print(f"{'='*60}\n")

    # Execute based on mode
    if args.dry_run:
        print(f"Mode: Dry Run (no API call)")
        success = dry_run(args.image, args.prompt, args.output)

    elif args.provider in ("kling", "kling-2.5", "kling-2.6"):
        model = KLING_MODELS.get(args.provider, KLING_MODELS["kling"])
        print(f"Mode: Generate ({model})")
        success = generate_kling(
            image_path=args.image,
            prompt=args.prompt,
            output_path=args.output,
            model=model,
            duration=args.duration,
            negative_prompt=args.negative_prompt,
            cfg_scale=args.cfg_scale,
        )

    elif args.provider == "runway":
        print(f"Mode: Generate (Runway Gen-3)")
        success = generate_runway(
            image_path=args.image,
            prompt=args.prompt,
            output_path=args.output,
        )

    else:
        print(f"[ERROR] Unknown provider: {args.provider}", file=sys.stderr)
        success = False

    print(f"\n{'='*60}\n")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
