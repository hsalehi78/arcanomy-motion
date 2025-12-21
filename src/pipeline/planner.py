"""Plan generator - deterministic segment/subsegment planning.

This is intentionally rules-first and deterministic.
It produces `meta/plan.json`, which becomes the contract for later stages.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from src.utils.paths import (
    claim_json_path,
    data_json_path,
    ensure_pipeline_layout,
    plan_path,
)
from src.pipeline.provenance import write_json_immutable


AuditLevel = Literal["basic", "strict"]


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


def _zoom_plan_for(duration_seconds: float) -> list[dict[str, float]]:
    """Deterministic 3-zoom schedule.

    Uses 15%, 45%, 75% marks, rounded to 0.1s.
    """
    t1 = round(duration_seconds * 0.15, 1)
    t2 = round(duration_seconds * 0.45, 1)
    t3 = round(duration_seconds * 0.75, 1)
    # Ensure within bounds and monotonic (avoid 0.0 edge cases)
    t1 = max(0.1, min(duration_seconds - 0.1, t1))
    t2 = max(t1 + 0.1, min(duration_seconds - 0.1, t2))
    t3 = max(t2 + 0.1, min(duration_seconds - 0.1, t3))
    return [{"at_seconds": t1}, {"at_seconds": t2}, {"at_seconds": t3}]


def generate_plan(
    reel_path: Path,
    *,
    force: bool = False,
) -> Path:
    """Generate `meta/plan.json` deterministically.

    Canonical defaults (doctrine):
    - 10.0s atomic subsegments
    - default reel = 50s (5 subsegments) using 10+20+10+10 segment template
    """
    reel_path = Path(reel_path)
    ensure_pipeline_layout(reel_path)

    claim_file = claim_json_path(reel_path)
    data_file = data_json_path(reel_path)
    if not claim_file.exists():
        raise FileNotFoundError(f"Missing required input: {claim_file}")
    if not data_file.exists():
        raise FileNotFoundError(f"Missing required input: {data_file}")

    claim = _parse_claim(_read_json(claim_file))
    data = _read_json(data_file)  # validated later during chart rendering (audit DSL)

    # Canonical default: 5 subsegments (50s)
    subsegment_ids = [f"subseg-{i:02d}" for i in range(1, 6)]

    # Canonical segment template for 50s: 10 + 20 + 10 + 10
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

    # Minimal deterministic voice text placeholders (Phase 4 will generate voice audio).
    # Subseg-01 uses the sacred claim sentence verbatim.
    voice_text = {
        subsegment_ids[0]: claim.claim_text,
        subsegment_ids[1]: "Here’s the proof.",
        subsegment_ids[2]: "And why it matters.",
        subsegment_ids[3]: "The hidden cost is time.",
        subsegment_ids[4]: "Decide—then move.",
    }

    # Overlays: always one emotional overlay instruction. Informational overlay optional.
    # Chart planning is not included here unless data contains explicit chart intents (future).
    subsegments = []
    for sid in subsegment_ids:
        subsegments.append(
            {
                "subsegment_id": sid,
                "duration_seconds": 10.0,
                "voice": {"text": voice_text[sid]},
                "visual": {
                    "type": "still",
                    "source": "library",
                    "prompt_ref": None,
                },
                "overlays": [
                    {"type": "emotional", "ref": "emoji:money_mouth"},
                ],
                "charts": [],
            }
        )

    # Optional v2 hook: allow data.json to provide fully-formed chart JSON props
    # using the docs/charts v2.0 schema. This is deterministic and keeps chart
    # authoring simple while strict audit DSL is implemented later.
    charts = data.get("charts") if isinstance(data, dict) else None
    if isinstance(charts, list):
        # Deterministic mapping: if chart specifies subsegment_id, use it; otherwise assign
        # in order to subseg-02, subseg-03, ... (skip subseg-01 by default).
        fallback_targets = subsegment_ids[1:] if len(subsegment_ids) > 1 else subsegment_ids
        fallback_i = 0

        by_id = {ss["subsegment_id"]: ss for ss in subsegments}
        for i, chart in enumerate(charts, start=1):
            if not isinstance(chart, dict):
                continue
            chart_id = str(chart.get("chart_id") or f"chart-{i:02d}")
            target = chart.get("subsegment_id")
            if not target:
                target = fallback_targets[min(fallback_i, len(fallback_targets) - 1)]
                fallback_i += 1
            target = str(target)
            if target not in by_id:
                continue
            props = chart.get("props")
            if not isinstance(props, dict):
                continue
            ss_obj = by_id[target]
            ss_obj["charts"].append({"chart_id": chart_id, "props": props})

            # Doctrine: 2 overlays per subsegment (1 informational max, 1 emotional).
            # If a chart is present, informational overlay becomes required.
            overlays = ss_obj.get("overlays")
            if not isinstance(overlays, list):
                overlays = []
                ss_obj["overlays"] = overlays
            has_info = any(isinstance(o, dict) and o.get("type") == "informational" for o in overlays)
            if not has_info:
                overlays.append({"type": "informational", "ref": f"chart:{chart_id}"})

    plan = {
        "version": "2.0",
        "reel": {
            "reel_id": reel_path.name,
            "claim_id": claim.claim_id,
            "subsegment_count": len(subsegment_ids),
            "duration_seconds": len(subsegment_ids) * 10,
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
            "data": data,
        },
        "segments": segments,
        "subsegments": subsegments,
        "notes": {
            "phase": "2",
            "determinism": "rules_only",
            "chart_planning": "not_implemented",
        },
    }

    out = plan_path(reel_path)
    write_json_immutable(out, plan, force=force)
    return out


# Legacy alias for backwards compatibility
v2_generate_plan = generate_plan


