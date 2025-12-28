"""Visual Plan Generator - LLM creates image prompts and motion prompts.

Reads plan.json (subsegments with voice scripts) and uses LLM to generate:
1. Image prompts for DALL-E/Gemini/Kie.ai
2. Motion prompts for Kling/Runway video generation
3. Global atmosphere block for visual consistency

OUTPUT: Self-contained visual_plan.json with all context needed for asset generation.
No downstream stage should need to reference plan.json.
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

    # Extract reel metadata for self-contained output
    reel_meta = plan.get("reel", {})

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

    # Enrich with metadata and chart subsegments
    visual_plan = _enrich_visual_plan(visual_plan, subsegments, reel_meta)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(visual_plan, indent=2), encoding="utf-8")
    
    logger.info(f"Visual plan generated: {output_path}")
    logger.info(f"  Assets: {len(visual_plan.get('assets', []))}")
    
    # Count by type
    image_count = len([a for a in visual_plan.get('assets', []) if a.get('type') != 'chart'])
    chart_count = len([a for a in visual_plan.get('assets', []) if a.get('type') == 'chart'])
    logger.info(f"  Images: {image_count}, Charts: {chart_count}")

    return output_path


def _enrich_visual_plan(
    visual_plan: dict[str, Any],
    subsegments: list[dict],
    reel_meta: dict,
) -> dict[str, Any]:
    """Enrich visual plan with metadata and chart subsegments.
    
    Makes visual_plan.json self-contained by:
    1. Adding reel metadata
    2. Adding duration/voice_text/visual_intent to each asset
    3. Adding chart subsegments that LLM skipped
    """
    # Build subsegment lookup
    ss_lookup = {ss.get("subsegment_id"): ss for ss in subsegments}
    
    # Add reel-level metadata
    visual_plan["reel_id"] = reel_meta.get("reel_id", "unknown")
    visual_plan["total_duration_seconds"] = reel_meta.get("duration_seconds", 50.0)
    
    # Track which subsegments have assets
    covered_ss_ids = {a.get("subsegment_id") for a in visual_plan.get("assets", [])}
    
    # Enrich existing assets with subsegment context
    enriched_assets = []
    for asset in visual_plan.get("assets", []):
        ss_id = asset.get("subsegment_id")
        ss = ss_lookup.get(ss_id, {})
        
        # Add self-contained fields
        asset["beat"] = ss.get("beat", "unknown")
        asset["duration_seconds"] = ss.get("duration_seconds", 10.0)
        asset["voice_text"] = ss.get("voice", {}).get("text", "") if isinstance(ss.get("voice"), dict) else ""
        asset["visual_intent"] = ss.get("visual", {}).get("intent", "") if isinstance(ss.get("visual"), dict) else ""
        asset["on_screen_text"] = ss.get("visual", {}).get("on_screen_text", "") if isinstance(ss.get("visual"), dict) else ""
        
        # Normalize type for non-chart assets
        if asset.get("type") not in ("chart",):
            asset["type"] = "image"  # Normalize to "image" for clarity
        
        enriched_assets.append(asset)
    
    # Add chart subsegments that were skipped by LLM
    for ss in subsegments:
        ss_id = ss.get("subsegment_id")
        charts = ss.get("charts", [])
        
        if charts and ss_id not in covered_ss_ids:
            # This is a chart subsegment - add it
            chart = charts[0] if charts else {}
            chart_id = chart.get("chart_id", ss.get("chart_id", f"{ss_id}-chart"))
            
            chart_asset = {
                "id": f"{ss_id}-chart",
                "subsegment_id": ss_id,
                "name": f"Chart: {chart_id}",
                "type": "chart",
                "beat": ss.get("beat", "unknown"),
                "duration_seconds": ss.get("duration_seconds", 10.0),
                "voice_text": ss.get("voice", {}).get("text", "") if isinstance(ss.get("voice"), dict) else "",
                "visual_intent": ss.get("visual", {}).get("intent", "") if isinstance(ss.get("visual"), dict) else "",
                "on_screen_text": ss.get("visual", {}).get("on_screen_text", "") if isinstance(ss.get("visual"), dict) else "",
                "chart_id": chart_id,
                "chart_props": chart.get("props", {}),
                "image_prompt": None,
                "motion_prompt": None,
                "camera_movement": None,
                "suggested_filename": f"{chart_id}.mp4",
            }
            enriched_assets.append(chart_asset)
    
    # Sort assets by subsegment order
    ss_order = {ss.get("subsegment_id"): i for i, ss in enumerate(subsegments)}
    enriched_assets.sort(key=lambda a: ss_order.get(a.get("subsegment_id"), 999))
    
    visual_plan["assets"] = enriched_assets
    return visual_plan


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

    # Filter out chart subsegments (LLM only generates image prompts)
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
- Total duration: {plan.get('reel', {}).get('duration_seconds', 50)}s
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
        voice_text = ss.get("voice", {}).get("text", "") if isinstance(ss.get("voice"), dict) else ""
        
        # Skip chart subsegments (they'll be added by _enrich_visual_plan)
        if ss.get("charts"):
            continue
        
        assets.append({
            "id": f"{ss_id}-asset",
            "subsegment_id": ss_id,
            "name": f"Asset for {ss_id}",
            "type": "image",
            "image_prompt": f"[PLACEHOLDER] Image for {ss_id}: {voice_text[:50]}...",
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
        voice_text = ss.get("voice", {}).get("text", "") if isinstance(ss.get("voice"), dict) else ""
        visual_intent = ss.get("visual", {}).get("intent", "") if isinstance(ss.get("visual"), dict) else ""
        duration = ss.get("duration_seconds", 10.0)
        beat = ss.get("beat", "unknown")
        lines.append(f"""### {ss_id} ({beat}, {duration}s)
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
            chart_id = ss.get("chart_id", "unknown")
            lines.append(f"- {ss_id}: Has chart ({chart_id}), skip image generation")
    return "\n".join(lines) if lines else "(None)"
