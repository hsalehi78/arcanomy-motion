"""Captions generation - line-level SRT for CapCut.

Canonical output:
- `captions/captions.srt`
- Line-level only (no karaoke / word timing)
- Timings aligned using audio analysis (silence detection)
- Hard rule: no entry crosses subsegment boundaries
"""

from __future__ import annotations

import math
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from src.utils.paths import (
    ensure_pipeline_layout,
    captions_srt_path,
    plan_path,
    pipeline_voice_dir,
)
from src.pipeline.visuals import probe_duration_seconds, validate_duration


def _format_srt_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - math.floor(seconds)) * 1000))
    if millis == 1000:
        secs += 1
        millis = 0
    if secs == 60:
        minutes += 1
        secs = 0
    if minutes == 60:
        hours += 1
        minutes = 0
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _write_text_immutable(path: Path, text: str, *, force: bool = False) -> bool:
    """Write text file without rewriting if identical. Raise if differs and not forced."""
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


def _silence_segments(path: Path, *, noise_db: float = -35.0, min_silence: float = 0.2) -> list[tuple[str, float]]:
    """Return silencedetect events as (kind, seconds) where kind is 'start' or 'end'."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found (required for silence detection).")
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "info",
        "-i",
        str(path),
        "-af",
        f"silencedetect=noise={noise_db}dB:d={min_silence}",
        "-f",
        "null",
        "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    text = proc.stderr or ""
    events: list[tuple[str, float]] = []
    for line in text.splitlines():
        line = line.strip()
        if "silence_start:" in line:
            m = re.search(r"silence_start:\s*([0-9.]+)", line)
            if m:
                events.append(("start", float(m.group(1))))
        elif "silence_end:" in line:
            m = re.search(r"silence_end:\s*([0-9.]+)", line)
            if m:
                events.append(("end", float(m.group(1))))
    return events


def _speech_window(path: Path, *, total_seconds: float = 10.0) -> tuple[float, float]:
    """Estimate speech start/end from silencedetect.

    If no useful events, returns a conservative default window.
    """
    events = _silence_segments(path)
    # Defaults
    start = 0.1
    end = total_seconds - 0.1

    # Leading silence: if the first event is silence_start very near 0, use its silence_end as speech start.
    for i, (kind, t) in enumerate(events):
        if kind == "start" and t <= 0.05:
            # find next end
            for j in range(i + 1, len(events)):
                if events[j][0] == "end":
                    start = min(end - 0.2, max(0.0, events[j][1]))
                    break
            break

    # Trailing silence: find last silence_start that occurs before the end and treat it as speech end.
    for kind, t in reversed(events):
        if kind == "start" and 0.2 < t < total_seconds:
            end = max(start + 0.2, min(total_seconds, t))
            break

    # Clamp
    start = max(0.0, min(total_seconds - 0.2, start))
    end = max(start + 0.2, min(total_seconds, end))
    return (start, end)


def _split_caption_lines(text: str, *, max_words: int = 9, max_chars: int = 42) -> list[str]:
    """Split into multiple SRT entries (each a single line) deterministically."""
    words = re.findall(r"\S+", text.strip())
    if not words:
        return []

    chunks: list[str] = []
    buf: list[str] = []

    def flush():
        nonlocal buf
        if buf:
            chunks.append(" ".join(buf).strip())
            buf = []

    for w in words:
        candidate = buf + [w]
        cand_text = " ".join(candidate)
        if len(candidate) > max_words or (len(cand_text) > max_chars and buf):
            flush()
            buf.append(w)
        else:
            buf.append(w)

        # Prefer break after sentence end if we have enough content
        if w.endswith((".", "!", "?")) and len(buf) >= 4:
            flush()

    flush()
    return chunks


def generate_captions_srt(
    reel_path: Path,
    *,
    force: bool = False,
    fps: int = 30,
) -> Path:
    reel_path = Path(reel_path)
    ensure_pipeline_layout(reel_path)

    plan_file = plan_path(reel_path)
    if not plan_file.exists():
        raise FileNotFoundError(f"Missing plan: {plan_file}. Run 'plan' stage first.")

    import json

    plan = json.loads(plan_file.read_text(encoding="utf-8"))
    subsegments = plan.get("subsegments") or []
    voice_dir = pipeline_voice_dir(reel_path)

    srt_entries: list[tuple[float, float, str]] = []
    idx_counter = 1

    for idx, ss in enumerate(subsegments):
        sid = ss["subsegment_id"]
        text = (ss.get("voice") or {}).get("text") or ""
        wav = voice_dir / f"{sid}.wav"
        if not wav.exists():
            raise FileNotFoundError(f"Missing voice WAV for captions alignment: {wav}")

        dur = probe_duration_seconds(wav)
        validate_duration(duration_seconds=dur, target_seconds=10.0, fps=fps, tolerance_frames=1)

        # Local window within the 10s block
        local_start, local_end = _speech_window(wav, total_seconds=10.0)
        window = max(0.2, local_end - local_start)

        # Split into line-level entries
        lines = _split_caption_lines(str(text))
        if not lines:
            continue

        weights = [max(1, len(line)) for line in lines]
        total_w = sum(weights)
        offsets = idx * 10.0

        cursor = local_start
        for line, w in zip(lines, weights):
            span = window * (w / total_w)
            start = cursor
            end = cursor + span
            cursor = end

            # Clamp within this subsegment
            start = max(0.0, min(10.0, start))
            end = max(start + (1.0 / fps), min(10.0, end))

            global_start = offsets + start
            global_end = offsets + end
            # Hard safety: never cross boundary
            global_end = min(offsets + 10.0, global_end)
            srt_entries.append((global_start, global_end, line))
            idx_counter += 1

        # Ensure last entry doesn't exceed boundary
        if srt_entries and srt_entries[-1][1] > offsets + 10.0:
            s, _, t = srt_entries[-1]
            srt_entries[-1] = (s, offsets + 10.0, t)

    # Emit SRT text
    out_lines: list[str] = []
    for i, (start, end, text) in enumerate(srt_entries, start=1):
        if end <= start:
            end = start + (1.0 / fps)
        out_lines.append(str(i))
        out_lines.append(f"{_format_srt_timestamp(start)} --> {_format_srt_timestamp(end)}")
        out_lines.append(text)
        out_lines.append("")

    out_text = "\n".join(out_lines).rstrip() + "\n"
    out_file = captions_srt_path(reel_path)
    _write_text_immutable(out_file, out_text, force=force)
    return out_file


# Legacy alias
v2_generate_captions_srt = generate_captions_srt


