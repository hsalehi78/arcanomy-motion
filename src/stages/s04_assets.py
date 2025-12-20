"""Stage 3.5: Asset Generation - Generate images from prompts using CLI."""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from src.utils.io import read_file, write_file
from src.config import get_default_provider
from src.utils.paths import (
    images_composites_dir,
    json_path,
    prompt_path,
    videos_dir as reel_videos_dir,
)

# Path to shared prompts directory
PROMPTS_DIR = Path(__file__).parent.parent.parent / "shared" / "prompts"
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"


def run_asset_generation(reel_path: Path, provider: str | None = None, dry_run: bool = False) -> list[dict]:
    """Generate images from the visual plan prompts.

    This is the "dumb script" execution stage that:
    1. Reads 03_visual_plan.output.json
    2. Combines global_atmosphere + each asset's image_prompt
    3. Calls generate_asset.py CLI for each asset
    4. Saves images to renders/images/

    Args:
        reel_path: Path to the reel folder
        provider: "openai" for DALL-E 3, "gemini" for Google Gemini
        dry_run: If True, only save prompts without calling API

    Returns:
        List of generation results
    """
    provider = provider or get_default_provider("assets")
    # Load the visual plan JSON
    visual_plan_path = json_path(reel_path, "03_visual_plan.output.json")
    
    if not visual_plan_path.exists():
        raise FileNotFoundError(
            f"03_visual_plan.output.json not found. Run Stage 3 (uv run plan) first.\n"
            f"Expected: {visual_plan_path}"
        )
    
    with open(visual_plan_path, "r", encoding="utf-8") as f:
        visual_plan = json.load(f)
    
    global_atmosphere = visual_plan.get("global_atmosphere", "")
    assets = visual_plan.get("assets", [])
    
    if not assets:
        raise ValueError(
            "No assets found in 03_visual_plan.output.json. "
            "The visual plan may be incomplete or malformed."
        )
    
    # Create renders directory structure
    images_dir = images_composites_dir(reel_path)
    images_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare execution log
    execution_log = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "reel_folder": reel_path.name,
        "provider": provider,
        "dry_run": dry_run,
        "global_atmosphere": global_atmosphere[:200] + "..." if len(global_atmosphere) > 200 else global_atmosphere,
        "total_assets": len(assets),
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "assets": [],
        "failures": []
    }
    
    # Save input/execution plan
    input_path = prompt_path(reel_path, "03.5_asset_generation.input.md")
    input_content = f"""# Asset Generation Stage Input

## Source File
`03_visual_plan.output.json`

## Provider
{provider} ({"DRY RUN - prompts only" if dry_run else "LIVE - generating images"})

## Global Atmosphere
```
{global_atmosphere}
```

## Assets to Generate ({len(assets)} total)

"""
    for asset in assets:
        input_content += f"""### {asset.get('id', 'unknown')}
- **Name:** {asset.get('name', 'Unknown')}
- **Type:** {asset.get('type', 'unknown')}
- **Segments:** {asset.get('used_in_segments', [])}
- **Filename:** {asset.get('suggested_filename', 'unknown.png')}

"""
    
    input_content += """---

## Execution Plan

For each asset:
1. Combine: global_atmosphere + image_prompt
2. Call: `python scripts/generate_asset.py --prompt "..." --output "..." --provider {provider}`
3. Save to: renders/images/{suggested_filename}
"""
    write_file(input_path, input_content)
    
    # Get the CLI script path
    cli_script = SCRIPTS_DIR / "generate_asset.py"
    if not cli_script.exists():
        raise FileNotFoundError(
            f"generate_asset.py not found at {cli_script}\n"
            "Please ensure scripts/generate_asset.py exists."
        )
    
    # Process each asset
    print(f"\n{'='*60}")
    print(f"Arcanomy Motion - Image Generation")
    print(f"{'='*60}")
    print(f"Reel: {reel_path.name}")
    print(f"Assets: {len(assets)}")
    print(f"Provider: {provider}")
    print(f"{'='*60}\n")
    
    for i, asset in enumerate(assets, 1):
        asset_id = asset.get("id", "unknown")
        image_prompt = asset.get("image_prompt", "")
        suggested_filename = asset.get("suggested_filename", f"{asset_id}.png")
        output_path = images_dir / suggested_filename
        
        # Combine prompts
        full_prompt = f"{global_atmosphere}\n\n{image_prompt}"
        
        print(f"[{i}/{len(assets)}] {asset_id}")
        
        # Check if image already exists
        if output_path.exists():
            print(f"   [SKIP] Already exists")
            execution_log["assets"].append({
                "id": asset_id,
                "status": "exists",
                "path": str(output_path.relative_to(reel_path)),
                "message": "Image already exists, skipping"
            })
            execution_log["skipped"] += 1
            continue
        
        # Save the full prompt for reference
        prompt_file = images_dir / f"{asset_id}_prompt.txt"
        write_file(prompt_file, full_prompt)
        
        if dry_run:
            print(f"   [DRY] Prompt saved")
            execution_log["assets"].append({
                "id": asset_id,
                "status": "dry_run",
                "prompt_file": str(prompt_file.relative_to(reel_path)),
                "prompt_length": len(full_prompt),
                "message": "Dry run - prompt saved, no API call"
            })
            continue
        
        # Call the CLI script
        try:
            cmd = [
                sys.executable,
                str(cli_script),
                "--prompt", full_prompt,
                "--output", str(output_path),
                "--provider", provider,
            ]
            
            # Set encoding for Windows compatibility
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout for async APIs like Kie.ai
                encoding="utf-8",
                env=env,
            )
            
            if result.returncode == 0:
                print(f"   [OK] Generated")
                execution_log["assets"].append({
                    "id": asset_id,
                    "status": "success",
                    "path": str(output_path.relative_to(reel_path)),
                })
                execution_log["successful"] += 1
            else:
                print(f"   [FAIL] {result.stderr[:100]}")
                execution_log["assets"].append({
                    "id": asset_id,
                    "status": "failed",
                    "error": result.stderr[:500],
                })
                execution_log["failures"].append(asset_id)
                execution_log["failed"] += 1
                
        except subprocess.TimeoutExpired:
            print(f"   [TIMEOUT] Timed out after 300s")
            execution_log["assets"].append({
                "id": asset_id,
                "status": "timeout",
                "error": "Generation timed out after 300 seconds",
            })
            execution_log["failures"].append(asset_id)
            execution_log["failed"] += 1
            
        except Exception as e:
            print(f"   [ERROR] {e}")
            execution_log["assets"].append({
                "id": asset_id,
                "status": "error",
                "error": str(e),
            })
            execution_log["failures"].append(asset_id)
            execution_log["failed"] += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Generation Complete")
    print(f"   Successful: {execution_log['successful']}")
    print(f"   Skipped: {execution_log['skipped']}")
    print(f"   Failed: {execution_log['failed']}")
    print(f"{'='*60}\n")
    
    # Save output
    output_json_path = json_path(reel_path, "03.5_asset_generation.output.json")
    write_file(output_json_path, json.dumps(execution_log, indent=2))
    
    return execution_log["assets"]


