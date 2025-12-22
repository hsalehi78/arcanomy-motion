"""Video Generation Stage - Animate images into video clips.

Reads video_prompts.json (or visual_plan.json fallback) and calls
Kling/Runway APIs to generate 10-second video clips from seed images.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config import get_default_provider, get_video_model
from src.utils.paths import (
    json_path,
    video_prompts_path,
    videos_dir,
    visual_plan_path,
)
from src.utils.logger import get_logger

logger = get_logger()

# Path to the CLI script
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"


def generate_videos(
    reel_path: Path,
    *,
    provider: str | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> list[dict]:
    """Generate video clips from seed images.

    Args:
        reel_path: Path to the reel folder
        provider: Video generation provider (kling, kling-2.5, kling-2.6)
        dry_run: If True, only save prompts without calling API
        force: Regenerate even if videos exist

    Returns:
        List of generation results
    """
    reel_path = Path(reel_path)
    provider = provider or get_default_provider("videos")

    # Try to load video prompts first, fall back to visual plan
    vp_prompts_path = video_prompts_path(reel_path)
    vp_plan_path = visual_plan_path(reel_path)

    clips = []
    source_file = None

    if vp_prompts_path.exists():
        source_file = "video_prompts.json"
        video_prompts = json.loads(vp_prompts_path.read_text(encoding="utf-8"))
        clips = video_prompts.get("clips", [])
    elif vp_plan_path.exists():
        source_file = "visual_plan.json (fallback)"
        visual_plan = json.loads(vp_plan_path.read_text(encoding="utf-8"))
        assets = visual_plan.get("assets", [])
        
        # Convert assets to clips format
        for i, asset in enumerate(assets, 1):
            clips.append({
                "clip_number": i,
                "subsegment_id": asset.get("subsegment_id", f"subseg-{i:02d}"),
                "seed_image": f"renders/images/composites/{asset.get('suggested_filename', f'{asset.get('id', i)}.png')}",
                "video_prompt": asset.get("motion_prompt", ""),
                "duration_seconds": 10,
            })
    else:
        raise FileNotFoundError(
            "Neither video_prompts.json nor visual_plan.json found.\n"
            "Run visual_plan stage first."
        )

    if not clips:
        logger.warning("No clips found in source file")
        return []

    # Create output directory
    vids_dir = videos_dir(reel_path)
    vids_dir.mkdir(parents=True, exist_ok=True)

    # Get CLI script path
    cli_script = SCRIPTS_DIR / "generate_video.py"
    if not cli_script.exists():
        raise FileNotFoundError(f"generate_video.py not found at {cli_script}")

    model = get_video_model(provider)
    execution_log: dict[str, Any] = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "reel_folder": reel_path.name,
        "source_file": source_file,
        "provider": provider,
        "model": model,
        "dry_run": dry_run,
        "total_clips": len(clips),
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "clips": [],
        "failures": [],
    }

    logger.info(f"Generating {len(clips)} videos with {provider} ({model})")
    if dry_run:
        logger.info("DRY RUN - prompts will be saved, no API calls")

    # Process each clip
    for clip in clips:
        clip_number = clip.get("clip_number", 0)
        segment_id = clip.get("subsegment_id", clip_number)
        seed_image_rel = clip.get("seed_image", "")
        video_prompt = clip.get("video_prompt", "")
        duration = str(clip.get("duration_seconds", 10))

        # Resolve paths
        seed_image_path = reel_path / seed_image_rel
        output_filename = f"clip_{clip_number:02d}.mp4"
        output_path = vids_dir / output_filename

        logger.info(f"[{clip_number}/{len(clips)}] {segment_id}")

        clip_entry = {
            "clip_number": clip_number,
            "subsegment_id": segment_id,
            "seed_image": seed_image_rel,
            "output_path": f"renders/videos/{output_filename}",
            "video_prompt": video_prompt[:200] + "..." if len(video_prompt) > 200 else video_prompt,
        }

        # Check if video already exists
        if output_path.exists() and not force:
            logger.info(f"   [SKIP] Already exists")
            clip_entry["status"] = "exists"
            execution_log["skipped"] += 1
            execution_log["clips"].append(clip_entry)
            continue

        # Check if seed image exists
        if not seed_image_path.exists():
            logger.warning(f"   [BLOCKED] Seed image missing: {seed_image_rel}")
            clip_entry["status"] = "blocked"
            clip_entry["message"] = f"Seed image not found. Run assets stage first."
            execution_log["failed"] += 1
            execution_log["failures"].append(clip_number)
            execution_log["clips"].append(clip_entry)
            continue

        # Save motion prompt for reference
        prompt_file = vids_dir / f"clip_{clip_number:02d}_prompt.txt"
        prompt_file.write_text(f"# Clip {clip_number} - {segment_id}\n\n{video_prompt}", encoding="utf-8")

        if dry_run:
            logger.info(f"   [DRY] Prompt saved")
            clip_entry["status"] = "dry_run"
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

            logger.info(f"   [GEN] Calling Kling API...")

            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=900,  # 15 minute timeout
                encoding="utf-8",
                env=env,
            )

            if result.returncode == 0:
                logger.info(f"   [OK] Generated: {output_filename}")
                clip_entry["status"] = "success"
                execution_log["successful"] += 1
            else:
                error = result.stderr[:500] if result.stderr else "Unknown error"
                logger.error(f"   [FAIL] {error[:100]}")
                clip_entry["status"] = "failed"
                clip_entry["error"] = error
                execution_log["failed"] += 1
                execution_log["failures"].append(clip_number)

        except subprocess.TimeoutExpired:
            logger.error(f"   [TIMEOUT] Timed out after 15 minutes")
            clip_entry["status"] = "timeout"
            clip_entry["error"] = "Generation timed out"
            execution_log["failed"] += 1
            execution_log["failures"].append(clip_number)

        except Exception as e:
            logger.error(f"   [ERROR] {e}")
            clip_entry["status"] = "error"
            clip_entry["error"] = str(e)
            execution_log["failed"] += 1
            execution_log["failures"].append(clip_number)

        execution_log["clips"].append(clip_entry)

    # Summary
    logger.info(f"Video generation complete: {execution_log['successful']} successful, "
                f"{execution_log['skipped']} skipped, {execution_log['failed']} failed")

    # Save output log
    output_json = json_path(reel_path, "video_generation.output.json")
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(execution_log, indent=2), encoding="utf-8")

    return execution_log["clips"]

