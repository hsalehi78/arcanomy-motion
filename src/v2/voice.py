"""V2 voice generation (Phase 4).

Canonical output:
- `v2/voice/subseg-XX.wav` (mono WAV)
- Exactly 10.0s each (pad/trim)

Provider:
- Uses ElevenLabs if `ELEVENLABS_API_KEY` is present.
- Otherwise generates a deterministic stub tone (for local/dev).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from src.config import get_default_voice_id
from src.services.elevenlabs import ElevenLabsService
from src.utils.paths import ensure_v2_layout, v2_plan_path, v2_voice_dir
from src.v2.visuals import probe_duration_seconds, validate_duration


def _ffmpeg_exists() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _to_wav_10s(
    *,
    in_audio: Path,
    out_wav: Path,
    duration_seconds: float = 10.0,
    sample_rate: int = 48000,
    force: bool = False,
) -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found on PATH (required for audio conversion).")
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    if out_wav.exists() and not force:
        return

    # Pad then trim to exact duration.
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y" if force else "-n",
        "-i",
        str(in_audio),
        "-af",
        f"apad,atrim=duration={duration_seconds}",
        "-ar",
        str(sample_rate),
        "-ac",
        "1",
        str(out_wav),
    ]
    _run(cmd)


def _render_stub_voice(
    *,
    out_wav: Path,
    words: int,
    duration_seconds: float = 10.0,
    sample_rate: int = 48000,
    force: bool = False,
) -> None:
    """Deterministic beep + trailing silence to allow audio-based timing tests."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found on PATH (required for stub audio).")
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    if out_wav.exists() and not force:
        return

    # Beep duration is a deterministic function of word count.
    beep = min(9.0, max(2.0, round(words * 0.35, 2)))
    silence = max(0.0, round(duration_seconds - beep, 2))

    # Two inputs: sine + silence, concat, then enforce exact length.
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y" if force else "-n",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=220:duration={beep}:sample_rate={sample_rate}",
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r={sample_rate}:cl=mono:d={silence}",
        "-filter_complex",
        f"[0:a][1:a]concat=n=2:v=0:a=1,atrim=duration={duration_seconds}",
        str(out_wav),
    ]
    _run(cmd)


def v2_generate_voice(
    reel_path: Path,
    *,
    voice_id: str | None = None,
    force: bool = False,
    fps: int = 30,
) -> list[Path]:
    """Generate per-subsegment 10.0s WAV files."""
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
    out_dir = v2_voice_dir(reel_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    api_key = os.getenv("ELEVENLABS_API_KEY") or ""
    use_elevenlabs = bool(api_key.strip())
    eleven = ElevenLabsService() if use_elevenlabs else None
    if voice_id is None:
        voice_id = get_default_voice_id("elevenlabs")

    outputs: list[Path] = []
    for ss in subsegments:
        sid = ss["subsegment_id"]
        text = (ss.get("voice") or {}).get("text") or ""
        words = len(str(text).split())
        out_wav = out_dir / f"{sid}.wav"

        if out_wav.exists() and not force:
            # Validate duration still, to guarantee invariants.
            dur = probe_duration_seconds(out_wav)
            validate_duration(duration_seconds=dur, target_seconds=10.0, fps=fps, tolerance_frames=1)
            outputs.append(out_wav)
            continue

        if use_elevenlabs and eleven is not None:
            tmp_mp3 = out_dir / f"{sid}.mp3"
            eleven.generate_speech(
                text=str(text),
                voice_id=voice_id,
                output_path=tmp_mp3,
            )
            _to_wav_10s(in_audio=tmp_mp3, out_wav=out_wav, force=True)
            # Keep tmp mp3 for debugging? No: determinism prefers minimal artifacts.
            try:
                tmp_mp3.unlink(missing_ok=True)
            except Exception:
                pass
        else:
            # Deterministic stub for development.
            _render_stub_voice(out_wav=out_wav, words=words, force=True)

        dur = probe_duration_seconds(out_wav)
        validate_duration(duration_seconds=dur, target_seconds=10.0, fps=fps, tolerance_frames=1)
        outputs.append(out_wav)

    return outputs


