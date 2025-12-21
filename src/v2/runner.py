"""V2 pipeline runner (Phase 1: init + provenance only)."""

from __future__ import annotations

import shutil
from pathlib import Path

from src.utils.paths import (
    claim_json_path,
    data_json_path,
    ensure_v2_layout,
    inputs_dir,
    v2_dir,
    v2_provenance_path,
)
from src.v2.provenance import V2RunContext, build_provenance, write_json_immutable


def v2_init(
    reel_path: Path,
    *,
    fresh: bool = False,
    force: bool = False,
    audit_level_override: str | None = None,
) -> Path:
    """Initialize v2 outputs for a reel: folder layout + provenance.

    Phase 1 scope:
    - Create `v2/` folder structure
    - Write `v2/meta/provenance.json` immutably
    """
    reel_path = Path(reel_path)
    if not reel_path.exists():
        raise FileNotFoundError(f"Reel folder not found: {reel_path}")

    # Ensure minimal inputs directory exists (do not create legacy folders here).
    inputs_dir(reel_path).mkdir(parents=True, exist_ok=True)

    # Fresh mode wipes all v2 artifacts.
    if fresh and v2_dir(reel_path).exists():
        shutil.rmtree(v2_dir(reel_path))

    ensure_v2_layout(reel_path)

    prov_path = v2_provenance_path(reel_path)
    # Provenance is immutable once created. On reruns, do not rewrite (created_at would differ)
    # unless explicitly forced or a fresh run wiped the v2/ directory.
    if prov_path.exists() and not force:
        return prov_path

    prov_payload = build_provenance(
        reel_path=reel_path,
        claim_path=claim_json_path(reel_path),
        data_path=data_json_path(reel_path),
        ctx=V2RunContext(
            mode="v2",
            fresh=fresh,
            force=force,
            audit_level_override=audit_level_override,
        ),
        extra={
            "phase": "1",
            "note": "v2_init only (folders + provenance).",
        },
    )
    write_json_immutable(prov_path, prov_payload, force=force)
    return prov_path


