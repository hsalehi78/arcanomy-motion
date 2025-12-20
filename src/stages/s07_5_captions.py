"""Stage 7.5: Captions - Generate word timings + SRT and burn karaoke captions via Remotion.

This stage is a deterministic post-processing step designed for social shorts where many viewers
watch muted. It overlays the spoken text as on-screen captions and exports an .srt file.

Inputs:
- json/02_story_generator.output.json (segment text)
- renders/audio/voice/voice_XX.mp3 (or json/05.5_audio_generation.output.json durations)
- json/07_final.output.json (which clips actually made it into final_raw)
- final/final_raw.mp4 (base video with correct audio)

Outputs:
- json/07.5_captions.output.json (timing + render props)
- final/final.srt
- final/final.mp4 (captioned)
"""

from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.domain import Objective
from src.services import RemotionCLI
from src.utils.io import write_file
from src.utils.logger import get_logger
from src.utils.paths import final_dir as reel_final_dir
from src.utils.paths import json_path, prompt_path, voice_dir as reel_voice_dir

logger = get_logger()

DEFAULT_FPS = 30
CLIP_SECONDS = 10.0
CLIP_FRAMES = int(CLIP_SECONDS * DEFAULT_FPS)  # 300


def _ffprobe_duration(path: Path) -> Optional[float]:
    """Return media duration in seconds using ffprobe, or None if unavailable."""
    if not shutil.which("ffprobe"):
        return None
    if not path.exists():
        return None
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return None
        out = (result.stdout or "").strip()
        if not out:
            return None
        return float(out)
    except Exception:
        return None


def _tokenize_words(text: str) -> list[str]:
    # Keep punctuation attached to preserve readability ("game." stays "game.")
    return re.findall(r"\S+", text.strip())


def _word_weight(word: str) -> int:
    # Heuristic: longer words get slightly more time.
    cleaned = re.sub(r"[^\w]+", "", word)
    return max(1, len(cleaned))


