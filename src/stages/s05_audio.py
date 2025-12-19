"""Stage 5.5: Audio Generation - Generate narration audio with ElevenLabs.

This is a Dumb Script stage that:
1. Reads optimized narrations from Stage 5
2. Generates audio using ElevenLabs TTS
3. Iteratively adjusts text to hit the 7.5-9 second target duration
"""

import json
import subprocess
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.services import ElevenLabsService
from src.utils.io import write_file
from src.utils.logger import get_logger

logger = get_logger()

# Target duration range
TARGET_MIN_SECONDS = 7.0
TARGET_MAX_SECONDS = 9.0
TARGET_IDEAL_SECONDS = 8.0

# Maximum iterations per clip to avoid infinite loops
MAX_ITERATIONS = 5


def get_audio_duration(audio_path: Path) -> Optional[float]:
    """Get audio duration in seconds using ffprobe.

    Args:
        audio_path: Path to the audio file

    Returns:
        Duration in seconds, or None if ffprobe fails
    """
    if not shutil.which("ffprobe"):
        logger.warning("ffprobe not found - cannot verify audio duration")
        return None

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-i",
                str(audio_path),
                "-show_entries",
                "format=duration",
                "-v",
                "quiet",
                "-of",
                "csv=p=0",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except (subprocess.TimeoutExpired, ValueError) as e:
        logger.warning(f"Failed to get audio duration: {e}")

    return None


def expand_text(text: str, word_count: int) -> str:
    """Expand short text to increase duration.

    Simple rule-based expansion. For more sophisticated expansion,
    this could use an LLM.

    Args:
        text: Original text
        word_count: Current word count

    Returns:
        Expanded text
    """
    # Add filler phrases based on content
    expansions = {
        "is ": "truly is ",
        "was ": "has always been ",
        "the ": "the very ",
        ". ": ". And so ",
        "today ": "on this very day ",
        "now ": "right now ",
        "begins ": "slowly begins ",
        "ends ": "finally ends ",
    }

    expanded = text
    for short, long in expansions.items():
        if short in expanded.lower() and len(expanded.split()) < 12:
            expanded = expanded.replace(short, long, 1)
            break

    return expanded


def trim_text(text: str, word_count: int) -> str:
    """Trim long text to reduce duration.

    Args:
        text: Original text
        word_count: Current word count

    Returns:
        Trimmed text
    """
    # Remove common filler words/phrases
    trims = [
        ("nothing but ", ""),
        ("something far more ", "something "),
        ("truly is ", "is "),
        ("has always been ", "was "),
        ("the very ", "the "),
        ("right now ", "now "),
        ("on this day ", "today "),
        ("In this moment, ", ""),
        ("And so, ", ""),
        ("Perhaps ", ""),
        ("Indeed, ", ""),
    ]

    trimmed = text
    for pattern, replacement in trims:
        if pattern.lower() in trimmed.lower():
            # Case-insensitive replacement
            import re

            trimmed = re.sub(re.escape(pattern), replacement, trimmed, flags=re.IGNORECASE)
            break

    # If no patterns matched and text is still too long, truncate at last sentence
    if trimmed == text and word_count > 12:
        sentences = text.split(". ")
        if len(sentences) > 1:
            trimmed = sentences[0] + "."

    return trimmed