def run_video_generation(reel_path: Path, provider: str | None = None, dry_run: bool = False) -> list[dict]:
    """Generate video clips from images using motion prompts.

    This is Stage 4.5 - animates static images into 10-second video clips.
    
    Uses 04_video_prompt.output.json as primary source (from Stage 4),
    falls back to 03_visual_plan.output.json if not available.

    Args:
        reel_path: Path to the reel folder
        provider: Video generation provider (kling, kling-2.5, kling-2.6, runway)
        dry_run: If True, only save prompts without calling API

    Returns:
        List of video generation results
    """
    provider = provider or get_default_provider("videos")
    # Try to load video prompts (Stage 4 output) first, fall back to visual plan
    video_prompts_path = json_path(reel_path, "04_video_prompt.output.json")
    visual_plan_path = json_path(reel_path, "03_visual_plan.output.json")
    
    clips = []
    source_file = None
    
    if video_prompts_path.exists():
        source_file = "04_video_prompt.output.json"
        with open(video_prompts_path, "r", encoding="utf-8") as f:
            video_prompts = json.load(f)
        clips = video_prompts.get("clips", [])
    elif visual_plan_path.exists():
        source_file = "03_visual_plan.output.json (fallback)"
        with open(visual_plan_path, "r", encoding="utf-8") as f:
            visual_plan = json.load(f)
        # Convert assets to clips format
        assets = visual_plan.get("assets", [])
        clip_num = 1
        for asset in assets:
            for seg_id in asset.get("used_in_segments", []):
                clips.append({
                    "clip_number": clip_num,
                    "segment_id": seg_id,
                    "seed_image": f"renders/images/composites/{asset.get('suggested_filename', asset.get('id') + '.png')}",
                    "video_prompt": asset.get("motion_prompt", ""),
                    "duration_seconds": 10,
                })
                clip_num += 1
    else:
        raise FileNotFoundError(
            "Neither 04_video_prompt.output.json nor 03_visual_plan.output.json found.\n"
            "Run Stage 3 (uv run plan) and optionally Stage 4 (uv run vidprompt) first."
        )
    
    if not clips:
        raise ValueError("No clips found in source file. The output may be incomplete.")
    
    # Create renders directory structure
    videos_dir = reel_videos_dir(reel_path)
    videos_dir.mkdir(parents=True, exist_ok=True)
    
    # Get the CLI script path
    cli_script = SCRIPTS_DIR / "generate_video.py"
    if not cli_script.exists():
        raise FileNotFoundError(
            f"generate_video.py not found at {cli_script}\n"
            "Please ensure scripts/generate_video.py exists."
        )
    
    execution_log = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "reel_folder": reel_path.name,
        "source_file": source_file,
        "provider": provider,
        "dry_run": dry_run,
        "total_clips": len(clips),
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "clips": [],
        "failures": []
    }
    
    print(f"\n{'='*60}")
    print(f"Arcanomy Motion - Video Generation")
    print(f"{'='*60}")
    print(f"Reel: {reel_path.name}")
    print(f"Source: {source_file}")
    print(f"Clips: {len(clips)}")
    print(f"Provider: {provider}")
    print(f"{'='*60}\n")
    
    # Process each clip
    for clip in clips:
        clip_number = clip.get("clip_number", 0)
        segment_id = clip.get("segment_id", clip_number)
        seed_image_rel = clip.get("seed_image", "")
        video_prompt = clip.get("video_prompt", "")
        duration = str(clip.get("duration_seconds", 10))
        
        # Resolve paths
        seed_image_path = reel_path / seed_image_rel
        output_filename = f"clip_{clip_number:02d}.mp4"
        output_path = videos_dir / output_filename
        
        print(f"[{clip_number}/{len(clips)}] Segment {segment_id}")
        
        clip_entry = {
            "clip_number": clip_number,
            "segment_id": segment_id,
            "seed_image": seed_image_rel,
            "output_path": f"renders/videos/{output_filename}",
            "video_prompt": video_prompt[:200] + "..." if len(video_prompt) > 200 else video_prompt,
        }
        
        # Check if video already exists
        if output_path.exists():
            print(f"   [SKIP] Already exists")
            clip_entry["status"] = "exists"
            clip_entry["message"] = "Video already exists, skipping"
            execution_log["skipped"] += 1
            execution_log["clips"].append(clip_entry)
            continue
        
        # Check if seed image exists
        if not seed_image_path.exists():
            print(f"   [BLOCKED] Seed image missing: {seed_image_rel}")
            clip_entry["status"] = "blocked"
            clip_entry["message"] = f"Seed image not found: {seed_image_rel}. Run `uv run assets` first."
            execution_log["failed"] += 1
            execution_log["failures"].append(clip_number)
            execution_log["clips"].append(clip_entry)
            continue
        
        # Save motion prompt for reference
        prompt_file = videos_dir / f"clip_{clip_number:02d}_prompt.txt"
        write_file(prompt_file, f"# Clip {clip_number} - Segment {segment_id}\n\n{video_prompt}")
        
        if dry_run:
            print(f"   [DRY] Prompt saved")
            clip_entry["status"] = "dry_run"
            clip_entry["message"] = "Dry run - prompt saved, no API call"
            execution_log["clips"].append(clip_entry)
            continue
        
        # Call the CLI script
        try:
            cmd = [
                sys.executable,
                str(cli_script),
                "--image", str(seed_image_path),
                "--prompt", video_prompt,
                "--output", str(output_path),
                "--provider", provider,
                "--duration", duration,
            ]
            
            print(f"   [GEN] Calling Kling API...")
            
            # Set encoding for Windows compatibility
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=900,  # 15 minute timeout (video gen takes 2-5 min)
                encoding="utf-8",
                env=env,
            )
            
            if result.returncode == 0:
                print(f"   [OK] Generated: {output_filename}")
                clip_entry["status"] = "success"
                clip_entry["message"] = "Video generated successfully"
                execution_log["successful"] += 1
            else:
                error_msg = result.stderr[:500] if result.stderr else "Unknown error"
                print(f"   [FAIL] {error_msg[:100]}")
                clip_entry["status"] = "failed"
                clip_entry["error"] = error_msg
                execution_log["failed"] += 1
                execution_log["failures"].append(clip_number)
                
        except subprocess.TimeoutExpired:
            print(f"   [TIMEOUT] Timed out after 15 minutes")
            clip_entry["status"] = "timeout"
            clip_entry["error"] = "Generation timed out after 15 minutes"
            execution_log["failed"] += 1
            execution_log["failures"].append(clip_number)
            
        except Exception as e:
            print(f"   [ERROR] {e}")
            clip_entry["status"] = "error"
            clip_entry["error"] = str(e)
            execution_log["failed"] += 1
            execution_log["failures"].append(clip_number)
        
        execution_log["clips"].append(clip_entry)
    
    # Save execution input log
    input_path = prompt_path(reel_path, "04.5_video_generation.input.md")
    input_content = f"""# Video Generation Stage Input

## Source
- Primary: `04_video_prompt.output.json`
- Fallback: `03_visual_plan.output.json`
- Used: `{source_file}`

## Provider
{provider} ({"DRY RUN" if dry_run else "LIVE"})

## Clips to Generate ({len(clips)} total)

"""
    for clip in clips:
        input_content += f"""### Clip {clip.get('clip_number')} (Segment {clip.get('segment_id')})
- **Seed Image:** {clip.get('seed_image')}
- **Duration:** {clip.get('duration_seconds', 10)}s
- **Prompt:** {clip.get('video_prompt', '')[:200]}...

"""
    write_file(input_path, input_content)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Video Generation Complete")
    print(f"   Successful: {execution_log['successful']}")
    print(f"   Skipped: {execution_log['skipped']}")
    print(f"   Failed: {execution_log['failed']}")
    print(f"{'='*60}\n")
    
    # Save output
    output_json_path = json_path(reel_path, "04.5_video_generation.output.json")
    write_file(output_json_path, json.dumps(execution_log, indent=2))
    
    return execution_log["clips"]
