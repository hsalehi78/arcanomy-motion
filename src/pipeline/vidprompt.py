"""Video Prompt Engineering Stage - LLM refines motion prompts.

Reads visual_plan.json and uses LLM to refine motion prompts for
optimal Kling/Runway video generation results.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.config import get_default_provider
from src.services import LLMService
from src.utils.paths import (
    images_composites_dir,
    video_prompts_path,
    visual_plan_path,
)
from src.utils.logger import get_logger

logger = get_logger()

# Path to system prompt
SYSTEM_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "video_prompt_system.md"


def _load_system_prompt() -> str:
    """Load the video prompt system prompt."""
    if SYSTEM_PROMPT_PATH.exists():
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    
    return """You are a Technical Director for video production.
Refine motion prompts for Kling/Runway video generation.

Key rules:
- Core action FIRST, camera movement LAST
- Plain language, specific elements
- Micro-movements only (10s breathing photographs)
- Exactly ONE camera movement per clip

Output JSON with clips array."""


def generate_video_prompts(
    reel_path: Path,
    *,
    force: bool = False,
    ai: bool = True,
    provider_override: str | None = None,
) -> Path:
    """Generate refined video prompts from visual plan.

    Args:
        reel_path: Path to the reel folder
        force: Overwrite existing video_prompts.json
        ai: Use LLM to refine prompts
        provider_override: Override default LLM provider

    Returns:
        Path to the generated video_prompts.json
    """
    reel_path = Path(reel_path)
    output_path = video_prompts_path(reel_path)

    # Check if already exists
    if output_path.exists() and not force:
        logger.info(f"Video prompts exist: {output_path}")
        return output_path

    # Load visual plan
    vp_path = visual_plan_path(reel_path)
    if not vp_path.exists():
        raise FileNotFoundError(f"Visual plan not found: {vp_path}. Run visual_plan stage first.")

    visual_plan = json.loads(vp_path.read_text(encoding="utf-8"))
    assets = visual_plan.get("assets", [])

    if not assets:
        raise ValueError("No assets found in visual_plan.json")

    # Check which images exist
    images_dir = images_composites_dir(reel_path)
    existing_images = []
    if images_dir.exists():
        existing_images = [f.name for f in images_dir.iterdir() if f.suffix == ".png"]

    if ai:
        video_prompts = _generate_with_ai(
            assets=assets,
            existing_images=existing_images,
            images_dir=images_dir,
            provider_override=provider_override,
        )
    else:
        video_prompts = _generate_placeholder(assets, images_dir)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(video_prompts, indent=2), encoding="utf-8")

    logger.info(f"Video prompts generated: {output_path}")
    logger.info(f"  Clips: {len(video_prompts.get('clips', []))}")

    return output_path


def _generate_with_ai(
    assets: list[dict],
    existing_images: list[str],
    images_dir: Path,
    provider_override: str | None = None,
) -> dict[str, Any]:
    """Generate refined video prompts using LLM."""
    provider = provider_override or get_default_provider("vidprompt")
    llm = LLMService(provider=provider)
    system_prompt = _load_system_prompt()

    user_prompt = f"""# Video Prompt Refinement Request

## Assets from Visual Plan

{_format_assets_for_prompt(assets)}

## Generated Images Available
{chr(10).join(f"- {img}" for img in existing_images) if existing_images else "- No images generated yet"}

---

## Your Task

Refine the motion prompts for optimal Kling/Runway generation:

1. Core action FIRST (what is happening)
2. Specific details (what parts are moving)
3. Environmental context
4. Camera movement LAST

Output JSON:
```json
{{
  "clips": [
    {{
      "clip_number": 1,
      "subsegment_id": "subseg-01",
      "seed_image": "renders/images/composites/subseg-01-asset.png",
      "video_prompt": "Refined prompt with camera at end...",
      "camera_movement": "Slow zoom in",
      "duration_seconds": 10,
      "movement_type": "micro",
      "notes": "Opening shot"
    }}
  ]
}}
```

**Output only valid JSON, no markdown code blocks.**
"""

    logger.info(f"Refining video prompts with {provider}...")

    response = llm.complete_json(
        user_prompt,
        system=system_prompt,
        stage="vidprompt",
    )

    if not isinstance(response, dict):
        raise ValueError(f"LLM returned invalid response type: {type(response)}")

    if "clips" not in response:
        response["clips"] = []

    return response


def _generate_placeholder(assets: list[dict], images_dir: Path) -> dict[str, Any]:
    """Generate placeholder video prompts without AI."""
    clips = []

    for i, asset in enumerate(assets, 1):
        ss_id = asset.get("subsegment_id", f"subseg-{i:02d}")
        filename = asset.get("suggested_filename", f"{ss_id}-asset.png")
        motion_prompt = asset.get("motion_prompt", "Subtle movement. Slow zoom in.")
        camera = asset.get("camera_movement", "Slow zoom in")

        clips.append({
            "clip_number": i,
            "subsegment_id": ss_id,
            "seed_image": f"renders/images/composites/{filename}",
            "video_prompt": motion_prompt,
            "camera_movement": camera,
            "duration_seconds": 10,
            "movement_type": "micro",
            "notes": f"Asset {asset.get('id', i)}",
        })

    return {"clips": clips}


def _format_assets_for_prompt(assets: list[dict]) -> str:
    """Format assets for the LLM prompt."""
    lines = []
    for i, asset in enumerate(assets, 1):
        lines.append(f"""### Asset {i}: {asset.get('id', 'unknown')}
- Subsegment: {asset.get('subsegment_id', 'unknown')}
- Image: {asset.get('suggested_filename', 'unknown.png')}
- Current Motion Prompt: {asset.get('motion_prompt', 'N/A')}
- Camera: {asset.get('camera_movement', 'N/A')}
""")
    return "\n".join(lines)