def run_audio_generation(
    reel_path: Path,
    voice_id: Optional[str] = None,
    dry_run: bool = False,
    skip_duration_check: bool = False,
) -> list[dict]:
    """Generate audio for each narration using ElevenLabs.

    This stage:
    1. Reads optimized narrations from Stage 5 (05_voice.output.json)
    2. Falls back to Stage 2 segments if Stage 5 output doesn't exist
    3. Generates audio using ElevenLabs TTS with documentary-style settings
    4. Optionally iterates to hit target duration (7.5-9 seconds)

    Args:
        reel_path: Path to the reel folder
        voice_id: Override voice ID (uses config if not provided)
        dry_run: If True, only save prompts without calling API
        skip_duration_check: If True, don't iterate for duration targeting

    Returns:
        List of audio generation results
    """
    from src.domain import Objective

    # Load reel config for voice ID if not provided
    objective = Objective.from_reel_folder(reel_path)
    if not voice_id:
        voice_id = getattr(objective, "voice_id", None)
        # Handle placeholder values
        if voice_id in (None, "eleven_labs_adam", "your_voice_id"):
            # Use a common ElevenLabs voice as default
            voice_id = "21m00Tcm4TlvDq8ikWAM"  # "Rachel" - a popular ElevenLabs voice
            logger.warning(f"No voice_id configured, using default: {voice_id}")

    # Try to load Stage 5 output first
    voice_output_path = reel_path / "05_voice.output.json"
    segments_path = reel_path / "02_story_generator.output.json"

    narrations = []
    voice_config = {
        "stability": 0.40,
        "similarity_boost": 0.75,
        "style": 0.12,
    }

    if voice_output_path.exists():
        logger.info(f"Loading narrations from Stage 5: {voice_output_path.name}")
        with open(voice_output_path, "r", encoding="utf-8") as f:
            voice_data = json.load(f)
        narrations = voice_data.get("narrations", [])
        voice_config = voice_data.get("voice_config", voice_config)
    elif segments_path.exists():
        logger.info(f"Stage 5 not found, falling back to Stage 2: {segments_path.name}")
        with open(segments_path, "r", encoding="utf-8") as f:
            segments_data = json.load(f)

        # Handle both formats
        segments_list = segments_data.get("segments", segments_data)
        if isinstance(segments_list, list):
            for seg in segments_list:
                narrations.append(
                    {
                        "sequence": seg.get("id", 1),
                        "segment_id": seg.get("id", 1),
                        "original_text": seg.get("text", ""),
                        "optimized_text": seg.get("text", ""),
                    }
                )
    else:
        logger.error("No narration source found. Run Stage 2 (script) or Stage 5 (voice) first.")
        return []

    if not narrations:
        logger.error("No narrations found in source files.")
        return []

    # Prepare output directory
    renders_dir = reel_path / "renders"
    renders_dir.mkdir(exist_ok=True)
    voice_dir = renders_dir / "voice"
    voice_dir.mkdir(exist_ok=True)

    # Initialize ElevenLabs service
    elevenlabs = None
    if not dry_run:
        elevenlabs = ElevenLabsService()

    results = []
    execution_log = []

    for narration in narrations:
        seq = narration.get("sequence", narration.get("segment_id", 1))
        text = narration.get("optimized_text", narration.get("original_text", ""))
        output_path = voice_dir / f"voice_{seq:02d}.mp3"

        execution_log.append(f"\n## Sequence {seq:02d}")
        execution_log.append(f"- Original text: \"{narration.get('original_text', text)}\"")
        execution_log.append(f"- Optimized text: \"{text}\"")

        if dry_run:
            results.append(
                {
                    "sequence": seq,
                    "segment_id": narration.get("segment_id", seq),
                    "text": text,
                    "audio_path": str(output_path),
                    "status": "dry_run",
                    "voice_id": voice_id,
                    "voice_config": voice_config,
                }
            )
            execution_log.append(f"- Status: DRY RUN (would generate to {output_path.name})")
            continue

        # Generate audio with optional duration iteration
        current_text = text
        iteration = 0
        final_duration = None
        status = "pending"

        while iteration < MAX_ITERATIONS:
            iteration += 1
            execution_log.append(f"\n### Iteration {iteration}")
            execution_log.append(f"- Text: \"{current_text}\"")
            execution_log.append(f"- Word count: {len(current_text.split())}")

            try:
                # Generate audio
                elevenlabs.generate_speech(
                    text=current_text,
                    voice_id=voice_id,
                    output_path=output_path,
                    stability=voice_config.get("stability", 0.40),
                    similarity_boost=voice_config.get("similarity_boost", 0.75),
                    style=voice_config.get("style", 0.12),
                )

                # Check duration if enabled
                if not skip_duration_check:
                    duration = get_audio_duration(output_path)
                    if duration is not None:
                        execution_log.append(f"- Duration: {duration:.2f}s")
                        final_duration = duration

                        if TARGET_MIN_SECONDS <= duration <= TARGET_MAX_SECONDS:
                            status = "success"
                            execution_log.append("- Status: [OK] IN TARGET RANGE")
                            break
                        elif duration < TARGET_MIN_SECONDS:
                            # Too short - expand text
                            execution_log.append("- Status: [!!] TOO SHORT, expanding...")
                            current_text = expand_text(current_text, len(current_text.split()))
                        else:
                            # Too long - trim text
                            execution_log.append("- Status: [!!] TOO LONG, trimming...")
                            current_text = trim_text(current_text, len(current_text.split()))
                    else:
                        # Can't check duration, accept the result
                        status = "success_no_duration_check"
                        execution_log.append("- Duration: Unable to verify (ffprobe unavailable)")
                        break
                else:
                    status = "success"
                    execution_log.append("- Duration check: SKIPPED")
                    break

            except Exception as e:
                status = "failed"
                execution_log.append(f"- Error: {e}")
                logger.error(f"Failed to generate audio for sequence {seq}: {e}")
                break

        # If we hit max iterations, use the last result
        if iteration >= MAX_ITERATIONS and status == "pending":
            status = "max_iterations"
            execution_log.append("- Status: [!!] Max iterations reached, using last result")

        results.append(
            {
                "sequence": seq,
                "segment_id": narration.get("segment_id", seq),
                "text": current_text,
                "original_text": text,
                "audio_path": str(output_path) if output_path.exists() else None,
                "duration_seconds": final_duration,
                "iterations": iteration,
                "status": status,
                "voice_id": voice_id,
            }
        )

    # Save execution log
    input_log_path = reel_path / "05.5_audio_generation.input.md"
    log_content = f"""# Audio Generation Execution Log

Generated: {datetime.now(timezone.utc).isoformat()}

## Configuration
- Voice ID: {voice_id}
- Stability: {voice_config.get('stability', 0.40)}
- Similarity Boost: {voice_config.get('similarity_boost', 0.75)}
- Style: {voice_config.get('style', 0.12)}
- Target Duration: {TARGET_MIN_SECONDS}-{TARGET_MAX_SECONDS}s

## Narration Count: {len(narrations)}

{"".join(execution_log)}
"""
    write_file(input_log_path, log_content)

    # Save results JSON
    output_json = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "voice_id": voice_id,
        "voice_config": voice_config,
        "target_duration": {"min": TARGET_MIN_SECONDS, "max": TARGET_MAX_SECONDS},
        "total_clips": len(results),
        "successful": sum(1 for r in results if r.get("status") in ("success", "success_no_duration_check")),
        "clips": results,
    }
    output_path = reel_path / "05.5_audio_generation.output.json"
    write_file(output_path, json.dumps(output_json, indent=2))

    # Print summary
    success_count = output_json["successful"]
    logger.info(f"Audio generation complete: {success_count}/{len(results)} clips successful")

    for r in results:
        # Use ASCII-safe status icons for Windows compatibility
        is_success = r.get("status") in ("success", "success_no_duration_check", "dry_run")
        status_icon = "[OK]" if is_success else "[!!]"
        duration_str = f"{r.get('duration_seconds', 0):.2f}s" if r.get("duration_seconds") else "N/A"
        logger.info(f"  {status_icon} Clip {r['sequence']:02d}: {duration_str} ({r.get('status', 'unknown')})")

    return results