def _allocate_frames(total_frames: int, weights: list[int], min_frames: int = 1) -> list[int]:
    """Allocate integer frames across items proportional to weights."""
    if total_frames <= 0 or not weights:
        return []

    total_w = sum(weights)
    if total_w <= 0:
        return [max(min_frames, total_frames // len(weights))] * len(weights)

    raw = [total_frames * (w / total_w) for w in weights]
    base = [max(min_frames, int(math.floor(r))) for r in raw]

    # Adjust to match exactly total_frames
    diff = total_frames - sum(base)

    if diff > 0:
        # Add remaining frames to largest fractional parts
        frac = [r - math.floor(r) for r in raw]
        order = sorted(range(len(frac)), key=lambda i: frac[i], reverse=True)
        for i in order:
            if diff == 0:
                break
            base[i] += 1
            diff -= 1
    elif diff < 0:
        # Remove extra frames from largest buckets first (keeping min_frames)
        order = sorted(range(len(base)), key=lambda i: base[i], reverse=True)
        diff = -diff
        for i in order:
            while diff > 0 and base[i] > min_frames:
                base[i] -= 1
                diff -= 1
            if diff == 0:
                break

    # If still mismatched (e.g., too few frames due to min_frames), hard fix last bucket.
    final_diff = total_frames - sum(base)
    if base and final_diff != 0:
        base[-1] = max(min_frames, base[-1] + final_diff)

    return base


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


def _chunks_for_srt(words: list[dict], max_words: int = 7, max_chars: int = 38) -> list[dict]:
    """Group word-timed tokens into readable caption lines for SRT."""
    chunks: list[dict] = []
    buf: list[dict] = []

    def flush():
        nonlocal buf
        if not buf:
            return
        text = " ".join(w["word"] for w in buf)
        chunks.append(
            {
                "startFrame": buf[0]["startFrame"],
                "endFrame": buf[-1]["endFrame"],
                "text": text,
            }
        )
        buf = []

    for w in words:
        candidate = buf + [w]
        candidate_text = " ".join(x["word"] for x in candidate)
        should_flush = False

        if len(candidate) > max_words:
            should_flush = True
        elif len(candidate_text) > max_chars and buf:
            should_flush = True

        if should_flush:
            flush()
            buf.append(w)
        else:
            buf.append(w)

        # Prefer line breaks after sentence-ending punctuation
        if w["word"].endswith((".", "!", "?")) and len(buf) >= 3:
            flush()

    flush()
    return chunks


@dataclass
class CaptionSegment:
    id: int
    start_frame: int
    duration_frames: int
    text: str
    subtitle_words: list[dict]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "startFrame": self.start_frame,
            "durationFrames": self.duration_frames,
            "text": self.text,
            "subtitleWords": self.subtitle_words,
        }


def run_captions(
    reel_path: Path,
    fps: int = DEFAULT_FPS,
    overwrite: bool = True,
) -> dict:
    """Generate captions (word timings + SRT) and burn into final.mp4 using Remotion."""
    reel_path = Path(reel_path)
    objective = Objective.from_reel_folder(reel_path)

    final_dir = reel_final_dir(reel_path)
    final_dir.mkdir(parents=True, exist_ok=True)

    base_video_path = final_dir / "final_raw.mp4"
    if not base_video_path.exists():
        raise FileNotFoundError(f"Base video not found: {base_video_path} (run Stage 7 first)")

    # Load script segments for spoken text
    script_path = json_path(reel_path, "02_story_generator.output.json")
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path} (run Stage 2 first)")
    with open(script_path, "r", encoding="utf-8") as f:
        script_data = json.load(f)
    script_segments = script_data.get("segments", script_data)
    if not isinstance(script_segments, list):
        raise ValueError("Unexpected script format: expected a list of segments")
    script_by_id = {int(s.get("id")): s for s in script_segments if isinstance(s, dict) and "id" in s}

    # Determine which clips are included in final_raw
    included_clip_ids: list[int] = []
    stage7_output = json_path(reel_path, "07_final.output.json")
    if stage7_output.exists():
        try:
            with open(stage7_output, "r", encoding="utf-8") as f:
                stage7_data = json.load(f)
            clip_results = stage7_data.get("clip_results", [])
            for r in clip_results:
                if isinstance(r, dict) and r.get("status") == "success":
                    included_clip_ids.append(int(r.get("clip_id")))
        except Exception:
            included_clip_ids = []

    if not included_clip_ids:
        # Fallback: assume clips 1..N where N is count of script segments
        included_clip_ids = sorted(script_by_id.keys())

    # Load durations from Stage 5.5 output (preferred)
    duration_by_seq: dict[int, float] = {}
    audio_json_path = json_path(reel_path, "05.5_audio_generation.output.json")
    if audio_json_path.exists():
        try:
            with open(audio_json_path, "r", encoding="utf-8") as f:
                audio_data = json.load(f)
            clips = audio_data.get("clips", [])
            for c in clips:
                if not isinstance(c, dict):
                    continue
                seq = int(c.get("sequence", c.get("segment_id", 0)) or 0)
                dur = c.get("duration_seconds")
                if seq and isinstance(dur, (int, float)) and dur > 0:
                    duration_by_seq[seq] = float(dur)
        except Exception:
            duration_by_seq = {}

    # Build caption segments in the exact order that final_raw concatenates clips
    caption_segments: list[CaptionSegment] = []
    srt_entries: list[dict] = []
    execution_log: list[str] = []

    for idx, clip_id in enumerate(included_clip_ids):
        seg = script_by_id.get(int(clip_id), {})
        text = (seg.get("text") or "").strip()
        if not text:
            # Don't generate empty subtitles, but keep the segment for consistent rendering
            text = ""

        # Determine voice duration for this clip
        voice_duration = duration_by_seq.get(int(clip_id))
        if not voice_duration:
            voice_path = reel_voice_dir(reel_path) / f"voice_{int(clip_id):02d}.mp3"
            voice_duration = _ffprobe_duration(voice_path)
        if not voice_duration or voice_duration <= 0:
            # Conservative default (centered later)
            voice_duration = 8.0

        padding = max(0.0, (CLIP_SECONDS - float(voice_duration)) / 2.0)
        seg_start_frame = idx * int(CLIP_SECONDS * fps)
        seg_duration_frames = int(CLIP_SECONDS * fps)

        words = _tokenize_words(text) if text else []
        voice_frames = max(1, int(round(float(voice_duration) * fps)))
        start_frame = seg_start_frame + int(round(padding * fps))

        subtitle_words: list[dict] = []
        if words:
            weights = [_word_weight(w) for w in words]
            frames_per_word = _allocate_frames(voice_frames, weights, min_frames=1)

            cursor = start_frame
            for w, fcount in zip(words, frames_per_word):
                end = cursor + max(1, int(fcount))
                subtitle_words.append({"word": w, "startFrame": cursor, "endFrame": end})
                cursor = end

        caption_segments.append(
            CaptionSegment(
                id=int(clip_id),
                start_frame=seg_start_frame,
                duration_frames=seg_duration_frames,
                text=text,
                subtitle_words=subtitle_words,
            )
        )

        # Build SRT chunks (readable lines, not karaoke)
        if subtitle_words:
            chunks = _chunks_for_srt(subtitle_words)
            for ch in chunks:
                srt_entries.append(ch)

        execution_log.append(
            f"- Clip {clip_id:02d}: voice={voice_duration:.2f}s padding={padding:.2f}s words={len(words)}"
        )

    total_frames = len(included_clip_ids) * int(CLIP_SECONDS * fps)

    # Write captions JSON (also serves as render props)
    captions_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "title": objective.title,
        "fps": fps,
        "totalFrames": total_frames,
        "baseVideoPath": str(base_video_path.resolve()),
        "segments": [s.to_dict() for s in caption_segments],
    }
    captions_json_path = json_path(reel_path, "07.5_captions.output.json")
    write_file(captions_json_path, json.dumps(captions_payload, indent=2))

    # Write SRT
    srt_lines: list[str] = []
    for i, entry in enumerate(srt_entries, start=1):
        start_sec = entry["startFrame"] / fps
        end_sec = entry["endFrame"] / fps
        if end_sec <= start_sec:
            end_sec = start_sec + (1 / fps)

        srt_lines.append(str(i))
        srt_lines.append(f"{_format_srt_timestamp(start_sec)} --> {_format_srt_timestamp(end_sec)}")
        srt_lines.append(entry["text"])
        srt_lines.append("")

    srt_path = final_dir / "final.srt"
    write_file(srt_path, "\n".join(srt_lines))

    # Save audit log
    input_md = prompt_path(reel_path, "07.5_captions.input.md")
    write_file(
        input_md,
        "# Captions Stage (7.5) Execution Log\n\n"
        f"Generated: {datetime.now(timezone.utc).isoformat()}\n\n"
        "## Clips\n"
        + "\n".join(execution_log)
        + "\n",
    )

    # Burn captions via Remotion
    output_mp4 = final_dir / "final.mp4"
    if output_mp4.exists() and not overwrite:
        logger.info(f"Captions output exists, skipping: {output_mp4}")
    else:
        remotion = RemotionCLI()
        remotion.render(
            composition_id="CaptionBurn",
            output_path=output_mp4,
            props=captions_payload,
            props_file=final_dir / "remotion_captions_props.json",
        )

    return {
        "status": "success",
        "base_video": str(base_video_path),
        "captioned_video": str(output_mp4),
        "srt": str(srt_path),
        "captions_json": str(captions_json_path),
        "clips": len(included_clip_ids),
    }


