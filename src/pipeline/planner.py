"""Plan generator - LLM-powered segment/subsegment planning.

Reads seed.md + claim.json (+ optional chart.json) and uses LLM to generate
a production-ready plan.json with voice scripts, chart assignments, and structure.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from src.config import get_default_provider
from src.services import LLMService
from src.utils.paths import (
    chart_json_path,
    claim_json_path,
    ensure_pipeline_layout,
    plan_path,
    provenance_path,
    seed_path,
)
from src.pipeline.provenance import build_provenance, RunContext, write_json_immutable
from src.utils.logger import get_logger

logger = get_logger()

AuditLevel = Literal["basic", "strict"]

# Path to system prompt
SYSTEM_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "plan_system.md"


@dataclass(frozen=True)
class ClaimInput:
    claim_id: str
    claim_text: str
    supporting_data_ref: str
    audit_level: AuditLevel
    tags: list[str] | None = None
    risk_notes: str | None = None
    thumbnail_text: str | None = None


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def _parse_claim(obj: dict[str, Any]) -> ClaimInput:
    missing = [k for k in ("claim_id", "claim_text", "supporting_data_ref", "audit_level") if k not in obj]
    if missing:
        raise ValueError(f"claim.json missing required fields: {', '.join(missing)}")

    audit_level = obj["audit_level"]
    if audit_level not in ("basic", "strict"):
        raise ValueError("claim.json.audit_level must be 'basic' or 'strict'")

    tags = obj.get("tags")
    if tags is not None and not isinstance(tags, list):
        raise ValueError("claim.json.tags must be a list of strings if provided")

    return ClaimInput(
        claim_id=str(obj["claim_id"]),
        claim_text=str(obj["claim_text"]).strip(),
        supporting_data_ref=str(obj["supporting_data_ref"]),
        audit_level=audit_level,  # type: ignore[assignment]
        tags=[str(t) for t in tags] if tags else None,
        risk_notes=str(obj["risk_notes"]).strip() if obj.get("risk_notes") else None,
        thumbnail_text=str(obj["thumbnail_text"]).strip() if obj.get("thumbnail_text") else None,
    )


def _load_system_prompt() -> str:
    """Load the plan system prompt from file."""
    if not SYSTEM_PROMPT_PATH.exists():
        raise FileNotFoundError(f"System prompt not found: {SYSTEM_PROMPT_PATH}")
    return _read_text(SYSTEM_PROMPT_PATH)


def _build_user_prompt(
    claim: ClaimInput,
    seed_content: str,
    chart_props: dict[str, Any] | None = None,
) -> str:
    """Build the user prompt for plan generation."""
    parts = []
    
    # Claim section
    parts.append("## CLAIM.JSON")
    parts.append(f"claim_id: {claim.claim_id}")
    parts.append(f"claim_text: {claim.claim_text}")
    parts.append(f"audit_level: {claim.audit_level}")
    if claim.tags:
        parts.append(f"tags: {', '.join(claim.tags)}")
    parts.append("")
    
    # Seed section
    parts.append("## SEED.MD")
    parts.append(seed_content)
    parts.append("")
    
    # Chart section
    if chart_props:
        parts.append("## CHART.JSON (Assign to subseg-02)")
        parts.append(f"chartType: {chart_props.get('chartType', 'bar')}")
        data = chart_props.get("data", [])
        if data:
            parts.append("data:")
            for item in data:
                if isinstance(item, dict):
                    label = item.get("label", "?")
                    value = item.get("value", 0)
                    parts.append(f"  - {label}: {value}")
        narrative = chart_props.get("_narrative")
        if narrative:
            parts.append(f"narrative: {narrative}")
        parts.append("")
        parts.append("IMPORTANT: Assign this chart to subseg-02 (the evidence/proof segment).")
    else:
        parts.append("## CHART.JSON")
        parts.append("No chart provided. This is a text-only reel.")
    
    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append("Generate the plan.json following the system prompt instructions.")
    parts.append("Return ONLY valid JSON, no markdown code blocks.")
    
    return "\n".join(parts)


def _zoom_plan_for(duration_seconds: float) -> list[dict[str, float]]:
    """Deterministic 3-zoom schedule."""
    t1 = round(duration_seconds * 0.15, 1)
    t2 = round(duration_seconds * 0.45, 1)
    t3 = round(duration_seconds * 0.75, 1)
    t1 = max(0.1, min(duration_seconds - 0.1, t1))
    t2 = max(t1 + 0.1, min(duration_seconds - 0.1, t2))
    t3 = max(t2 + 0.1, min(duration_seconds - 0.1, t3))
    return [{"at_seconds": t1}, {"at_seconds": t2}, {"at_seconds": t3}]


def _enrich_plan(
    llm_plan: dict[str, Any],
    claim: ClaimInput,
    chart_props: dict[str, Any] | None,
    reel_path: Path,
) -> dict[str, Any]:
    """Enrich LLM-generated plan with additional metadata."""
    
    subsegments = llm_plan.get("subsegments", [])
    segments = llm_plan.get("segments", [])
    
    # Ensure subsegment structure is complete
    for ss in subsegments:
        ss.setdefault("duration_seconds", 10.0)
        ss.setdefault("overlays", [{"type": "emotional", "ref": "emoji:money_mouth"}])
        ss.setdefault("charts", [])
        
        # Ensure visual structure
        if "visual" not in ss:
            ss["visual"] = {"type": "still", "source": "library", "prompt_ref": None}
        elif isinstance(ss["visual"], dict):
            ss["visual"].setdefault("source", "library")
            ss["visual"].setdefault("prompt_ref", None)
        
        # If this subsegment has a chart assignment, add it
        if ss.get("chart_id") and chart_props:
            ss["charts"] = [{
                "chart_id": ss["chart_id"],
                "props": chart_props,
            }]
            # Add informational overlay
            if not any(o.get("type") == "informational" for o in ss.get("overlays", [])):
                ss.setdefault("overlays", [])
                ss["overlays"].append({"type": "informational", "ref": f"chart:{ss['chart_id']}"})
    
    # Ensure segment structure is complete
    for seg in segments:
        seg.setdefault("zoom_plan", _zoom_plan_for(seg.get("duration_seconds", 10.0)))
        seg.setdefault("sound_reset", {"sfx_id": "tap_01", "at_seconds": 0.0})
    
    # Build final plan structure
    plan = {
        "version": "2.1",
        "reel": {
            "reel_id": reel_path.name,
            "claim_id": claim.claim_id,
            "subsegment_count": len(subsegments),
            "duration_seconds": sum(ss.get("duration_seconds", 10.0) for ss in subsegments),
            "audit_level": claim.audit_level,
        },
        "inputs": {
            "claim": {
                "claim_id": claim.claim_id,
                "claim_text": claim.claim_text,
                "supporting_data_ref": claim.supporting_data_ref,
                "audit_level": claim.audit_level,
                "tags": claim.tags or [],
                "risk_notes": claim.risk_notes,
                "thumbnail_text": claim.thumbnail_text,
            },
        },
        "segments": segments,
        "subsegments": subsegments,
        "script": {
            "ai_generated": True,
            "title": llm_plan.get("title", "Untitled"),
            "total_word_count": sum(ss.get("word_count", 0) for ss in subsegments),
        },
        "notes": {
            "phase": "2",
            "ai_mode": True,
        },
    }
    
    return plan


def generate_plan(
    reel_path: Path,
    *,
    force: bool = False,
    ai: bool = True,  # Now defaults to True - we always use AI
    ai_provider: str | None = None,
) -> Path:
    """Generate `meta/plan.json` using LLM.

    Reads seed.md + claim.json (+ optional chart.json) and uses AI to generate
    a production-ready plan with voice scripts and structure.
    
    Args:
        reel_path: Path to the reel folder
        force: Allow overwriting existing plan.json
        ai: If True, use LLM (default). If False, use minimal placeholders.
        ai_provider: Override LLM provider (default: config default for 'plan')
    """
    reel_path = Path(reel_path)
    ensure_pipeline_layout(reel_path)

    # Create provenance if it doesn't exist
    prov_file = provenance_path(reel_path)
    if not prov_file.exists():
        claim_file_for_prov = claim_json_path(reel_path)
        chart_file_for_prov = chart_json_path(reel_path)
        prov_payload = build_provenance(
            reel_path=reel_path,
            claim_path=claim_file_for_prov if claim_file_for_prov.exists() else None,
            chart_path=chart_file_for_prov if chart_file_for_prov.exists() else None,
            ctx=RunContext(mode="pipeline", fresh=False, force=force),
        )
        write_json_immutable(prov_file, prov_payload, force=False)
        logger.info(f"[Plan] Created provenance.json")

    # Load inputs
    claim_file = claim_json_path(reel_path)
    seed_file = seed_path(reel_path)
    chart_file = chart_json_path(reel_path)
    
    if not claim_file.exists():
        raise FileNotFoundError(f"Missing required input: {claim_file}")
    
    claim = _parse_claim(_read_json(claim_file))
    
    # Load seed.md (required for AI mode)
    seed_content = ""
    if seed_file.exists():
        seed_content = _read_text(seed_file)
        logger.info(f"[Plan] Loaded seed.md ({len(seed_content)} chars)")
    elif ai:
        logger.warning(f"[Plan] seed.md not found, using claim text only")
        seed_content = f"# Hook\n{claim.claim_text}\n"
    
    # Load chart.json (optional)
    chart_props = None
    if chart_file.exists():
        chart_props = _read_json(chart_file)
        logger.info(f"[Plan] Loaded chart.json ({chart_props.get('chartType', 'unknown')} chart)")
    
    if ai:
        # Load system prompt
        system_prompt = _load_system_prompt()
        logger.info(f"[Plan] Using AI mode with system prompt")
        
        # Build user prompt
        user_prompt = _build_user_prompt(claim, seed_content, chart_props)
        
        # Get LLM provider
        provider = ai_provider or get_default_provider("plan")
        llm = LLMService(provider=provider)
        
        logger.info(f"[Plan] Calling {provider} for plan generation...")
        
        try:
            llm_plan = llm.complete_json(
                prompt=user_prompt,
                system=system_prompt,
                stage="plan",
            )
            logger.info(f"[Plan] LLM generated plan: '{llm_plan.get('title', 'Untitled')}'")
        except Exception as e:
            logger.error(f"[Plan] LLM call failed: {e}")
            raise
        
        # Enrich with metadata
        plan = _enrich_plan(llm_plan, claim, chart_props, reel_path)
        
    else:
        # Fallback: minimal deterministic plan (for testing without API)
        logger.info("[Plan] Using deterministic fallback (no AI)")
        plan = _generate_fallback_plan(claim, chart_props, reel_path)
    
    # Write plan
    out = plan_path(reel_path)
    write_json_immutable(out, plan, force=force)
    return out


def _generate_fallback_plan(
    claim: ClaimInput,
    chart_props: dict[str, Any] | None,
    reel_path: Path,
) -> dict[str, Any]:
    """Generate a minimal fallback plan without AI."""
    
    subsegment_ids = [f"subseg-{i:02d}" for i in range(1, 6)]
    
    # Minimal voice text placeholders
    voice_text = {
        subsegment_ids[0]: claim.claim_text,
        subsegment_ids[1]: "Here's the proof.",
        subsegment_ids[2]: "And why it matters.",
        subsegment_ids[3]: "The hidden cost is time.",
        subsegment_ids[4]: "Decide. Then move.",
    }
    
    subsegments = []
    for i, sid in enumerate(subsegment_ids):
        ss = {
            "subsegment_id": sid,
            "duration_seconds": 10.0,
            "voice": {"text": voice_text[sid]},
            "visual": {"type": "still", "source": "library", "prompt_ref": None},
            "overlays": [{"type": "emotional", "ref": "emoji:money_mouth"}],
            "charts": [],
            "word_count": len(voice_text[sid].split()),
        }
        
        # Assign chart to subseg-02
        if sid == "subseg-02" and chart_props:
            ss["charts"] = [{"chart_id": "chart-01", "props": chart_props}]
            ss["overlays"].append({"type": "informational", "ref": "chart:chart-01"})
        
        subsegments.append(ss)
    
    segments = [
        {
            "segment_id": "seg-01",
            "beat": "hook_claim",
            "subsegments": [subsegment_ids[0]],
            "duration_seconds": 10.0,
            "zoom_plan": _zoom_plan_for(10.0),
            "sound_reset": {"sfx_id": "tap_01", "at_seconds": 0.0},
        },
        {
            "segment_id": "seg-02",
            "beat": "support_proof",
            "subsegments": [subsegment_ids[1], subsegment_ids[2]],
            "duration_seconds": 20.0,
            "zoom_plan": _zoom_plan_for(20.0),
            "sound_reset": {"sfx_id": "tap_01", "at_seconds": 0.0},
        },
        {
            "segment_id": "seg-03",
            "beat": "implication_cost",
            "subsegments": [subsegment_ids[3]],
            "duration_seconds": 10.0,
            "zoom_plan": _zoom_plan_for(10.0),
            "sound_reset": {"sfx_id": "tap_01", "at_seconds": 0.0},
        },
        {
            "segment_id": "seg-04",
            "beat": "landing_reframe",
            "subsegments": [subsegment_ids[4]],
            "duration_seconds": 10.0,
            "zoom_plan": _zoom_plan_for(10.0),
            "sound_reset": {"sfx_id": "tap_01", "at_seconds": 0.0},
        },
    ]
    
    return {
        "version": "2.1",
        "reel": {
            "reel_id": reel_path.name,
            "claim_id": claim.claim_id,
            "subsegment_count": len(subsegment_ids),
            "duration_seconds": 50,
            "audit_level": claim.audit_level,
        },
        "inputs": {
            "claim": {
                "claim_id": claim.claim_id,
                "claim_text": claim.claim_text,
                "supporting_data_ref": claim.supporting_data_ref,
                "audit_level": claim.audit_level,
                "tags": claim.tags or [],
                "risk_notes": claim.risk_notes,
                "thumbnail_text": claim.thumbnail_text,
            },
        },
        "segments": segments,
        "subsegments": subsegments,
        "script": {"ai_generated": False},
        "notes": {"phase": "2", "ai_mode": False},
    }


# Legacy alias for backwards compatibility
v2_generate_plan = generate_plan
