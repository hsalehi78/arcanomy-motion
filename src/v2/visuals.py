"""V2 deterministic subsegment visuals (Phase 3).

Canonical baseline:
- Produce `v2/subsegments/subseg-XX.mp4`
- Each output is exactly 10.0s (±1 frame tolerance at target fps for validation)
- No Remotion usage (Remotion is charts-only in v2)
"""

from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path

from src.utils.paths import ensure_v2_layout, v2_plan_path, v2_subsegments_dir
# (reserved for later) quality gate metadata emission will live next to this stage.


def _ffmpeg_exists() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def probe_duration_seconds(path: Path) -> float:
    """Return duration in seconds using ffprobe."""
    if shutil.which("ffprobe") is None:
        raise RuntimeError("ffprobe not found on PATH (required for duration validation).")
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    out = subprocess.check_output(cmd).decode("utf-8", errors="replace").strip()
    return float(out)


def validate_duration(
    *,
    duration_seconds: float,
    target_seconds: float,
    fps: int,
    tolerance_frames: int = 1,
) -> None:
    tol = tolerance_frames / float(fps)
    if abs(duration_seconds - target_seconds) > tol:
        raise RuntimeError(
            f"Duration out of tolerance: got {duration_seconds:.4f}s, "
            f"target {target_seconds:.1f}s ± {tol:.4f}s ({tolerance_frames} frame @ {fps}fps)"
        )


def render_subsegment_background(
    *,
    out_path: Path,
    duration_seconds: float = 10.0,
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
    force: bool = False,
) -> None:
    """Render a deterministic dark 'breathing' background clip using FFmpeg.

    We generate a slightly larger canvas and apply a slow drift crop so the frame changes
    subtly over time (Ken Burns-like), plus light temporal grain for texture.
    """
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found on PATH (required to render subsegments).")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Immutability: do not overwrite unless force.
    if out_path.exists() and not force:
        return

    # Overscan canvas to allow drift.
    overscan_w = int(math.ceil(width * 1.15))
    overscan_h = int(math.ceil(height * 1.15))

    # Deterministic drift expressions (time-based, but fully deterministic).
    # Period set to 10s so each clip is one full gentle loop.
    x_expr = f"(iw-{width})/2 + 40*sin(2*PI*t/{duration_seconds})"
    y_expr = f"(ih-{height})/2 + 25*cos(2*PI*t/{duration_seconds})"

    # Use a near-black base, add temporal grain, then drift crop to 9:16 frame.
    lavfi = (
        f"color=c=#050505:s={overscan_w}x{overscan_h}:r={fps}:d={duration_seconds},"
        f"noise=alls=8:allf=t+u,"
        f"crop={width}:{height}:x='{x_expr}':y='{y_expr}',"
        f"format=yuv420p"
    )

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y" if force else "-n",
        "-f",
        "lavfi",
        "-i",
        lavfi,
        "-t",
        f"{duration_seconds}",
        "-r",
        str(fps),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(out_path),
    ]
    _run(cmd)


def v2_generate_subsegments(
    reel_path: Path,
    *,
    force: bool = False,
    fps: int = 30,
    tolerance_frames: int = 1,
) -> list[Path]:
    """Generate `v2/subsegments/*.mp4` from `v2/meta/plan.json`."""
    reel_path = Path(reel_path)
    ensure_v2_layout(reel_path)

    if not _ffmpeg_exists():
        raise RuntimeError("ffmpeg/ffprobe required but not found on PATH.")

    plan_path = v2_plan_path(reel_path)
    if not plan_path.exists():
        raise FileNotFoundError(f"Missing v2 plan: {plan_path}. Run v2 stage 'plan' first.")

    import json

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    subsegments = plan.get("subsegments") or []
    out_dir = v2_subsegments_dir(reel_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    outputs: list[Path] = []
    for ss in subsegments:
        sid = ss["subsegment_id"]
        out_path = out_dir / f"{sid}.mp4"
        render_subsegment_background(out_path=out_path, duration_seconds=10.0, fps=fps, force=force)
        dur = probe_duration_seconds(out_path)
        validate_duration(duration_seconds=dur, target_seconds=10.0, fps=fps, tolerance_frames=tolerance_frames)
        outputs.append(out_path)

    return outputs


