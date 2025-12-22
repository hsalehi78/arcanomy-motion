"""Provenance helpers for deterministic, auditable runs.

Provenance must be stable (sorted keys), and reruns should not
rewrite files if content is unchanged.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


def _sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def sha256_file(path: Path) -> str:
    path = Path(path)
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_json_dumps(obj: Any) -> str:
    """Deterministic JSON encoding."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def write_json_immutable(
    path: Path,
    payload: Mapping[str, Any],
    *,
    force: bool = False,
) -> bool:
    """Write a JSON file deterministically.

    Rules:
    - If file does not exist: write it.
    - If file exists with identical content: do nothing.
    - If file exists and differs: raise unless force=True.

    Returns:
        True if wrote bytes, False if skipped due to identical content.
    """
    path = Path(path)
    new_text = stable_json_dumps(payload)

    if path.exists():
        old_text = path.read_text(encoding="utf-8")
        if old_text == new_text:
            return False
        if not force:
            raise RuntimeError(
                f"Refusing to overwrite existing file (immutability): {path}. "
                f"Pass --force to overwrite."
            )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(new_text, encoding="utf-8")
    return True


@dataclass(frozen=True)
class RunContext:
    """Minimal run context captured in provenance."""

    mode: str  # "pipeline"
    fresh: bool
    force: bool
    audit_level_override: str | None = None


def build_provenance(
    *,
    reel_path: Path,
    claim_path: Path | None,
    chart_path: Path | None,
    ctx: RunContext,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    reel_path = Path(reel_path)

    inputs: dict[str, Any] = {}

    def add_input(label: str, p: Path | None):
        if p is None:
            inputs[label] = {"present": False}
            return
        p = Path(p)
        if not p.exists():
            inputs[label] = {"present": False, "path": str(p)}
            return
        inputs[label] = {
            "present": True,
            "path": str(p),
            "sha256": sha256_file(p),
        }

    add_input("claim_json", claim_path)
    add_input("chart_json", chart_path)

    payload: dict[str, Any] = {
        "schema_version": "provenance.1",
        "mode": ctx.mode,
        # Timestamp is intentionally kept (auditable), but does mean reruns differ.
        # For "zero diffs" reruns, callers should avoid writing if unchanged.
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reel_path": str(reel_path),
        "inputs": inputs,
        "flags": {
            "fresh": ctx.fresh,
            "force": ctx.force,
            "audit_level_override": ctx.audit_level_override,
        },
        "runtime": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
    }

    if extra:
        payload["extra"] = dict(extra)

    # Deterministic signature of provenance content excluding created_at.
    sig_obj = dict(payload)
    sig_obj.pop("created_at", None)
    payload["signature_sha256"] = _sha256_bytes(stable_json_dumps(sig_obj).encode("utf-8"))

    return payload


# Legacy alias for backwards compatibility
V2RunContext = RunContext


