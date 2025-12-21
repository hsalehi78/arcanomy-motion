"""V2 kit generation (Phase 6): guides, thumbnail, quality gate."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from src.utils.paths import (
    ensure_v2_layout,
    v2_captions_srt_path,
    v2_charts_dir,
    v2_guides_dir,
    v2_plan_path,
    v2_quality_gate_path,
    v2_subsegments_dir,
    v2_thumbnail_dir,
    v2_voice_dir,
)
from src.v2.charts import probe_video_frame_count, TARGET_FRAMES
from src.v2.provenance import write_json_immutable
from src.v2.visuals import probe_duration_seconds, validate_duration


def _write_text_immutable(path: Path, text: str, *, force: bool = False) -> bool:
    path = Path(path)
    if path.exists():
        old = path.read_text(encoding="utf-8")
        if old == text:
            return False
        if not force:
            raise RuntimeError(f"Refusing to overwrite existing file (immutability): {path}. Pass --force.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def _load_plan(reel_path: Path) -> dict[str, Any]:
    plan_path = v2_plan_path(reel_path)
    if not plan_path.exists():
        raise FileNotFoundError(f"Missing v2 plan: {plan_path}")
    return json.loads(plan_path.read_text(encoding="utf-8"))


def _wrap_text(text: str, width: int = 22) -> list[str]:
    words = re.findall(r"\S+", text.strip())
    if not words:
        return []
    lines: list[str] = []
    buf: list[str] = []
    for w in words:
        cand = " ".join(buf + [w])
        if len(cand) > width and buf:
            lines.append(" ".join(buf))
            buf = [w]
        else:
            buf.append(w)
    if buf:
        lines.append(" ".join(buf))
    return lines[:6]


def generate_thumbnail(
    reel_path: Path,
    *,
    force: bool = False,
    width: int = 1080,
    height: int = 1920,
) -> Path:
    """Generate a deterministic thumbnail.png (black bg, white text)."""
    reel_path = Path(reel_path)
    ensure_v2_layout(reel_path)

    plan = _load_plan(reel_path)
    claim = (plan.get("inputs") or {}).get("claim") or {}
    text = (claim.get("thumbnail_text") or claim.get("claim_text") or "").strip()
    if not text:
        text = reel_path.name

    out_dir = v2_thumbnail_dir(reel_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "thumbnail.png"

    if out.exists() and not force:
        return out

    img = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Try a bold font; fall back to default.
    font = None
    for candidate in (
        "shared/fonts/Montserrat-Bold.ttf",
        "shared/fonts/Inter-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/Arial.ttf",
    ):
        p = Path(candidate)
        if p.exists():
            try:
                font = ImageFont.truetype(str(p), 86)
                break
            except Exception:
                pass
    if font is None:
        font = ImageFont.load_default()

    lines = _wrap_text(text, width=24)
    if not lines:
        lines = [text[:40]]

    # Center block in top ~40% (avoid bottom UI area).
    y = int(height * 0.18)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (width - w) // 2
        # White with black stroke (high contrast)
        draw.text((x, y), line, font=font, fill=(245, 245, 245), stroke_width=6, stroke_fill=(0, 0, 0))
        y += int((bbox[3] - bbox[1]) * 1.2)

    out_dir.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def generate_guides(
    reel_path: Path,
    *,
    force: bool = False,
) -> list[Path]:
    """Generate CapCut assembly guide + retention checklist."""
    reel_path = Path(reel_path)
    ensure_v2_layout(reel_path)
    plan = _load_plan(reel_path)

    guides_dir = v2_guides_dir(reel_path)
    guides_dir.mkdir(parents=True, exist_ok=True)

    segments = plan.get("segments") or []
    subsegments = plan.get("subsegments") or []

    # CapCut Assembly Guide
    lines: list[str] = []
    lines.append("# CapCut Assembly Guide (V2)\n")
    lines.append(f"Reel: `{reel_path.name}`\n")
    lines.append("## Track Layout\n")
    lines.append("- V1: Background subsegments (`v2/subsegments/subseg-XX.mp4`)\n")
    lines.append("- V2: Chart overlays (`v2/charts/*.mp4`) (green screen -> Chroma Key)\n")
    lines.append("- V3: Captions + overlays (CapCut preset)\n")
    lines.append("- A1: Voice (`v2/voice/subseg-XX.wav`)\n")
    lines.append("- A2: Music (manual)\n")
    lines.append("- A3: Sound resets (library; manual placement)\n")
    lines.append("\n## Assembly Steps (Mechanical)\n")
    lines.append("1. Import all `v2/subsegments/*.mp4` and place them in order on V1.\n")
    lines.append("2. Import all `v2/voice/*.wav` and place them in order on A1 (align each to its matching 10s subsegment).\n")
    lines.append("3. Import `v2/captions/captions.srt` and apply the Arcanomy CapCut captions preset.\n")
    lines.append("4. If a chart MP4 exists for a subsegment, place it on V2 above the corresponding subsegment and apply Chroma Key to remove `#00FF00`.\n")
    lines.append("5. Apply zooms and overlays per the instructions below.\n")
    lines.append("6. Add sound resets at segment boundaries per the instructions below.\n")
    lines.append("\n## Per-Subsegment Instructions\n")

    charts_dir = v2_charts_dir(reel_path)
    for ss in subsegments:
        sid = ss.get("subsegment_id")
        if not sid:
            continue
        lines.append(f"\n### {sid}\n")
        lines.append(f"- V1: `v2/subsegments/{sid}.mp4`\n")
        lines.append(f"- A1: `v2/voice/{sid}.wav`\n")
        # charts
        chart_jobs = ss.get("charts") or []
        if chart_jobs:
            for job in chart_jobs:
                cid = (job or {}).get("chart_id")
                if cid:
                    chart_file = f"chart-{sid}-{cid}.mp4"
                    lines.append(f"- V2 chart: `v2/charts/{chart_file}` (apply Chroma Key to green)\n")
        else:
            # Look for any rendered chart file matching the sid (best-effort)
            matches = sorted(charts_dir.glob(f"chart-{sid}-*.mp4"))
            for m in matches:
                lines.append(f"- V2 chart: `v2/charts/{m.name}` (apply Chroma Key to green)\n")

        # overlays
        overlays = ss.get("overlays") or []
        emos = [o for o in overlays if isinstance(o, dict) and o.get("type") == "emotional"]
        infos = [o for o in overlays if isinstance(o, dict) and o.get("type") == "informational"]
        if emos:
            lines.append(f"- Emotional overlay: `{emos[0].get('ref')}`\n")
        else:
            lines.append("- Emotional overlay: (ADD ONE)\n")
        if infos:
            lines.append(f"- Informational overlay: `{infos[0].get('ref')}`\n")
        else:
            # If charts exist, informational overlay is required.
            if chart_jobs:
                lines.append("- Informational overlay: (REQUIRED - tie to chart)\n")
            else:
                lines.append("- Informational overlay: (optional)\n")

    lines.append("\n## Segment Boundaries (Sound Reset)\n")
    for seg in segments:
        seg_id = seg.get("segment_id")
        subseg_ids = seg.get("subsegments") or []
        sfx = (seg.get("sound_reset") or {}).get("sfx_id", "tap_01")
        if seg_id and subseg_ids:
            lines.append(f"- {seg_id} start ({subseg_ids[0]} @ 0.0s): sound reset `{sfx}`\n")

    lines.append("\n## Zoom Plan (3 per segment)\n")
    for seg in segments:
        seg_id = seg.get("segment_id")
        zp = seg.get("zoom_plan") or []
        if not seg_id:
            continue
        if isinstance(zp, list) and len(zp) >= 3:
            times = [str(z.get("at_seconds")) for z in zp[:3]]
            lines.append(f"- {seg_id}: zooms at {', '.join(times)} seconds\n")

    capcut_guide = guides_dir / "capcut_assembly_guide.md"
    _write_text_immutable(capcut_guide, "".join(lines), force=force)

    # Retention checklist
    cl: list[str] = []
    cl.append("# Retention Checklist (V2)\n\n")
    cl.append("## 3–2–1 Instruction Presence Gate\n")
    cl.append("- [ ] 3 zoom instructions per segment present\n")
    cl.append("- [ ] Emotional overlay instruction present per subsegment\n")
    cl.append("- [ ] Informational overlay instruction present when a chart is used\n")
    cl.append("- [ ] Sound reset instruction present at each segment boundary\n\n")
    cl.append("## CapCut Rules\n")
    cl.append("- [ ] Captions preset applied (yellow + stroke + glow + keyword highlighting)\n")
    cl.append("- [ ] Chroma key applied to chart overlays (remove #00FF00)\n")
    cl.append("- [ ] Music is low arousal, no vocals, no drops\n")
    cl.append("- [ ] Export 9:16, 1080x1920\n")

    retention = guides_dir / "retention_checklist.md"
    _write_text_immutable(retention, "".join(cl), force=force)

    return [capcut_guide, retention]


def _parse_srt_timestamp(ts: str) -> float:
    # "HH:MM:SS,mmm"
    hh, mm, rest = ts.split(":")
    ss, ms = rest.split(",")
    return int(hh) * 3600 + int(mm) * 60 + int(ss) + (int(ms) / 1000.0)


def _validate_srt_boundaries(srt_path: Path) -> list[str]:
    """Return list of errors."""
    errors: list[str] = []
    if not srt_path.exists():
        return ["missing captions.srt"]
    text = srt_path.read_text(encoding="utf-8", errors="replace")
    lines = [l.rstrip("\n") for l in text.splitlines()]
    for l in lines:
        if "-->" in l:
            start_s, end_s = [x.strip() for x in l.split("-->")]
            start = _parse_srt_timestamp(start_s)
            end = _parse_srt_timestamp(end_s)
            if end <= start:
                errors.append(f"srt entry has non-positive duration: {l}")
                continue
            # Boundary rule: must not cross 10s block boundary.
            start_block = int(start // 10.0)
            end_block = int((end - 1e-6) // 10.0)
            if start_block != end_block:
                errors.append(f"srt crosses subsegment boundary: {l}")
    return errors


def generate_quality_gate(
    reel_path: Path,
    *,
    force: bool = False,
    fps: int = 30,
) -> Path:
    """Emit `v2/meta/quality_gate.json` with pass/fail + reasons."""
    reel_path = Path(reel_path)
    ensure_v2_layout(reel_path)

    plan = _load_plan(reel_path)
    segments = plan.get("segments") or []
    subsegments = plan.get("subsegments") or []

    reasons: list[str] = []
    counters: dict[str, Any] = {}

    # Validate instruction presence
    for seg in segments:
        seg_id = seg.get("segment_id", "seg-?")
        zp = seg.get("zoom_plan") or []
        if not (isinstance(zp, list) and len(zp) >= 3):
            reasons.append(f"{seg_id}: missing zoom_plan (need 3)")
        sr = seg.get("sound_reset") or {}
        if not (isinstance(sr, dict) and sr.get("sfx_id")):
            reasons.append(f"{seg_id}: missing sound_reset instruction")

    # Validate subsegment outputs
    sub_dir = v2_subsegments_dir(reel_path)
    voice_dir = v2_voice_dir(reel_path)
    charts_dir = v2_charts_dir(reel_path)
    srt_path = v2_captions_srt_path(reel_path)

    counters["subsegments_expected"] = len(subsegments)
    counters["charts_expected"] = sum(len(ss.get("charts") or []) for ss in subsegments if isinstance(ss, dict))

    for ss in subsegments:
        sid = ss.get("subsegment_id")
        if not sid:
            continue
        mp4 = sub_dir / f"{sid}.mp4"
        wav = voice_dir / f"{sid}.wav"
        if not mp4.exists():
            reasons.append(f"missing subsegment video: {mp4.name}")
        else:
            dur = probe_duration_seconds(mp4)
            try:
                validate_duration(duration_seconds=dur, target_seconds=10.0, fps=fps, tolerance_frames=1)
            except Exception as e:
                reasons.append(f"{mp4.name}: {e}")
        if not wav.exists():
            reasons.append(f"missing voice wav: {wav.name}")
        else:
            dur = probe_duration_seconds(wav)
            try:
                validate_duration(duration_seconds=dur, target_seconds=10.0, fps=fps, tolerance_frames=1)
            except Exception as e:
                reasons.append(f"{wav.name}: {e}")

        overlays = ss.get("overlays") or []
        emos = [o for o in overlays if isinstance(o, dict) and o.get("type") == "emotional"]
        infos = [o for o in overlays if isinstance(o, dict) and o.get("type") == "informational"]
        if not emos:
            reasons.append(f"{sid}: missing emotional overlay instruction")
        if len(infos) > 1:
            reasons.append(f"{sid}: too many informational overlays (max 1)")
        if (ss.get("charts") or []) and not infos:
            reasons.append(f"{sid}: missing informational overlay instruction (required when chart present)")

        # Chart outputs (if chart jobs exist)
        jobs = ss.get("charts") or []
        for job in jobs:
            cid = (job or {}).get("chart_id")
            if not cid:
                continue
            out = charts_dir / f"chart-{sid}-{cid}.mp4"
            if not out.exists():
                reasons.append(f"missing chart mp4: {out.name}")
            else:
                frames = probe_video_frame_count(out)
                if abs(frames - TARGET_FRAMES) > 1:
                    reasons.append(f"{out.name}: frames {frames} != {TARGET_FRAMES}±1")

    # Captions boundary validation
    reasons.extend(_validate_srt_boundaries(srt_path))

    # Guides + thumbnail presence
    guides_dir = v2_guides_dir(reel_path)
    thumb = v2_thumbnail_dir(reel_path) / "thumbnail.png"
    if not (guides_dir / "capcut_assembly_guide.md").exists():
        reasons.append("missing capcut_assembly_guide.md")
    if not (guides_dir / "retention_checklist.md").exists():
        reasons.append("missing retention_checklist.md")
    if not thumb.exists():
        reasons.append("missing thumbnail.png")

    payload = {
        "schema_version": "v2.quality_gate.1",
        "reel_id": reel_path.name,
        "pass": len(reasons) == 0,
        "reasons": reasons,
        "counters": counters,
    }
    out_path = v2_quality_gate_path(reel_path)
    write_json_immutable(out_path, payload, force=force)
    return out_path


def v2_generate_kit(
    reel_path: Path,
    *,
    force: bool = False,
) -> dict[str, Path]:
    """Generate guides + thumbnail + quality gate."""
    reel_path = Path(reel_path)
    ensure_v2_layout(reel_path)

    thumb = generate_thumbnail(reel_path, force=force)
    guides = generate_guides(reel_path, force=force)
    gate = generate_quality_gate(reel_path, force=force)
    return {
        "thumbnail": thumb,
        "capcut_guide": guides[0],
        "retention_checklist": guides[1],
        "quality_gate": gate,
    }


