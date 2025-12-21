"""Pipeline runner - initialization and orchestration."""

from __future__ import annotations

import shutil
from pathlib import Path

from src.utils.paths import (
    claim_json_path,
    data_json_path,
    ensure_pipeline_layout,
    inputs_dir,
    meta_dir,
    provenance_path,
)
from src.pipeline.provenance import RunContext, build_provenance, write_json_immutable


def init(
    reel_path: Path,
    *,
    fresh: bool = False,
    force: bool = False,
    audit_level_override: str | None = None,
) -> Path:
    """Initialize pipeline outputs for a reel: folder layout + provenance.

    Creates the canonical output folder structure and writes provenance.json.
    """
    reel_path = Path(reel_path)
    if not reel_path.exists():
        raise FileNotFoundError(f"Reel folder not found: {reel_path}")

    # Ensure minimal inputs directory exists.
    inputs_dir(reel_path).mkdir(parents=True, exist_ok=True)

    # Fresh mode wipes pipeline artifacts (meta, subsegments, charts, etc).
    if fresh:
        for subdir in ("meta", "subsegments", "charts", "voice", "captions", "thumbnail", "guides"):
            target = reel_path / subdir
            if target.exists():
                shutil.rmtree(target)

    ensure_pipeline_layout(reel_path)

    prov_path = provenance_path(reel_path)
    # Provenance is immutable once created. On reruns, do not rewrite (created_at would differ)
    # unless explicitly forced or a fresh run wiped the directory.
    if prov_path.exists() and not force:
        return prov_path

    prov_payload = build_provenance(
        reel_path=reel_path,
        claim_path=claim_json_path(reel_path),
        data_path=data_json_path(reel_path),
        ctx=RunContext(
            mode="pipeline",
            fresh=fresh,
            force=force,
            audit_level_override=audit_level_override,
        ),
        extra={
            "note": "Pipeline init (folders + provenance).",
        },
    )
    write_json_immutable(prov_path, prov_payload, force=force)
    return prov_path


# Legacy alias for backwards compatibility
v2_init = init


