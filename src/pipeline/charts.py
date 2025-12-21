"""Charts stage - Remotion chart rendering.

Inputs:
- `meta/plan.json` containing optional per-subsegment chart jobs

Outputs:
- `charts/chart-<subseg>-<chart_id>.json` (render props, deterministic)
- `charts/chart-<subseg>-<chart_id>.mp4` (10.0s @ 30fps)

Canonical approach (aligned with docs/charts):
- Chart duration is controlled via `animation.*` props.
- For exact 10.0s (300 frames @ 30fps), we set props such that Remotion metadata
  naturally computes durationInFrames=300 using the existing formulas:
    - Use animation.style="simultaneous"
    - velocityMode=false
    - staggerDelay=0
    - For number counter, set delay=0
    - Set animation.duration=270 so (duration + hold 30) = 300
- Transparency for CapCut is via green-screen: `background.color="#00FF00"`
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from src.services.chart_renderer import render_chart_from_json
from src.utils.paths import ensure_pipeline_layout, charts_dir, plan_path
from src.pipeline.provenance import write_json_immutable


TARGET_FPS = 30
TARGET_SECONDS = 10.0
TARGET_FRAMES = int(TARGET_SECONDS * TARGET_FPS)  # 300
HOLD_FRAMES_DEFAULT = 30  # per Remotion Root metadata formulas
ANIM_FRAMES_FOR_10S = TARGET_FRAMES - HOLD_FRAMES_DEFAULT  # 270


def _normalize_chart_props(props: dict[str, Any]) -> dict[str, Any]:
    """Mutate chart props to enforce canonical 10s render + green-screen background."""
    out = json.loads(json.dumps(props))  # deep copy deterministically

    # Green-screen background (docs/charts)
    bg = out.get("background")
    if not isinstance(bg, dict):
        bg = {}
        out["background"] = bg
    bg["color"] = "#00FF00"

    # Animation normalization
    anim = out.get("animation")
    if not isinstance(anim, dict):
        anim = {}
        out["animation"] = anim
    anim["duration"] = int(ANIM_FRAMES_FOR_10S)
    anim["style"] = "simultaneous"
    anim["staggerDelay"] = 0
    anim["velocityMode"] = False

    # Some charts use delay (number counter)
    if "delay" in anim:
        anim["delay"] = 0

    # Legacy prop shape support: remove animationDuration if present (avoid ambiguity)
    if "animationDuration" in out:
        out.pop("animationDuration", None)

    return out


def probe_video_frame_count(path: Path) -> int:
    """Count decoded video frames using ffprobe."""
    if shutil.which("ffprobe") is None:
        raise RuntimeError("ffprobe not found on PATH (required for frame validation).")
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-count_frames",
        "-show_entries",
        "stream=nb_read_frames",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    out = subprocess.check_output(cmd).decode("utf-8", errors="replace").strip()
    return int(out)


def render_charts(
    reel_path: Path,
    *,
    force: bool = False,
    fps: int = TARGET_FPS,
) -> list[Path]:
    reel_path = Path(reel_path)
    ensure_pipeline_layout(reel_path)

    plan_file = plan_path(reel_path)
    if not plan_file.exists():
        raise FileNotFoundError(f"Missing plan: {plan_file}. Run 'plan' stage first.")

    plan = json.loads(plan_file.read_text(encoding="utf-8"))
    subsegments = plan.get("subsegments") or []
    out_dir = charts_dir(reel_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    rendered: list[Path] = []
    for ss in subsegments:
        sid = ss.get("subsegment_id")
        jobs = ss.get("charts") or []
        if not sid or not isinstance(jobs, list):
            continue

        for job in jobs:
            if not isinstance(job, dict):
                continue
            chart_id = str(job.get("chart_id") or "chart")
            props = job.get("props")
            if not isinstance(props, dict):
                continue

            norm = _normalize_chart_props(props)
            props_path = out_dir / f"chart-{sid}-{chart_id}.json"
            mp4_path = out_dir / f"chart-{sid}-{chart_id}.mp4"

            # Deterministic props file (immutable unless force)
            write_json_immutable(props_path, norm, force=force)

            # Render (skip if exists unless force)
            if mp4_path.exists() and not force:
                frames = probe_video_frame_count(mp4_path)
                # Accept ±1 frame per RFC
                if abs(frames - TARGET_FRAMES) > 1:
                    raise RuntimeError(f"Chart frame count out of tolerance: got {frames}, expected {TARGET_FRAMES}±1")
                rendered.append(mp4_path)
                continue

            # Render exact 10.0s by clamping frames.
            render_chart_from_json(props_path, output_path=mp4_path, frames="0-299")
            frames = probe_video_frame_count(mp4_path)
            if abs(frames - TARGET_FRAMES) > 1:
                raise RuntimeError(f"Chart frame count out of tolerance: got {frames}, expected {TARGET_FRAMES}±1")
            rendered.append(mp4_path)

    return rendered


# Legacy alias
v2_render_charts = render_charts


