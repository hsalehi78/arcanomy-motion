"""Visual Plan Generator - LLM creates image prompts and motion prompts.

Reads plan.json (subsegments with voice scripts) and uses LLM to generate:
1. Image prompts for DALL-E/Gemini/Kie.ai
2. Motion prompts for Kling/Runway video generation
3. Global atmosphere block for visual consistency
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.config import get_default_provider
from src.services import LLMService
from src.utils.paths import (
    claim_json_path,
    plan_path,
    seed_path,
    visual_plan_path,
)
from src.utils.logger import get_logger

logger = get_logger()

# Path to system prompt
SYSTEM_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "visual_plan_system.md"


def _read_file(path: Path) -> str:
    """Read file contents or return empty string if not exists."""
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _read_json(path: Path) -> dict:
    """Read JSON file or return empty dict if not exists."""
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _load_system_prompt() -> str:
    """Load the visual plan system prompt."""
    if SYSTEM_PROMPT_PATH.exists():
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    
    # Fallback if file missing
    return """You are a visual director for short-form video content.
Create image prompts for DALL-E/Midjourney and motion prompts for Kling/Runway.

Output JSON with:
- global_atmosphere: Consistent visual style (100-150 words)
- assets: Array of {id, subsegment_id, image_prompt, motion_prompt, camera_movement, suggested_filename}
"""


def generate_visual_plan(
    reel_path: Path,
    *,
    force: bool = False,
    ai: bool = True,
    provider_override: str | None = None,
) -> Path:
    """Generate visual plan with image and motion prompts.

    Args:
        reel_path: Path to the reel folder
        force: Overwrite existing visual_plan.json
        ai: Use LLM to generate prompts (if False, creates placeholder)
        provider_override: Override default LLM provider

    Returns:
        Path to the generated visual_plan.json
    """
    reel_path = Path(reel_path)
    output_path = visual_plan_path(reel_path)

    # Check if already exists
    if output_path.exists() and not force:
        logger.info(f"Visual plan exists: {output_path}")
        return output_path

    # Load inputs
    plan_file = plan_path(reel_path)
    if not plan_file.exists():
        raise FileNotFoundError(f"Plan not found: {plan_file}. Run plan stage first.")

    plan = _read_json(plan_file)
    seed = _read_file(seed_path(reel_path))
    claim = _read_json(claim_json_path(reel_path))

    subsegments = plan.get("subsegments", [])
    if not subsegments:
        raise ValueError("No subsegments found in plan.json")

    if ai:
        visual_plan = _generate_with_ai(
            subsegments=subsegments,
            seed=seed,
            claim=claim,
            plan=plan,
            provider_override=provider_override,
        )
    else:
        visual_plan = _generate_placeholder(subsegments)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(visual_plan, indent=2), encoding="utf-8")
    
    logger.info(f"Visual plan generated: {output_path}")
    logger.info(f"  Assets: {len(visual_plan.get('assets', []))}")

    return output_path


def _generate_with_ai(
    subsegments: list[dict],
    seed: str,
    claim: dict,
    plan: dict,
    provider_override: str | None = None,
) -> dict[str, Any]:
    """Generate visual plan using LLM."""
    provider = provider_override or get_default_provider("visual_plan")
    llm = LLMService(provider=provider)
    system_prompt = _load_system_prompt()

    # Filter out chart subsegments (they don't need image generation)
    non_chart_subsegments = [
        ss for ss in subsegments
        if not ss.get("charts")
    ]

    user_prompt = f"""# Visual Plan Generation Request

## Claim
{json.dumps(claim, indent=2)}

## Creative Brief (seed.md)
{seed}

## Plan Summary
- Total duration: {plan.get('total_duration_seconds', 50)}s
- Subsegments: {len(subsegments)}

## Subsegments Needing Visual Assets

{_format_subsegments_for_prompt(non_chart_subsegments)}

## Subsegments with Charts (skip image generation for these)
{_format_chart_subsegments(subsegments)}

---

## Your Task

Generate a visual_plan.json with:

1. **global_atmosphere**: A 100-150 word paragraph describing consistent visual style
2. **assets**: One asset per non-chart subsegment with:
   - id: "subseg-XX-asset"
   - subsegment_id: "subseg-XX"
   - name: Descriptive name
   - type: "object" | "character" | "environment"
   - image_prompt: Complete DALL-E/Gemini prompt (include atmosphere)
   - motion_prompt: Kling/Runway motion description (10s breathing photograph)
   - camera_movement: "Slow zoom in" | "Slow push in" | etc.
   - suggested_filename: "subseg-XX-asset.png"

**Output only valid JSON, no markdown code blocks.**
"""

    logger.info(f"Generating visual plan with {provider}...")
    
    response = llm.complete_json(
        user_prompt,
        system=system_prompt,
        stage="visual_plan",
    )

    # Validate response
    if not isinstance(response, dict):
        raise ValueError(f"LLM returned invalid response type: {type(response)}")

    if "assets" not in response:
        response["assets"] = []

    if "global_atmosphere" not in response:
        response["global_atmosphere"] = "Cinematic atmosphere, professional lighting."

    return response


def _generate_placeholder(subsegments: list[dict]) -> dict[str, Any]:
    """Generate placeholder visual plan without AI."""
    assets = []
    
    for ss in subsegments:
        ss_id = ss.get("subsegment_id", "unknown")
        
        # Skip chart subsegments
        if ss.get("charts"):
            continue
        
        assets.append({
            "id": f"{ss_id}-asset",
            "subsegment_id": ss_id,
            "name": f"Asset for {ss_id}",
            "type": "object",
            "image_prompt": f"[PLACEHOLDER] Image for {ss_id}: {ss.get('voice_text', '')[:50]}...",
            "motion_prompt": "[PLACEHOLDER] Subtle movement. Slow zoom in.",
            "camera_movement": "Slow zoom in",
            "suggested_filename": f"{ss_id}-asset.png",
        })

    return {
        "global_atmosphere": "[PLACEHOLDER] Cinematic atmosphere with professional lighting.",
        "assets": assets,
    }


def _format_subsegments_for_prompt(subsegments: list[dict]) -> str:
    """Format subsegments for the LLM prompt."""
    lines = []
    for ss in subsegments:
        ss_id = ss.get("subsegment_id", "unknown")
        voice_text = ss.get("voice_text", "")
        visual_intent = ss.get("visual_intent", "")
        lines.append(f"""### {ss_id}
- Voice: "{voice_text}"
- Visual Intent: {visual_intent}
""")
    return "\n".join(lines) if lines else "(None - all subsegments have charts)"


def _format_chart_subsegments(subsegments: list[dict]) -> str:
    """Format chart subsegments for reference."""
    lines = []
    for ss in subsegments:
        if ss.get("charts"):
            ss_id = ss.get("subsegment_id", "unknown")
            lines.append(f"- {ss_id}: Has chart, skip image generation")
    return "\n".join(lines) if lines else "(None)"

