"""Asset Generation Stage - Generate images from visual plan prompts.

Reads visual_plan.json and calls image generation APIs (DALL-E, Gemini, Kie.ai)
to create seed images for video generation.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config import get_default_provider, get_image_model
from src.utils.paths import (
    images_composites_dir,
    json_path,
    prompt_path,
    visual_plan_path,
)
from src.utils.logger import get_logger

logger = get_logger()

# Path to the CLI script
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"


def generate_assets(
    reel_path: Path,
    *,
    provider: str | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> list[dict]:
    """Generate images from the visual plan prompts.

    Args:
        reel_path: Path to the reel folder
        provider: Image generation provider (kie, gemini, openai)
        dry_run: If True, only save prompts without calling API
        force: Regenerate even if images exist

    Returns:
        List of generation results
    """
    reel_path = Path(reel_path)
    provider = provider or get_default_provider("assets")

    # Load the visual plan
    vp_path = visual_plan_path(reel_path)
    if not vp_path.exists():
        raise FileNotFoundError(
            f"visual_plan.json not found. Run visual_plan stage first.\n"
            f"Expected: {vp_path}"
        )

    with open(vp_path, "r", encoding="utf-8") as f:
        visual_plan = json.load(f)

    global_atmosphere = visual_plan.get("global_atmosphere", "")
    assets = visual_plan.get("assets", [])

    if not assets:
        logger.warning("No assets found in visual_plan.json")
        return []

    # Create output directory
    images_dir = images_composites_dir(reel_path)
    images_dir.mkdir(parents=True, exist_ok=True)

    # Prepare execution log
    model = get_image_model(provider)
    execution_log: dict[str, Any] = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "reel_folder": reel_path.name,
        "provider": provider,
        "model": model,
        "dry_run": dry_run,
        "global_atmosphere": global_atmosphere[:200] + "..." if len(global_atmosphere) > 200 else global_atmosphere,
        "total_assets": len(assets),
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "assets": [],
        "failures": [],
    }

    # Get CLI script path
    cli_script = SCRIPTS_DIR / "generate_asset.py"
    if not cli_script.exists():
        raise FileNotFoundError(f"generate_asset.py not found at {cli_script}")

    logger.info(f"Generating {len(assets)} assets with {provider} ({model})")
    if dry_run:
        logger.info("DRY RUN - prompts will be saved, no API calls")

    # Process each asset
    for i, asset in enumerate(assets, 1):
        asset_id = asset.get("id", "unknown")
        image_prompt = asset.get("image_prompt", "")
        suggested_filename = asset.get("suggested_filename", f"{asset_id}.png")
        output_path = images_dir / suggested_filename

        # Combine prompts
        full_prompt = f"{global_atmosphere}\n\n{image_prompt}"

        logger.info(f"[{i}/{len(assets)}] {asset_id}")

        # Check if image already exists
        if output_path.exists() and not force:
            logger.info(f"   [SKIP] Already exists")
            execution_log["assets"].append({
                "id": asset_id,
                "status": "exists",
                "path": str(output_path.relative_to(reel_path)),
            })
            execution_log["skipped"] += 1
            continue

        # Save the full prompt for reference
        prompt_file = images_dir / f"{asset_id}_prompt.txt"
        prompt_file.write_text(full_prompt, encoding="utf-8")

        if dry_run:
            logger.info(f"   [DRY] Prompt saved")
            execution_log["assets"].append({
                "id": asset_id,
                "status": "dry_run",
                "prompt_file": str(prompt_file.relative_to(reel_path)),
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

            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                encoding="utf-8",
                env=env,
            )

            if result.returncode == 0:
                logger.info(f"   [OK] Generated")
                execution_log["assets"].append({
                    "id": asset_id,
                    "status": "success",
                    "path": str(output_path.relative_to(reel_path)),
                })
                execution_log["successful"] += 1
            else:
                error = result.stderr[:500] if result.stderr else "Unknown error"
                logger.error(f"   [FAIL] {error[:100]}")
                execution_log["assets"].append({
                    "id": asset_id,
                    "status": "failed",
                    "error": error,
                })
                execution_log["failures"].append(asset_id)
                execution_log["failed"] += 1

        except subprocess.TimeoutExpired:
            logger.error(f"   [TIMEOUT] Timed out after 300s")
            execution_log["assets"].append({
                "id": asset_id,
                "status": "timeout",
                "error": "Generation timed out after 300 seconds",
            })
            execution_log["failures"].append(asset_id)
            execution_log["failed"] += 1

        except Exception as e:
            logger.error(f"   [ERROR] {e}")
            execution_log["assets"].append({
                "id": asset_id,
                "status": "error",
                "error": str(e),
            })
            execution_log["failures"].append(asset_id)
            execution_log["failed"] += 1

    # Summary
    logger.info(f"Generation complete: {execution_log['successful']} successful, "
                f"{execution_log['skipped']} skipped, {execution_log['failed']} failed")

    # Save output log
    output_json = json_path(reel_path, "asset_generation.output.json")
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(execution_log, indent=2), encoding="utf-8")

    return execution_log["assets"]

